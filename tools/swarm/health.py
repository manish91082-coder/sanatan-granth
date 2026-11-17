"""स्वार्म की सेहत-बही और मॉडल-चयन (router)।

दो स्रोत, दो भरोसे:
  - policy/model_roster.json (main, केवल PR + मालिक की स्वीकृति): कौन-सा मॉडल किस भूमिका के योग्य है, और दिन का हमारा हिस्सा।
  - <state>/health.json (branch 'swarm-state', मशीन लिखती है): अभी कौन-सा मॉडल चल रहा है, कौन कब तक रुका है, आज कितना ख़र्च हुआ।

नियम:
  - quota ख़त्म, रुकावट, समय-सीमा या बंद key पर मॉडल एक तय समय तक "रुका" माना जाता है और अगला योग्य मॉडल लिया जाता है।
  - अयोग्य मॉडल कभी नहीं लिया जाता। कोई योग्य रचना न बने तो काम रुकता है और अगला समय बताता है (इंतज़ार, गिरावट नहीं)।
  - मशीन किसी मॉडल को केवल हटा सकती है। जोड़ना या योग्य बनाना roster के PR से ही होता है।
  - कभी दूसरी key, दूसरा खाता या quota बढ़ाने की कोई चाल नहीं।
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROSTER_PATH = REPO / "policy" / "model_roster.json"
UTC = dt.timezone.utc
# जिन विफलताओं पर मॉडल कुछ देर के लिए सूची से हटता है
COOLDOWN_KINDS = ("daily_quota", "budget", "overloaded", "timeout", "rate_limited", "auth", "gone", "quality")
# जिनसे पता चलता है कि रुकावट बाहर की है (काम "रुका" गिना जाए, "विफल" नहीं)। run_cap = एक run में OpenRouter के अनुरोधों की
# सीमा: मॉडल ठीक है, बस यह run आगे नहीं जा सकता (बचा काम अगला run उठाता है)।
BLOCKING_KINDS = ("daily_quota", "budget", "overloaded", "timeout", "rate_limited", "auth", "gone", "run_cap")


def state_dir() -> Path | None:
    v = os.environ.get("SWARM_STATE_DIR")
    return Path(v) if v else None


def now_utc() -> dt.datetime:
    return dt.datetime.now(UTC).replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def load_roster(path: Path = ROSTER_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load(sd: Path | None) -> dict:
    h: dict = {"version": 1, "updated_at": None, "models": {}, "providers": {}}
    p = sd / "health.json" if sd else None
    if p and p.exists():
        try:
            got = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(got, dict) and isinstance(got.get("models"), dict):
                got.setdefault("providers", {})
                h = got
        except Exception:  # noqa: BLE001  टूटी बही: ख़ाली से शुरू (बही केवल सुविधा है, स्रोत-सत्य नहीं)
            pass
    # संचालक की अलग फ़ाइल: provider ने ख़ुद जो गिनती बताई (बही का लेखक काम करने वाला job है, इसलिए यह अलग रहती है)
    u = sd / "usage_reported.json" if sd else None
    if u and u.exists():
        try:
            for prov, r in json.loads(u.read_text(encoding="utf-8")).items():
                e = h["providers"].setdefault(prov, {})
                e["reported_used"], e["reported_window"], e["reported_at"] = int(r["used"]), r["window"], r.get("at")
        except Exception:  # noqa: BLE001
            pass
    return h


def save(sd: Path | None, h: dict, now: dt.datetime | None = None) -> None:
    if not sd:
        return
    h["updated_at"] = iso(now or now_utc())
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "health.json").write_text(json.dumps(h, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def provider_of(ref: str) -> str:
    return ref.split(":", 1)[0]


def reset_rule(roster: dict, ref: str) -> str:
    return (roster.get("providers", {}).get(provider_of(ref)) or {}).get("reset", "utc_midnight")


def next_reset(rule: str, now: dt.datetime) -> dt.datetime:
    """अगला क्षण जब दिन का हिस्सा लौटता है (कुछ मिनट की गुंजाइश के साथ)।"""
    if rule == "pacific_midnight":  # Google: आधी रात Pacific ≈ 08:00 UTC (DST में 07:00); देर वाली ओर रखा है
        r = now.replace(hour=8, minute=5, second=0)
        return r if r > now else r + dt.timedelta(days=1)
    if rule == "rolling_24h":  # Groq: चलती खिड़की; पक्का समय 429 के संदेश से आता है, यह केवल ऊपरी सीमा है
        return now + dt.timedelta(hours=24)
    r = now.replace(hour=0, minute=5, second=0) + dt.timedelta(days=1)
    return r


def window_id(rule: str, now: dt.datetime) -> str:
    """ख़र्च की गिनती किस "दिन" में जाती है।"""
    if rule == "pacific_midnight":
        return (now - dt.timedelta(hours=8)).strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


def _roll(entry: dict, rule: str, now: dt.datetime) -> dict:
    w = window_id(rule, now)
    if entry.get("window") != w:
        entry["window"], entry["requests"], entry["output_tokens"] = w, 0, 0
    return entry


def cooldown_until(kind: str, roster: dict, ref: str, fails: int, now: dt.datetime, retry_after_s: float | None) -> dt.datetime | None:
    cd = roster.get("rules", {}).get("cooldown", {})
    rule = reset_rule(roster, ref)
    if kind in ("daily_quota", "budget"):
        if kind == "daily_quota" and retry_after_s and retry_after_s > 0:
            return now + dt.timedelta(seconds=min(retry_after_s + 60, 26 * 3600))
        if rule == "rolling_24h":  # समय नहीं बताया गया: घंटे-भर बाद दोबारा परखें
            return now + dt.timedelta(minutes=cd.get("rolling_probe_min", 60))
        return next_reset(rule, now)
    if kind in ("overloaded", "timeout"):
        base, top = cd.get("overloaded_base_min", 15), cd.get("overloaded_max_min", 360)
        return now + dt.timedelta(minutes=min(base * 2 ** max(0, min(fails, 8) - 1), top))
    if kind == "rate_limited":
        return now + dt.timedelta(minutes=cd.get("rate_limited_min", 10))
    if kind == "auth":
        return now + dt.timedelta(hours=cd.get("auth_hours", 24))
    if kind == "gone":
        return now + dt.timedelta(hours=cd.get("gone_hours", 24))
    if kind == "quality":
        return now + dt.timedelta(hours=roster.get("rules", {}).get("quality_hold_hours", 168))
    return None


def absorb(h: dict, stats: dict, roster: dict, now: dt.datetime | None = None) -> list[dict]:
    """एक run के llm.STATS को बही में जोड़ता है। लौटाता है: इस बार जो मॉडल रुके (रिपोर्ट के लिए)।"""
    now = now or now_utc()
    held: list[dict] = []
    for ref, s in sorted(stats.items()):
        rule = reset_rule(roster, ref)
        m = _roll(h["models"].setdefault(ref, {}), rule, now)
        p = _roll(h["providers"].setdefault(provider_of(ref), {}), rule, now)
        for target in (m, p):
            target["requests"] = target.get("requests", 0) + int(s.get("requests", 0))
            target["output_tokens"] = target.get("output_tokens", 0) + int(s.get("output_tokens", 0))
        f = s.get("fail")
        if f and f.get("kind") == "daily_quota" and (roster.get("providers", {}).get(provider_of(ref)) or {}).get("daily_requests"):
            # साझा हिस्से वाला provider (OpenRouter): दिन की सीमा एक मॉडल की नहीं, पूरे खाते की है
            p["exhausted_until"] = iso(next_reset(rule, now))
        if f and f.get("kind") in COOLDOWN_KINDS:
            m["fails"] = int(m.get("fails", 0)) + 1
            until = cooldown_until(f["kind"], roster, ref, m["fails"], now, f.get("retry_after_s"))
            old = parse_iso(m.get("cooldown_until"))
            keep_quality = m.get("reason") == "quality" and old is not None and old > now  # गुणवत्ता की रोक छोटी नहीं होती
            if until and not keep_quality:
                m["cooldown_until"], m["reason"] = iso(until), f["kind"]
            m["last_error"], m["last_error_at"] = str(f.get("message", ""))[:200], iso(now)
            held.append({"model": ref, "reason": f["kind"], "until": m.get("cooldown_until")})
        elif f and f.get("kind") == "run_cap":
            held.append({"model": ref, "reason": "run_cap", "until": None})
        elif s.get("ok"):
            m["last_ok"] = iso(now)
            if m.get("reason") != "quality":  # गुणवत्ता की रोक केवल जज-परीक्षा पास होने पर हटती है
                m["fails"] = 0
                m.pop("cooldown_until", None)
                m.pop("reason", None)
    return held


def hold_quality(h: dict, roster: dict, ref: str, why: str, now: dt.datetime | None = None) -> None:
    now = now or now_utc()
    m = h["models"].setdefault(ref, {})
    m["cooldown_until"], m["reason"] = iso(cooldown_until("quality", roster, ref, 1, now, None)), "quality"
    m["last_error"], m["last_error_at"] = why[:200], iso(now)


def clear_quality(h: dict, ref: str) -> None:
    m = h["models"].get(ref) or {}
    if m.get("reason") == "quality":
        m.pop("cooldown_until", None)
        m.pop("reason", None)
        m["fails"] = 0


def has_key(ref: str) -> bool:
    need = {"google_ai_studio": "GEMINI_API_KEY", "groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY"}.get(provider_of(ref))
    return bool(need and os.environ.get(need))


BIG = 10 ** 6


def remaining_model(h: dict, roster: dict, ref: str, now: dt.datetime) -> int:
    """इस मॉडल के दिन के हमारे हिस्से में से बचे अनुरोध। सीमा न लिखी हो तो BIG।"""
    rule = reset_rule(roster, ref)
    left = BIG
    cfg = roster.get("models", {}).get(ref, {})
    m = h["models"].get(ref) or {}
    same = m.get("window") == window_id(rule, now)
    if cfg.get("daily_requests"):
        left = min(left, int(cfg["daily_requests"]) - (m.get("requests", 0) if same else 0))
    if cfg.get("daily_tokens") and same and m.get("output_tokens", 0) >= int(cfg["daily_tokens"]):
        left = 0
    return max(0, left)


def remaining_provider(h: dict, roster: dict, provider: str, now: dt.datetime) -> int:
    """provider के साझा दिन के हिस्से में से बचे अनुरोध (जैसे OpenRouter: सारे मुफ़्त मॉडलों का एक ही हिस्सा)।"""
    pc = roster.get("providers", {}).get(provider) or {}
    if not pc.get("daily_requests"):
        return BIG
    w = window_id(pc.get("reset", "utc_midnight"), now)
    p = h["providers"].get(provider) or {}
    ex = parse_iso(p.get("exhausted_until"))
    if ex and ex > now:
        return 0
    used = p.get("requests", 0) if p.get("window") == w else 0
    used = max(used, int(p.get("reported_used", 0)) if p.get("reported_window") == w else 0)
    return max(0, int(pc["daily_requests"]) - used)


def remaining(h: dict, roster: dict, ref: str, now: dt.datetime) -> int:
    return min(remaining_model(h, roster, ref, now), remaining_provider(h, roster, provider_of(ref), now))


def usable(h: dict, roster: dict, ref: str, kind: str, now: dt.datetime, need_requests: int = 1, check_key: bool = True) -> tuple[bool, str, dt.datetime | None]:
    """(चल सकता है?, कारण, कब दोबारा देखें)। kind: 'draft' या 'judge'। कारण 'अयोग्य' हो तो समय None (इंतज़ार से नहीं बदलेगा)।"""
    cfg = roster.get("models", {}).get(ref)
    if not cfg:
        return False, "roster में नहीं", None
    if not (cfg.get(kind) or {}).get("qualified"):
        return False, "इस भूमिका के योग्य नहीं", None
    if kind == "judge":
        j, rules = cfg["judge"], roster.get("rules", {})
        if float(j.get("catch_rate") or 0) < rules.get("judge_min_catch_rate", 0.85) or int(j.get("items") or 0) < rules.get("judge_min_items", 12):
            return False, "जज-परीक्षा की सीमा से नीचे", None
    if check_key and not has_key(ref):
        return False, "key नहीं", None
    m = h["models"].get(ref) or {}
    until = parse_iso(m.get("cooldown_until"))
    if until and until > now:
        return False, f"रुका: {m.get('reason')}", until
    if remaining(h, roster, ref, now) < need_requests:
        return False, "दिन का हिस्सा पूरा", next_reset(reset_rule(roster, ref), now)
    return True, "", None


def _need(roster: dict, ref: str, n: int, per_chunk: int, extra: int) -> int:
    chunk = int(roster.get("models", {}).get(ref, {}).get("chunk") or 9)
    return -(-n // chunk) * per_chunk + extra


def plan(h: dict, roster: dict, now: dt.datetime | None = None, n_segments: int = 18, check_key: bool = True, fixed: dict | None = None) -> dict:
    """अभी की सबसे अच्छी योग्य रचना (ड्राफ़्ट A, ड्राफ़्ट B, जज; और दूसरे दौर के लिए ड्राफ़्ट C + जज)।

    शर्तें: A, B और जज तीन अलग परिवार; कम से कम `min_tier1_drafters` ड्राफ़्टर पहले दर्जे के; दूसरे दौर के लिए ऐसा C जिसका परिवार
    A और B से अलग हो, और हर संभावित विजेता (A या B) के लिए ऐसा योग्य जज जो उस विजेता और C, दोनों के परिवार से बाहर हो।
    क्रम: ड्राफ़्टरों का दर्जा, फिर जज की पकड़-दर, फिर roster का क्रम। यह चयन नियतात्मक है; इसमें कोई LLM नहीं।
    `fixed`: जिन भूमिकाओं का काम पिछले अधूरे run में हो चुका है ({"draft_a": ref, "draft_b": ref, "judge": ref}); उनका मॉडल वही
    रहता है और उसे अभी चलना ज़रूरी नहीं (उससे नया अनुरोध नहीं चाहिए), पर उसे roster में योग्य होना चाहिए।
    """
    now = now or now_utc()
    fixed = fixed or {}
    rules, models, roles = roster.get("rules", {}), roster.get("models", {}), roster.get("roles", {})
    fam = {r: models[r]["family"] for r in models}
    why: dict[str, str] = {}
    waits: list[dt.datetime] = []         # कोई भी रुका मॉडल कब लौटेगा
    better_waits: list[dt.datetime] = []  # जज या पहले दर्जे का ड्राफ़्टर कब लौटेगा (इन्हीं से रचना बेहतर होती है)

    def ok(ref: str, kind: str, need: int) -> bool:
        good, reason, until = usable(h, roster, ref, kind, now, need, check_key)
        if not good:
            why[f"{ref} ({kind})"] = reason + (f" → {iso(until)}" if until else "")
            if until:
                waits.append(until)
                if kind == "judge" or int((models[ref].get("draft") or {}).get("tier", 2)) == 1:
                    better_waits.append(until)
        return good

    drafters = [r for r in roles.get("drafters", []) if ok(r, "draft", _need(roster, r, n_segments, 1, 1))]
    judges = [r for r in roles.get("judges", []) if ok(r, "judge", _need(roster, r, n_segments, 2, 2))]
    order = [r for r in roles.get("drafters", []) if (models.get(r, {}).get("draft") or {}).get("qualified")]
    tier = {r: int(models[r]["draft"].get("tier", 2)) for r in order}
    rank = {r: k for k, r in enumerate(order)}

    def cands(role: str) -> list[str]:
        f = fixed.get(role)
        return ([f] if f in tier else []) if f else drafters

    fj = fixed.get("judge")
    if fj:
        # पहले दौर के फ़ैसले बचे हैं: वही जज माना जाता है, बशर्ते वह roster में अब भी योग्य हो और उस पर गुणवत्ता की रोक न हो
        hm = h["models"].get(fj) or {}
        on_hold = hm.get("reason") == "quality" and (parse_iso(hm.get("cooldown_until")) or now) > now
        judge_cands = [fj] if fj in roles.get("judges", []) and (models.get(fj, {}).get("judge") or {}).get("qualified") and not on_hold else []
    else:
        judge_cands = judges
    best: tuple | None = None
    for a, b in itertools.product(cands("draft_a"), cands("draft_b")):
        if a == b or fam[a] == fam[b] or sum(1 for x in (a, b) if tier[x] == 1) < rules.get("min_tier1_drafters", 1):
            continue
        for j in judge_cands:
            if fam[j] in (fam[a], fam[b]):
                continue
            cs = [c for c in drafters if fam[c] not in (fam[a], fam[b])
                  and all(any(fam[j2] not in (fam[w], fam[c]) for j2 in judges) for w in (a, b))]
            if not cs:
                continue
            # एक ही provider पर दिन का साझा हिस्सा: A, B और जज की कुल ज़रूरत उसमें समानी चाहिए
            need_by_provider: dict[str, int] = {}
            for role, ref, per, extra in (("draft_a", a, 1, 1), ("draft_b", b, 1, 1), ("judge", j, 2, 2)):
                if not fixed.get(role):  # जो काम हो चुका है उसे नया हिस्सा नहीं चाहिए
                    need_by_provider[provider_of(ref)] = need_by_provider.get(provider_of(ref), 0) + _need(roster, ref, n_segments, per, extra)
            if any(remaining_provider(h, roster, p, now) < need for p, need in need_by_provider.items()):
                why["साझा हिस्सा"] = "एक provider पर A, B और जज की कुल ज़रूरत आज के बचे हिस्से से ज़्यादा"
                waits.append(next_reset("utc_midnight", now))
                better_waits.append(next_reset("utc_midnight", now))
                continue
            cs.sort(key=lambda c: (fam[c] == fam[j], tier[c], rank[c]))  # ऐसा C पहले जिससे पहला जज दूसरे दौर में भी चल सके
            score = (tier[a] + tier[b], -float(models[j]["judge"].get("catch_rate") or 0), rank[a] + rank[b], rank[a])
            if best is None or score < best[0]:
                best = (score, a, b, j, cs)
    earliest = min(waits) if waits else None
    if best is None:
        return {"feasible": False, "next_try": iso(earliest) if earliest else None, "why": why,
                "reason": "कोई योग्य रचना अभी नहीं बनती (अलग परिवार + योग्य जज + पहले दर्जे का ड्राफ़्टर)"}
    score, a, b, j, cs = best
    horizon = now + dt.timedelta(hours=rules.get("wait_for_better_hours", 6))
    sooner = min(better_waits) if better_waits else None
    if score[0] > 2 and sooner and sooner <= horizon:
        # अभी की रचना में एक ड्राफ़्टर दूसरे दर्जे का है और पहले दर्जे का कोई मॉडल जल्द लौटेगा: बेहतर रचना का इंतज़ार
        return {"feasible": False, "next_try": iso(sooner), "why": why, "would_be": {"draft_a": a, "draft_b": b, "judge": j},
                "reason": f"बेहतर रचना {rules.get('wait_for_better_hours', 6)} घंटे के भीतर संभव: इंतज़ार"}
    return {
        "feasible": True, "chosen": {"draft_a": a, "draft_b": b, "judge": j, "draft_c": cs[0]}, "tier_sum": score[0],
        "families": {"draft_a": fam[a], "draft_b": fam[b], "judge": fam[j], "draft_c": fam[cs[0]]},
        # ड्राफ़्ट A और B: केवल चुना हुआ मॉडल। वह run के बीच रुक जाए तो run रुकता है और अगली रचना फिर यही function चुनता है
        # (ताकि दर्जे और "बेहतर का इंतज़ार" वाले नियम run के भीतर के बदलाव से न टूटें)। C और जज: सारे योग्य, चलते विकल्प।
        "lists": {"draft_a": [a], "draft_b": [b], "draft_c": cs, "judges": [j] + [x for x in judges if x != j]},
        "why_not": why,
    }


def run_budgets(h: dict, roster: dict, now: dt.datetime | None = None) -> dict[str, int]:
    """llm.BUDGET के लिए: इस run में हर मॉडल ("provider:model") और हर साझा provider ("provider:<नाम>") कितने अनुरोध कर सकता है।"""
    now = now or now_utc()
    out = {r: remaining_model(h, roster, r, now) for r in roster.get("models", {})}
    out.update({f"provider:{p}": remaining_provider(h, roster, p, now) for p in roster.get("providers", {})})
    return {k: v for k, v in out.items() if v < BIG}


def blocked_refs(h: dict, now: dt.datetime | None = None) -> dict[str, str]:
    now = now or now_utc()
    out = {}
    for ref, m in h["models"].items():
        until = parse_iso(m.get("cooldown_until"))
        if until and until > now:
            out[ref] = f"{m.get('reason')} → {m['cooldown_until']}"
    return out


def note_openrouter_usage(h: dict, roster: dict, used: int, now: dt.datetime | None = None) -> None:
    """OpenRouter ख़ुद बताता है कि खाते ने आज कितने मुफ़्त अनुरोध किए (मालिक की दूसरी keys समेत)। बही उसी को मानती है।"""
    now = now or now_utc()
    p = h["providers"].setdefault("openrouter", {})
    p["reported_used"], p["reported_window"], p["reported_at"] = int(used), window_id("utc_midnight", now), iso(now)


def scrub_reason(s: str) -> str:
    return re.sub(r"\s+", " ", s)[:200]
