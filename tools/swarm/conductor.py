"""स्वार्म का संचालक: कतार (swarm/BACKLOG.json) से अगला काम चुनकर Foreman को देता है। इसमें कोई LLM नहीं; सब नियम code में हैं।

    python -m tools.swarm.conductor tick [--dry-run]      # हालत पढ़ो, अगला काम कतार में डालो, STATUS.md लिखो
    python -m tools.swarm.conductor report --batch B --step S --text T --rc N [--ref R] [--report-dir DIR]   # काम का नतीजा दर्ज करो
    python -m tools.swarm.conductor kick                  # काम ख़त्म होते ही संचालक को तुरंत जगाओ

हालत कहाँ रहती है (branch 'swarm-state', env SWARM_STATE_DIR):
  tasks.json     हर काम की स्थिति (केवल संचालक लिखता है)
  runs/<batch>.json   हर चक्कर का नतीजा (काम करने वाला job लिखता है)
  health.json    मॉडलों की सेहत-बही (काम करने वाला job लिखता है)
  work/<task>.json    अधूरे run का बचा काम
  STATUS.md      इंसान के पढ़ने के लिए हालत

नियम:
  - संचालक वही काम चलाता है जो main की कतार में लिखा है; नया काम कभी नहीं गढ़ता। कतार संरक्षित फ़ाइल है।
  - मॉडल-काम एक समय में एक (quota साझा है)। जो काम अभी नहीं चल सकता वह "रुका" रहता है और उसका अगला समय लिखा जाता है।
  - लगातार विफलताओं पर काम रोककर मालिक के लिए issue खुलता है। swarm/STOP हो तो कुछ नहीं चलता।
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.swarm import health  # noqa: E402

BACKLOG = REPO / "swarm" / "BACKLOG.json"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
EXIT_BLOCKED = 75
ALERT_TITLE = "स्वार्म: ध्यान चाहिए"


# ------------------------------------------------------------------ फ़ाइलें
def read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def task_of(batch_id: str) -> str:
    return batch_id.split(".")[0]


# ------------------------------------------------------------------ Foreman
def foreman(path: str, body: dict) -> tuple[int, dict]:
    """Foreman का admin-अनुरोध (HMAC)। URL या secret न हो तो (0, {})।"""
    url, secret = os.environ.get("FOREMAN_URL", ""), os.environ.get("FOREMAN_SHARED_SECRET", "")
    if not re.fullmatch(r"https://[a-z0-9.-]+\.workers\.dev", url) or not secret:
        return 0, {"error": "FOREMAN_URL या secret नहीं"}
    raw = json.dumps(body, separators=(",", ":")).encode()
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    req = urllib.request.Request(url + path, data=raw, method="POST",
                                 headers={"content-type": "application/json", "x-foreman-signature": sig, "user-agent": "sanatan-granth-conductor"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": type(e).__name__}


def openrouter_used() -> int | None:
    """OpenRouter से पूछना कि खाते ने आज कितने मुफ़्त अनुरोध किए (यह अनुरोध गिनती में नहीं आता)। उत्तर समझ न आए तो None।"""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"authorization": "Bearer " + key, "user-agent": "sanatan-granth-conductor"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = (json.loads(r.read() or b"{}").get("data") or {})
    except Exception:  # noqa: BLE001
        return None
    v = d.get("free_model_daily_requests")
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, dict):
        for k in ("used", "count", "requests", "usage"):
            if isinstance(v.get(k), (int, float)):
                return int(v[k])
    return None


# ------------------------------------------------------------------ काम कब चलना है
def due(task: dict, st: dict, now: dt.datetime) -> bool:
    last = health.parse_iso(st.get("last_done"))
    rep = task.get("repeat", "once")
    if rep == "once":
        return last is None
    if rep == "daily":
        return last is None or last.strftime("%Y-%m-%d") != now.strftime("%Y-%m-%d")
    if rep == "weekly":
        return last is None or now - last >= dt.timedelta(days=7)
    return False


def feasibility(task: dict, H: dict, roster: dict, sd: Path | None, now: dt.datetime) -> dict:
    """काम अभी चल सकता है? नहीं तो कब दोबारा देखें।"""
    check_key = any(os.environ.get(k) for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"))
    if task["step"] == "pilot_e2e":
        fixed: dict = {}
        ck = read_json(sd / "work" / f"{task['id']}.json", {}) if sd else {}
        stages = ck.get("stages") or {}
        for st, role in (("draft_a", "draft_a"), ("draft_b", "draft_b"), ("judge1", "judge")):
            if isinstance(stages.get(st), dict) and stages[st].get("model"):
                fixed[role] = stages[st]["model"]
        pl = health.plan(H, roster, now, n_segments=int(task.get("segments", 18)), check_key=check_key, fixed=fixed)
        if not pl["feasible"] and fixed:
            nt = health.parse_iso(pl.get("next_try"))
            if nt is None or nt > now + dt.timedelta(hours=24):
                pl = health.plan(H, roster, now, n_segments=int(task.get("segments", 18)), check_key=check_key)
        return {"ok": pl["feasible"], "next_try": pl.get("next_try"), "reason": pl.get("reason", ""), "plan": pl.get("chosen"), "why": pl.get("why") or pl.get("why_not")}
    if task["step"] == "judge_test":
        waits, ready = [], []
        for ref in roster.get("roles", {}).get("judge_candidates", []):
            m = H["models"].get(ref) or {}
            until = health.parse_iso(m.get("cooldown_until"))
            if check_key and not health.has_key(ref):
                continue
            if until and until > now and m.get("reason") != "quality":
                waits.append(until)
            elif health.remaining(H, roster, ref, now) < 6:
                waits.append(health.next_reset(health.reset_rule(roster, ref), now))
            else:
                ready.append(ref)
        if len(ready) >= 2:  # एक ही जज नापना बेकार है: तुलना के लिए कम से कम दो
            return {"ok": True, "judges": ready}
        return {"ok": False, "next_try": health.iso(min(waits)) if waits else None, "reason": "जज-परीक्षा के लिए दो जज अभी उपलब्ध नहीं"}
    return {"ok": False, "next_try": None, "reason": f"step '{task['step']}' संचालक को नहीं आता"}


# ------------------------------------------------------------------ report (काम करने वाला job)
def cmd_report(a) -> int:
    sd = health.state_dir()
    if not sd:
        print("SWARM_STATE_DIR नहीं: नतीजा दर्ज नहीं हुआ")
        return 0
    now = health.now_utc()
    rc = int(a.rc)
    rdir = Path(a.report_dir) if a.report_dir else None
    rec = {"batch_id": a.batch, "task": task_of(a.batch), "step": a.step, "text_id": a.text, "rc": rc, "ref": a.ref or "",
           "status": "done" if rc == 0 else ("blocked" if rc == EXIT_BLOCKED else "failed"), "at": health.iso(now), "run": os.environ.get("GITHUB_RUN_ID")}
    if rdir:
        if rc == EXIT_BLOCKED:
            b = read_json(rdir / "blocked.json", {})
            rec["blocked_until"], rec["reason"] = b.get("blocked_until"), str(b.get("reason", ""))[:200]
        m = read_json(rdir / "pilot_metrics.json", {})
        if m and a.step == "pilot_e2e":
            c = m.get("cascade") or {}
            rec["summary"] = {"pipeline_version": m.get("pipeline_version"), "segments": m.get("segments"), "first_pass": c.get("first_pass_agreed"),
                              "agreement_rate": c.get("agreement_rate"), "badges": m.get("badges"), "seconds": m.get("seconds_total"),
                              "models": {k: (m.get("models") or {}).get(k) for k in ("draft_a", "draft_b", "draft_c", "judge1")},
                              "api_calls": (m.get("api") or {}).get("calls"), "resumed": (m.get("swarm") or {}).get("resumed_stages")}
        if a.step == "judge_test" and rc == 0:
            # जज-परीक्षा का नतीजा बही में: सीमा से नीचे गया जज रुकता है; पास हुआ जज (अगर गुणवत्ता की रोक पर था) लौटता है।
            # यह किसी जज को योग्य नहीं बनाता: योग्यता roster के PR से ही आती है।
            jt = read_json(rdir / f"judge_test_{a.text}.json", {})
            roster, H = health.load_roster(), health.load(sd)
            rules, rows = roster.get("rules", {}), []
            for r in jt.get("results", []):
                ref, judged, rate = r.get("judge"), int(r.get("judged") or 0), r.get("catch_rate")
                if not ref or judged < int(rules.get("judge_min_items", 12)) or rate is None:
                    rows.append({"judge": ref, "judged": judged, "verdict": "फ़ैसला नहीं (कम उत्तर)"})
                    continue
                if float(rate) < float(rules.get("judge_min_catch_rate", 0.85)):
                    health.hold_quality(H, roster, ref, f"जज-परीक्षा: {r.get('caught')}/{judged}", now)
                    rows.append({"judge": ref, "judged": judged, "catch_rate": rate, "verdict": "सीमा से नीचे: रोका गया"})
                else:
                    health.clear_quality(H, ref)
                    rows.append({"judge": ref, "judged": judged, "catch_rate": rate, "verdict": "सीमा के ऊपर"})
            health.save(sd, H, now)
            rec["summary"] = {"items": jt.get("items"), "judges": rows}
    write_json(sd / "runs" / f"{a.batch}.json", rec)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


# ------------------------------------------------------------------ tick (संचालक)
def apply_record(st: dict, rec: dict, rules: dict, now: dt.datetime) -> None:
    st["last"] = {k: rec.get(k) for k in ("batch_id", "status", "rc", "ref", "at", "reason", "run", "summary")}
    if rec["status"] == "done":
        st.update(status="done", last_done=rec["at"], fails=0, replans=0)
        st.pop("blocked_until", None)
        st.pop("reason", None)
    elif rec["status"] == "blocked":
        until = health.parse_iso(rec.get("blocked_until")) or now + dt.timedelta(hours=1)
        # "अभी दोबारा रचना चुनो" वाले रुकाव गिने जाते हैं: लगातार चार बार बिना पूरा हुए → यह चक्कर है, विफलता मानी जाए
        st["replans"] = int(st.get("replans", 0)) + 1 if until <= now + dt.timedelta(minutes=2) else 0
        if st["replans"] >= 4:
            st["replans"] = 0
            apply_record(st, {**rec, "status": "failed", "reason": "चार बार रचना बदली, काम पूरा नहीं हुआ"}, rules, now)
            return
        st.update(status="blocked", blocked_until=health.iso(until), reason=rec.get("reason") or "मॉडल रुके")
    else:
        st["fails"] = int(st.get("fails", 0)) + 1
        if st["fails"] >= int(rules.get("max_consecutive_task_failures", 3)):
            st.update(status="needs_owner", reason=f"लगातार {st['fails']} विफलताएँ")
        else:
            st.update(status="failed", blocked_until=health.iso(now + dt.timedelta(minutes=30 * st["fails"])), reason="विफल; थोड़ी देर बाद दोबारा")


def cmd_tick(a) -> int:
    sd = health.state_dir()
    now = health.now_utc()
    roster = health.load_roster()
    rules = roster.get("rules", {})
    backlog = read_json(BACKLOG, {"tasks": []})
    H = health.load(sd)
    tasks: dict = read_json(sd / "tasks.json", {}) if sd else {}
    meta = tasks.setdefault("_meta", {})
    notes: list[str] = []
    alerts: list[str] = []

    used = None if a.dry_run else openrouter_used()
    if used is not None and sd:
        prev = read_json(sd / "usage_reported.json", {}).get("openrouter") or {}
        win = health.window_id("utc_midnight", now)
        if prev.get("used") != used or prev.get("window") != win:
            write_json(sd / "usage_reported.json", {"openrouter": {"used": used, "window": win, "at": health.iso(now)}})
        health.note_openrouter_usage(H, roster, used, now)

    stopped = (REPO / "swarm" / "STOP").exists()
    jobs_cache: list | None = None

    def foreman_job(batch_id: str) -> dict | None:
        nonlocal jobs_cache
        if jobs_cache is None:
            st_code, rows = foreman("/admin/export-jobs", {})
            jobs_cache = rows if st_code == 200 and isinstance(rows, list) else []
        return next((r for r in jobs_cache if r.get("batch_id") == batch_id), None)

    busy = False
    plan_now: dict | None = None
    for task in backlog.get("tasks", []):
        tid = task["id"]
        st = tasks.setdefault(tid, {"status": "pending", "seq": 0, "fails": 0})
        st["step"], st["enabled"] = task["step"], bool(task.get("enabled", True))
        # 1. जो चक्कर कतार में था, उसका नतीजा आया?
        if st.get("status") == "queued" and sd:
            rec = read_json(sd / "runs" / f"{st.get('batch_id')}.json", None)
            if rec:
                apply_record(st, rec, rules, now)
            else:
                age = now - (health.parse_iso(st.get("queued_at")) or now)
                if age > dt.timedelta(minutes=int(rules.get("queued_stale_minutes", 100))):
                    row = None if a.dry_run else foreman_job(st.get("batch_id", ""))
                    if row and row.get("status") in ("queued", "running", "waiting_reset") and age < dt.timedelta(hours=8):
                        notes.append(f"{tid}: Foreman में अब भी {row.get('status')} ({int(age.total_seconds() // 60)} मिनट)")
                    else:
                        apply_record(st, {"batch_id": st.get("batch_id"), "status": "failed", "rc": -1, "at": health.iso(now),
                                          "reason": "नतीजा नहीं लौटा (job खो गया या समय-सीमा पार)"}, rules, now)
        if not st["enabled"]:
            continue
        if st.get("status") == "needs_owner":
            alerts.append(f"काम `{tid}` रुका है: {st.get('reason')}. अंतिम चक्कर: {(st.get('last') or {}).get('ref') or (st.get('last') or {}).get('run') or '—'}")
            continue
        if st.get("status") == "queued":
            busy = True
            continue
        if not due(task, st, now):
            if st.get("status") != "done":
                st["status"] = "done"
            continue
        if st.get("status") == "done":
            st["status"] = "pending"  # दोहराने वाला काम: नया दिन या नया सप्ताह
        until = health.parse_iso(st.get("blocked_until"))
        if st.get("status") in ("blocked", "failed") and until and until > now:
            continue
        if busy or stopped:
            continue
        f = feasibility(task, H, roster, sd, now)
        if task["step"] == "pilot_e2e" and plan_now is None:
            plan_now = f
        if not f["ok"]:
            nt = health.parse_iso(f.get("next_try")) or now + dt.timedelta(hours=6)
            st.update(status="blocked", blocked_until=health.iso(nt), reason=f.get("reason", ""))
            if f.get("next_try") is None:
                alerts.append(f"काम `{tid}` के लिए कोई योग्य रचना नहीं बनती और कोई रुका मॉडल लौटने वाला नहीं: {f.get('reason')}")
            continue
        seq = int(st.get("seq", 0)) + 1
        batch = f"{tid}.{now.strftime('%Y%m%d')}.{seq}"
        if a.dry_run:
            notes.append(f"{tid}: कतार में जाता (dry-run) → {batch}")
            busy = True
            continue
        code, out = foreman("/admin/enqueue", {"text_id": task["text_id"], "batch_id": batch, "step": task["step"]})
        if code == 200 and out.get("job_key"):
            st.update(status="queued", batch_id=batch, queued_at=health.iso(now), seq=seq, job_key=out["job_key"])
            st.pop("blocked_until", None)
            st.pop("reason", None)
            busy = True
            notes.append(f"{tid}: कतार में → {batch}")
        elif code == 400:
            st.update(status="blocked", blocked_until=health.iso(now + dt.timedelta(hours=1)), reason="Foreman इस step को अभी नहीं जानता (नया deploy बाक़ी)")
        else:
            notes.append(f"{tid}: Foreman तक बात नहीं पहुँची (HTTP {code})")
            meta["foreman_unreachable"] = int(meta.get("foreman_unreachable", 0)) + 1
            break
    else:
        meta["foreman_unreachable"] = 0
    if busy and not a.dry_run:
        foreman("/admin/tick", {})
    if int(meta.get("foreman_unreachable", 0)) >= 3:
        alerts.append("Foreman (Cloudflare Worker) लगातार तीन बार उत्तर नहीं दे रहा")
    for ref, m in sorted(H["models"].items()):
        until = health.parse_iso(m.get("cooldown_until"))
        if until and until > now and m.get("reason") in ("auth", "gone"):
            alerts.append(f"मॉडल `{ref}` पर `{m['reason']}`: key या मॉडल की उपलब्धता देखनी होगी")
    if stopped:
        notes.append("swarm/STOP मौजूद: कोई नया काम नहीं")
    if sd and not a.dry_run and (sd / "work").is_dir():
        known = {t["id"] for t in backlog.get("tasks", [])}
        for f in (sd / "work").glob("*.json"):
            if f.stem not in known:  # कतार में ऐसा कोई काम नहीं: बचा हुआ अधूरा काम किसी के काम का नहीं
                f.unlink()

    status_md = render_status(now, backlog, tasks, H, roster, notes, alerts, plan_now, stopped)
    if sd and not a.dry_run:
        # हालत तभी लिखी जाती है जब कुछ बदला हो (या 6 घंटे हो गए हों): हर चक्कर का commit नहीं
        core = json.dumps({k: v for k, v in tasks.items() if k != "_meta"}, ensure_ascii=False, sort_keys=True) + "\n".join(status_md.splitlines()[3:])
        digest = hashlib.sha256(core.encode("utf-8")).hexdigest()[:16]
        last = health.parse_iso(meta.get("updated_at"))
        if digest != meta.get("digest") or last is None or now - last > dt.timedelta(hours=6):
            meta["updated_at"], meta["digest"] = health.iso(now), digest
            write_json(sd / "tasks.json", tasks)
            (sd / "STATUS.md").write_text(status_md, encoding="utf-8", newline="\n")
        raise_alert(alerts, meta, sd, tasks)
    print(status_md)
    return 0


def raise_alert(alerts: list[str], meta: dict, sd: Path, tasks: dict) -> None:
    """मालिक के लिए एक ही खुला issue; वही बात दोबारा नहीं लिखी जाती।"""
    if not alerts or not os.environ.get("GH_TOKEN"):
        return
    body = "स्वार्म के संचालक की मशीन-सूचना (इंसान की समीक्षा नहीं):\n\n" + "\n".join(f"- {x}" for x in alerts) + \
           "\n\nहालत: branch `swarm-state` की `STATUS.md`। रोकने के लिए: `swarm/STOP` फ़ाइल (PR से) या Foreman का `/admin/stop`।"
    sha = hashlib.sha256(body.encode()).hexdigest()[:16]
    if meta.get("alert_sha") == sha:
        return

    def gh(*args: str) -> tuple[int, str]:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
        return r.returncode, (r.stdout or "").strip()

    for name, color in (("swarm-alert", "B60205"), ("needs-human", "D93F0B")):
        gh("label", "create", name, "--color", color, "--force")
    rc, out = gh("issue", "list", "--label", "swarm-alert", "--state", "open", "--json", "number", "--jq", ".[0].number // empty")
    if rc == 0 and out:
        rc, _ = gh("issue", "comment", out, "--body", body)
    else:
        rc, _ = gh("issue", "create", "--title", ALERT_TITLE, "--label", "swarm-alert,needs-human", "--body", body)
    if rc == 0:
        meta["alert_sha"] = sha
        write_json(sd / "tasks.json", tasks)


def render_status(now, backlog, tasks, H, roster, notes, alerts, plan_now, stopped) -> str:
    def ist(s: str | None) -> str:
        t = health.parse_iso(s)
        return t.astimezone(IST).strftime("%d %b %H:%M IST") if t else "—"

    word = {"pending": "बारी का इंतज़ार", "queued": "चल रहा / कतार में", "blocked": "रुका (मॉडल या quota)", "failed": "विफल, दोबारा होगा",
            "done": "पूरा", "needs_owner": "मालिक की ज़रूरत"}
    L = ["# स्वार्म की हालत", "",
         f"अपडेट: {now.astimezone(IST).strftime('%d %b %Y %H:%M IST')} ({health.iso(now)}). यह मशीन की प्रक्रिया-स्थिति है; कोई त्रुटि-दर या सत्यापन का दावा नहीं।",
         "", f"**लक्ष्य:** {backlog.get('goal', '')}", ""]
    if stopped:
        L += ["**रुका हुआ: `swarm/STOP` फ़ाइल मौजूद है।**", ""]
    L += ["## काम", "", "| काम | step | स्थिति | अगला समय | पिछली बार पूरा | कारण / टिप्पणी |", "|---|---|---|---|---|---|"]
    for t in backlog.get("tasks", []):
        st = tasks.get(t["id"], {})
        state = "बंद (कतार में enabled नहीं)" if not t.get("enabled", True) else word.get(st.get("status", "pending"), st.get("status", ""))
        L.append(f"| `{t['id']}` | {t['step']} · {t.get('repeat', 'once')} | {state} | {ist(st.get('blocked_until')) if st.get('status') in ('blocked', 'failed') else '—'} | "
                 f"{ist(st.get('last_done'))} | {str(st.get('reason') or '')[:120]} |")
    L += ["", "## मॉडल", "", "| मॉडल | परिवार | भूमिका (roster) | अभी | आज के अनुरोध / हमारा हिस्सा |", "|---|---|---|---|---|"]
    for ref, cfg in roster.get("models", {}).items():
        m = H["models"].get(ref) or {}
        until = health.parse_iso(m.get("cooldown_until"))
        if until and until > now:
            state = f"रुका: {m.get('reason')} → {ist(m.get('cooldown_until'))}"
        elif health.remaining(H, roster, ref, now) <= 0:  # मॉडल ठीक है, पर दिन का हिस्सा (अपना या provider का साझा) पूरा
            state = f"दिन का हिस्सा पूरा → {ist(health.iso(health.next_reset(health.reset_rule(roster, ref), now)))}"
        else:
            state = "चल सकता है"
        role = " + ".join(x for x, k in (("ड्राफ़्ट", "draft"), ("जज", "judge")) if (cfg.get(k) or {}).get("qualified")) or "कोई नहीं"
        rule = health.reset_rule(roster, ref)
        used = m.get("requests", 0) if m.get("window") == health.window_id(rule, now) else 0
        cap = cfg.get("daily_requests") or (roster.get("providers", {}).get(health.provider_of(ref)) or {}).get("daily_requests") or "—"
        L.append(f"| `{ref.split(':', 1)[1]}` | {cfg['family']} | {role} | {state} | {used} / {cap} |")
    orr = H["providers"].get("openrouter") or {}
    if orr.get("reported_window") == health.window_id("utc_midnight", now):
        L += ["", f"OpenRouter ने बताया: खाते के आज के मुफ़्त अनुरोध {orr.get('reported_used')} (मालिक की दूसरी keys समेत)।"]
    if plan_now:
        L += ["", "## अभी की रचना", ""]
        if plan_now.get("ok"):
            L.append("चुनी गई: " + ", ".join(f"{k} = `{str(v).split(':', 1)[1]}`" for k, v in (plan_now.get("plan") or {}).items()))
        else:
            L.append(f"कोई रचना नहीं: {plan_now.get('reason')}. अगली जाँच: {ist(plan_now.get('next_try'))}")
    if notes:
        L += ["", "## इस चक्कर में", ""] + [f"- {x}" for x in notes]
    if alerts:
        L += ["", "## ध्यान चाहिए", ""] + [f"- {x}" for x in alerts]
    return "\n".join(L) + "\n"


def cmd_kick(_a) -> int:
    """काम ख़त्म होते ही संचालक को जगाना, ताकि अगला काम 20 मिनट की घड़ी का इंतज़ार न करे।"""
    run = os.environ.get("GITHUB_RUN_ID", "local")
    code, out = foreman("/admin/enqueue", {"text_id": "swarm", "batch_id": f"after-{run}", "step": "conduct"})
    if code == 200 and out.get("job_key"):
        foreman("/admin/tick", {})
        print("संचालक Foreman की कतार में")
        return 0
    if os.environ.get("GH_TOKEN"):  # पुराना Foreman 'conduct' नहीं जानता: सीधे workflow
        r = subprocess.run(["gh", "workflow", "run", "swarm-conduct.yml", "--ref", "main"], capture_output=True, text=True, encoding="utf-8")
        print("संचालक workflow से जगाया" if r.returncode == 0 else f"संचालक नहीं जगा: {(r.stderr or '')[:200]}")
        return 0
    print(f"संचालक नहीं जगा (Foreman HTTP {code})")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("tick")
    t.add_argument("--dry-run", action="store_true")
    r = sp.add_parser("report")
    for name in ("--batch", "--step", "--text", "--rc"):
        r.add_argument(name, required=True)
    r.add_argument("--ref", default="")
    r.add_argument("--report-dir", default="")
    sp.add_parser("kick")
    a = ap.parse_args()
    return {"tick": cmd_tick, "report": cmd_report, "kick": cmd_kick}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
