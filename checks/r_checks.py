"""R1–R14: रोज़ पूरे repo पर चलने वाली script-जाँचें (मास्टर योजना §3.2)।

हर जाँच ctx.findings में FAIL/WARN जोड़ती है। कोई जाँच फ़ाइलें नहीं बदलती।
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from pathlib import Path

from .common import (Ctx, SEGMENT_ID_RE, canonical_segments_hash, iter_strings, load_json, load_jsonl,
                     segment_sort_key, validator)
from .lexicon import EMAIL_OK, EMAIL_RE, RE_CLAIMS, RE_DEITY, RE_VERIFIED

AI_PROSE_LAYERS = {"summary", "note", "commentary"}
CODE_DIRS = (".github", "foreman", "tools", "checks", "drive", "kaggle")
ALLOWED_TOP = {
    ".git", ".github", ".gitattributes", ".gitignore", "CLAUDE.md", "README.md", "LICENSE", "LICENSES.md",
    "swarm", "policy", "schema", "context", "entities", "catalog", "texts", "witnesses", "sources", "state",
    "audit", "checks", "canaries", "tools", "foreman", "drive", "kaggle", "docs", "badges.json",
    "requirements.txt", "pyproject.toml", ".cache", "_cache", "_raw", "exports", "node_modules",
}


# ---------------------------------------------------------------- R1
def _unicode_lint(ctx: Ctx, check: str, p: Path, where: str, s: str, sa_deva: bool = False) -> None:
    if s != unicodedata.normalize("NFC", s):
        ctx.add(check, "FAIL", p, f"NFC नहीं: {where}")
    if "﻿" in s:
        ctx.add(check, "FAIL", p, f"BOM मिला: {where}")
    if "�" in s:
        ctx.add(check, "FAIL", p, f"U+FFFD (टूटा अक्षर): {where}")
    if any(unicodedata.category(c) == "Cc" and c not in "\n\t" for c in s):
        ctx.add(check, "FAIL", p, f"control अक्षर: {where}")
    if sa_deva:
        if "।।" in s:
            ctx.add(check, "FAIL", p, f"'।।' की जगह '॥' चाहिए: {where}")
        if re.search(r"[A-Za-z]", s):
            ctx.add(check, "FAIL", p, f"sa-Deva पाठ में Latin अक्षर: {where}")
        if "‌" in s or "‍" in s:
            ctx.add(check, "WARN", p, f"ZWJ/ZWNJ (तुलना-कुंजी में हटेगा): {where}")


def r1_schema_unicode(ctx: Ctx) -> None:
    """R1: हर JSON/JSONL parse हो, schema माने, Unicode साफ़ हो।"""
    C = "R1"
    for p in ctx.walk(".json", ".jsonl", ".jsonld"):
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            ctx.add(C, "FAIL", p, "फ़ाइल BOM से शुरू")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as e:
            ctx.add(C, "FAIL", p, f"UTF-8 नहीं: {e}")
            continue
        try:
            if p.suffix == ".jsonl":
                load_jsonl(p)
            else:
                load_json(p)
        except Exception as e:  # noqa: BLE001
            ctx.add(C, "FAIL", p, f"JSON parse विफल: {e}")

    v_layer = validator(ctx.policy_root, "layer.schema.json")
    for p, obj in ctx.layer_files():
        for err in v_layer.iter_errors(obj):
            ctx.add(C, "FAIL", p, f"layer schema: {'/'.join(map(str, err.absolute_path))}: {err.message[:200]}")
        meta = obj.get("_meta", {})
        sa = meta.get("layer") == "root" and meta.get("lang") == "sa-Deva"
        for sid, txt in obj.get("segments", {}).items():
            if isinstance(txt, str):
                _unicode_lint(ctx, C, p, sid, txt, sa_deva=sa)
            tid = meta.get("text_id")
            if tid and not sid.startswith(tid + ":"):
                ctx.add(C, "FAIL", p, f"segment-ID '{sid}' text_id '{tid}' का नहीं", sid)

    v_text = validator(ctx.policy_root, "text.schema.json")
    v_lock = validator(ctx.policy_root, "records.schema.json", "/$defs/text_lock")
    for d in ctx.text_dirs():
        t = d / "_text.json"
        if not t.exists():
            ctx.add(C, "FAIL", d, "_text.json नहीं है")
            continue
        try:
            for err in v_text.iter_errors(load_json(t)):
                ctx.add(C, "FAIL", t, f"text schema: {err.message[:200]}")
        except Exception:  # parse-विफलता ऊपर दर्ज
            pass
        lk = d / "text_lock.json"
        if lk.exists():
            try:
                for err in v_lock.iter_errors(load_json(lk)):
                    ctx.add(C, "FAIL", lk, f"text_lock schema: {err.message[:200]}")
            except Exception:
                pass

    v_card = validator(ctx.policy_root, "catalog_card.schema.json")
    cat = ctx.data_root / "catalog"
    if cat.exists():
        for p in sorted(cat.rglob("*.json")):
            if p.name.startswith("_") or "seed" in p.parts:
                continue
            try:
                card = load_json(p)
            except Exception:
                continue
            for err in v_card.iter_errors(card):
                ctx.add(C, "FAIL", p, f"card schema: {'/'.join(map(str, err.absolute_path))}: {err.message[:200]}")
            if isinstance(card, dict) and card.get("attestation_count") != len(card.get("attested_by", [])):
                ctx.add(C, "FAIL", p, "attestation_count ≠ attested_by की गिनती")

    v_wit = validator(ctx.policy_root, "witness.schema.json")
    wit = ctx.data_root / "witnesses"
    if wit.exists():
        for p in sorted(wit.rglob("*.json")):
            try:
                for err in v_wit.iter_errors(load_json(p)):
                    ctx.add(C, "FAIL", p, f"witness schema: {err.message[:200]}")
            except Exception:
                pass

    for rel, ptr in (("sources/manifest.jsonl", "/$defs/source_manifest_entry"), ("state/jobs.jsonl", "/$defs/job")):
        p = ctx.data_root / rel
        if p.exists():
            v = validator(ctx.policy_root, "records.schema.json", ptr)
            try:
                for ln, row in load_jsonl(p):
                    for err in v.iter_errors(row):
                        ctx.add(C, "FAIL", p, f"पंक्ति {ln}: {err.message[:200]}")
            except Exception:
                pass


# ---------------------------------------------------------------- R2
LOCKED_STATES = {"TEXT_LOCKED", "ANALYSED", "DRAFTED", "JUDGED", "REVISED", "SCIENCE_SCREENED", "MACHINE_COMPLETE", "RELEASED_INTERNAL"}


def r2_sanskrit_lock(ctx: Ctx) -> None:
    """R2: संस्कृत-ताला। lock हुई मूल-परत का hash न बदले; lock से पहले कोई अनुवाद न हो।"""
    C = "R2"
    for d in ctx.text_dirs():
        try:
            text = load_json(d / "_text.json")
        except Exception:
            continue
        lk_path = d / "text_lock.json"
        root_files = sorted((d / "root").rglob("*.json")) if (d / "root").exists() else []
        has_translation = (d / "translation").exists() and any((d / "translation").rglob("*.json"))
        state = text.get("state")
        if not lk_path.exists():
            if state in LOCKED_STATES:
                ctx.add(C, "FAIL", d, f"state={state} पर text_lock.json नहीं है")
            if has_translation:
                ctx.add(C, "FAIL", d, "text-lock से पहले अनुवाद-परत मौजूद है")
            continue
        try:
            lock = load_json(lk_path)
        except Exception:
            continue
        files = lock.get("files", {})
        for rf in root_files:
            rel = rf.relative_to(d).as_posix()
            if rel not in files:
                ctx.add(C, "FAIL", rf, "मूल-परत text_lock में दर्ज नहीं")
                continue
            try:
                h = canonical_segments_hash(load_json(rf)["segments"])
            except Exception:
                ctx.add(C, "FAIL", rf, "मूल-परत पढ़ी नहीं जा सकी")
                continue
            if h != files[rel]:
                ctx.add(C, "FAIL", rf, "संस्कृत पाठ lock के बाद बदला है (hash अलग)")
        for rel in files:
            if not (d / rel).exists():
                ctx.add(C, "FAIL", lk_path, f"lock में दर्ज फ़ाइल ग़ायब: {rel}")


# ---------------------------------------------------------------- R3
def _expert_badges(ctx: Ctx) -> dict:
    p = ctx.data_root / ctx.policy("thresholds.json")["badges"]["expert_badges_file"]
    if p.exists():
        try:
            return load_json(p)
        except Exception:
            return {}
    return {}


def r3_badge_honesty(ctx: Ctx) -> None:
    """R3: बैज-ईमानदारी। विशेषज्ञ-मंच के badges.json के बिना हर A/B/AV FAIL।
    AI-अनुवाद के हर श्लोक पर बैज हो; झंडा खुला हो तो बैज D ही हो; 'सत्यापित' जैसे शब्द कहीं नहीं।"""
    C = "R3"
    th = ctx.policy("thresholds.json")["badges"]
    locked = set(th["locked_until_expert_platform"])
    expert = _expert_badges(ctx).get("items", {}) if isinstance(_expert_badges(ctx), dict) else {}
    for p, obj in ctx.layer_files():
        meta = obj["_meta"]
        segs = obj.get("segments", {})
        badges = obj.get("badges", {})
        flags = obj.get("flags", {})
        for sid, b in badges.items():
            if b in locked:
                key = f"{meta.get('text_id')}/{meta.get('translation_id', meta.get('layer'))}/{sid}"
                ent = expert.get(key)
                if not ent or ent.get("badge") != b or not ent.get("reviewers") or ent.get("version") != meta.get("version"):
                    ctx.add(C, "FAIL", p, f"बैज {b} विशेषज्ञ-मंच के प्रमाण के बिना", sid)
            if sid not in segs:
                ctx.add(C, "FAIL", p, "बैज ऐसे ID पर जो segments में नहीं", sid)
            if sid in flags and b != "D":
                ctx.add(C, "FAIL", p, f"झंडा खुला है ({', '.join(flags[sid])}) पर बैज {b}", sid)
        if meta.get("ai_generated") and meta.get("layer") in ({"translation"} | AI_PROSE_LAYERS):
            for sid in segs:
                if sid not in badges:
                    ctx.add(C, "FAIL", p, "AI-परत के श्लोक पर बैज नहीं", sid)
            for where, s in iter_strings(obj):
                for rx in RE_VERIFIED:
                    if rx.search(s):
                        ctx.add(C, "FAIL", p, f"AI-output पर वर्जित शब्द /{rx.pattern}/ at {where}")
                        break
            rb = meta.get("provenance", {}).get("reviewed_by")
            if rb:
                ctx.add(C, "FAIL", p, "AI-परत पर reviewed_by भरा है, जबकि विशेषज्ञ-मंच अभी नहीं है")


# ---------------------------------------------------------------- R4
def r4_claims_lint(ctx: Ctx) -> None:
    """R4: निषिद्ध दावों का lint (AI-परतें, सूची-कार्ड के notes, annotations)।"""
    C = "R4"
    for p, obj in ctx.layer_files():
        if not obj["_meta"].get("ai_generated"):
            continue
        for sid, s in obj.get("segments", {}).items():
            for rx in RE_CLAIMS:
                if isinstance(s, str) and rx.search(s):
                    ctx.add(C, "FAIL", p, f"निषिद्ध दावा /{rx.pattern}/", sid)
    for base in ("catalog", "entities"):
        d = ctx.data_root / base
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.json")):
            if p.name == "_taxonomy.json":
                continue
            try:
                obj = load_json(p)
            except Exception:
                continue
            for where, s in iter_strings(obj):
                for rx in RE_CLAIMS + RE_VERIFIED:
                    if rx.search(s):
                        ctx.add(C, "FAIL", p, f"निषिद्ध शब्द /{rx.pattern}/ at {where}")
    for p in sorted((ctx.data_root / "texts").rglob("*.jsonl")) if (ctx.data_root / "texts").exists() else []:
        try:
            rows = load_jsonl(p)
        except Exception:
            continue
        for ln, row in rows:
            for where, s in iter_strings(row):
                for rx in RE_CLAIMS + RE_VERIFIED:
                    if rx.search(s):
                        ctx.add(C, "FAIL", p, f"पंक्ति {ln}: निषिद्ध शब्द /{rx.pattern}/")


# ---------------------------------------------------------------- R5
def r5_deity_first_person(ctx: Ctx) -> None:
    """R5: कोई AI देवता/गुरु बनकर न बोले। शास्त्र का अनुवाद (translation परत, श्लोक-ID सहित) इससे बाहर है;
    सार, टिप्पणी, नोट, annotations और docs के AI-गद्य पर लागू।"""
    C = "R5"

    def scan(p: Path, s: str, sid: str | None = None) -> None:
        for rx in RE_DEITY:
            if rx.search(s):
                ctx.add(C, "FAIL", p, f"देवता-प्रथम-पुरुष /{rx.pattern[:60]}/", sid)
                return

    for p, obj in ctx.layer_files():
        meta = obj["_meta"]
        if meta.get("layer") in AI_PROSE_LAYERS and meta.get("ai_generated"):
            for sid, s in obj.get("segments", {}).items():
                if isinstance(s, str):
                    scan(p, s, sid)
    tdir = ctx.data_root / "texts"
    if tdir.exists():
        for p in sorted(tdir.rglob("*.jsonl")):
            try:
                for _, row in load_jsonl(p):
                    for _, s in iter_strings(row):
                        scan(p, s)
            except Exception:
                pass
    for p in sorted((ctx.data_root / "docs").rglob("*.md")) if (ctx.data_root / "docs").exists() else []:
        scan(p, p.read_text(encoding="utf-8", errors="replace"))


# ---------------------------------------------------------------- R6
def _shingles(s: str, n: int = 7) -> set[str]:
    toks = re.findall(r"\w+", s.lower())
    return {" ".join(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))}


def ngram_overlap(ours: str, theirs: str, n: int = 7) -> float:
    """हमारे पाठ के n-शब्द shingles का कितना हिस्सा तुलना-स्रोत में भी है (0–1)।"""
    a = _shingles(ours, n)
    if not a:
        return 0.0
    return len(a & _shingles(theirs, n)) / len(a)


def r6_licence_gate(ctx: Ctx) -> None:
    """R6: लाइसेंस-द्वार। NC/ND/SA/अज्ञात केवल तुलना के लिए; उनका पाठ repo में कभी नहीं।"""
    C = "R6"
    allow = ctx.policy("licence_allowlist.json")
    display, compare, meta_only = set(allow["display"]), set(allow["compare_only"]), set(allow["metadata_only"])
    for p, obj in ctx.layer_files():
        meta = obj["_meta"]
        lic = meta.get("licence")
        if lic not in display:
            ctx.add(C, "FAIL", p, f"परत का लाइसेंस '{lic}' display allow-list में नहीं")
        for src in meta.get("provenance", {}).get("sources", []) or []:
            sl = src.get("licence")
            if sl not in display and src.get("usage") == "display":
                ctx.add(C, "FAIL", p, f"स्रोत '{src.get('witness_id')}' ({sl}) से प्रदर्शन-पाठ बना है; यह केवल तुलना के लिए है")
            if sl not in display | compare | meta_only:
                ctx.add(C, "FAIL", p, f"अज्ञात लाइसेंस-पहचान '{sl}' (allow-list में जोड़ें या LicenseRef-unknown लिखें)")
    wit = ctx.data_root / "witnesses"
    if wit.exists():
        for p in sorted(wit.rglob("*.json")):
            try:
                w = load_json(p)
            except Exception:
                continue
            lic, usage = w.get("licence"), w.get("usage")
            if lic not in display and usage == "display":
                ctx.add(C, "FAIL", p, f"लाइसेंस {lic} वाला गवाह display के रूप में दर्ज")
            if lic == "LicenseRef-PD-India-US" and len(w.get("licence_evidence", [])) < allow["rules"]["copyright_fact_min_sources"]:
                ctx.add(C, "FAIL", p, "PD-दावे के लिए ≥2 प्रमाण-स्रोत चाहिए; वरना सर्वाधिकार-युक्त मानें")
            if w.get("g1", {}).get("status") in ("pending_owner", "rejected") and usage == "display":
                ctx.add(C, "FAIL", p, "G1-स्वीकृति के बिना display गवाह")
            if any(k in w for k in ("text", "segments", "content")):
                ctx.add(C, "FAIL", p, "गवाह-फ़ाइल में पाठ है; यहाँ केवल metadata रहता है")
    # तुलना-स्रोत की स्थानीय प्रति (.cache/compare/<witness_id>.txt) हो तो n-gram overlap
    cache = ctx.data_root / ".cache" / "compare"
    if cache.exists():
        for p, obj in ctx.layer_files():
            if obj["_meta"].get("layer") == "root":
                continue  # मूल संस्कृत पाठ का मिलना अपेक्षित है
            ours = " ".join(v for v in obj["segments"].values() if isinstance(v, str))
            for c in cache.glob("*.txt"):
                ov = ngram_overlap(ours, c.read_text(encoding="utf-8", errors="replace"))
                if ov > 0.10:
                    ctx.add(C, "FAIL", p, f"तुलना-स्रोत '{c.stem}' से 7-शब्द overlap {ov:.0%} (>10%)")


# ---------------------------------------------------------------- R7
def r7_science_tags(ctx: Ctx) -> None:
    """R7: विज्ञान/स्वास्थ्य-दावे। इंसानी टैग के बिना दावा publish:false हो और उस पर अंतिम E-स्तर न हो।"""
    C = "R7"
    tdir = ctx.data_root / "texts"
    if not tdir.exists():
        return
    for p in sorted(tdir.rglob("claims.jsonl")):
        try:
            rows = load_jsonl(p)
        except Exception:
            continue
        for ln, row in rows:
            if row.get("tagged_by") == "human":
                ctx.add(C, "FAIL", p, f"पंक्ति {ln}: tagged_by=human, जबकि विशेषज्ञ-मंच अभी नहीं है")
                continue
            if row.get("publish") is not False:
                ctx.add(C, "FAIL", p, f"पंक्ति {ln}: बिना इंसानी टैग का दावा publish:false नहीं है")
            if row.get("e_level") is not None:
                ctx.add(C, "FAIL", p, f"पंक्ति {ln}: अंतिम E-स्तर केवल विशेषज्ञ दे सकते हैं (e_level_proposed उपयोग करें)")


# ---------------------------------------------------------------- R8
def r8_ai_label(ctx: Ctx) -> None:
    """R8: AI-label। मॉडल से बनी हर परत ai_generated:true हो और pipeline_version रखे।"""
    C = "R8"
    for p, obj in ctx.layer_files():
        meta = obj["_meta"]
        prov = meta.get("provenance", {})
        if (prov.get("model") or prov.get("model_family")) and meta.get("ai_generated") is not True:
            ctx.add(C, "FAIL", p, "मॉडल से बनी परत पर ai_generated:true नहीं")
        if meta.get("ai_generated") and not meta.get("pipeline_version"):
            ctx.add(C, "FAIL", p, "AI-परत पर pipeline_version नहीं")
        if meta.get("layer") == "root" and (meta.get("ai_generated") or prov.get("model")):
            ctx.add(C, "FAIL", p, "मूल संस्कृत परत किसी LLM ने लिखी है; LLM संस्कृत कभी नहीं लिखता")


# ---------------------------------------------------------------- R9 / R10
def _code_files(ctx: Ctx):
    for top in CODE_DIRS:
        d = ctx.data_root / top
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and "node_modules" not in p.parts and p.suffix in (
                    ".py", ".ts", ".js", ".mjs", ".yml", ".yaml", ".json", ".jsonc", ".toml", ".sh", ".gs", ".ipynb", ".sql"):
                if p.name in ("lexicon.py", "package-lock.json"):
                    continue
                yield p


def r9_allowed_platforms(ctx: Ctx) -> None:
    """R9: no-card/अनुमत मंच। code और workflows में वर्जित host न हों।"""
    C = "R9"
    pol = ctx.policy("platforms.json")
    for p in _code_files(ctx):
        s = p.read_text(encoding="utf-8", errors="replace")
        for host in pol["banned_hosts"]:
            if host in s and host not in pol["colab_automation_markers"]:  # Colab को R10 देखती है
                ctx.add(C, "FAIL", p, f"वर्जित मंच का host: {host}")


def r10_no_colab_automation(ctx: Ctx) -> None:
    """R10: Colab कभी स्वचालित नहीं।"""
    C = "R10"
    pol = ctx.policy("platforms.json")
    for p in _code_files(ctx):
        s = p.read_text(encoding="utf-8", errors="replace").lower()
        for mark in pol["colab_automation_markers"]:
            if mark.lower() in s:
                ctx.add(C, "FAIL", p, f"Colab-automation का चिह्न: {mark}")


# ---------------------------------------------------------------- R11
def r11_quota_ledger(ctx: Ctx) -> None:
    """R11: quota-खाता। किसी provider का उपयोग सीमा से ऊपर न हो; ≥90% पर चेतावनी।"""
    C = "R11"
    p = ctx.data_root / "state" / "quota_ledger.json"
    if not p.exists():
        ctx.add(C, "WARN", "state/quota_ledger.json", "quota-बही नहीं मिली")
        return
    try:
        led = load_json(p)
    except Exception:
        return
    th = ctx.policy("thresholds.json")["provider_budget"]
    for name, pr in (led.get("providers") or {}).items():
        used, limit = pr.get("used"), pr.get("limit")
        if isinstance(used, (int, float)) and isinstance(limit, (int, float)) and limit > 0:
            if used > limit:
                ctx.add(C, "FAIL", p, f"{name}: उपयोग {used} सीमा {limit} से ऊपर")
            elif used >= th["switch_at"] * limit:
                ctx.add(C, "WARN", p, f"{name}: उपयोग सीमा के {used / limit:.0%} पर")
        if pr.get("keys", 1) != 1 or pr.get("projects", 1) != 1:
            ctx.add(C, "FAIL", p, f"{name}: एक provider पर एक से ज़्यादा key/project दर्ज")


# ---------------------------------------------------------------- R12
def r12_kpi(ctx: Ctx) -> None:
    """R12: KPI-गिनती (विशेषज्ञ टले होने का रूप): अवस्था-वार ग्रंथ, C/D, खुले D। कोई त्रुटि-दर नहीं।"""
    C = "R12"
    states: dict[str, int] = {}
    per_text: dict[str, dict] = {}
    for d in ctx.text_dirs():
        try:
            t = load_json(d / "_text.json")
        except Exception:
            continue
        states[t.get("state", "?")] = states.get(t.get("state", "?"), 0) + 1
        per_text[t.get("text_id", d.name)] = {"state": t.get("state"), "declared_segments": sum(c.get("segment_count", 0) for c in t.get("chapters", [])),
                                               "root_segments": 0, "C": 0, "D": 0, "open_flags": 0, "W2+": 0, "WV": 0, "W1": 0}
    for p, obj in ctx.layer_files():
        meta = obj["_meta"]
        k = per_text.get(meta.get("text_id"))
        if k is None:
            continue
        if meta.get("layer") == "root":
            k["root_segments"] += len(obj["segments"])
            for ws in (obj.get("witness_status") or {}).values():
                if ws in k:
                    k[ws] += 1
        elif meta.get("layer") == "translation":
            for b in (obj.get("badges") or {}).values():
                if b in ("C", "D"):
                    k[b] += 1
            k["open_flags"] += sum(len(v) for v in (obj.get("flags") or {}).values())
    for tid, k in per_text.items():
        if k["state"] in ("MACHINE_COMPLETE", "RELEASED_INTERNAL") and k["root_segments"] != k["declared_segments"]:
            ctx.add(C, "FAIL", f"texts/{tid}", f"state={k['state']} पर मूल-श्लोक {k['root_segments']} ≠ घोषित {k['declared_segments']}")
    cards = 0
    cat = ctx.data_root / "catalog"
    if cat.exists():
        cards = sum(1 for p in cat.rglob("*.json") if not p.name.startswith("_") and "seed" not in p.parts)
    ctx.kpi.update({
        "catalog_cards": cards,
        "texts_by_state": states,
        "per_text": per_text,
        "segments_C": sum(k["C"] for k in per_text.values()),
        "segments_D": sum(k["D"] for k in per_text.values()),
        "open_flags_total": sum(k["open_flags"] for k in per_text.values()),
        "note": "प्रक्रिया-आँकड़े; यह कोई त्रुटि-दर नहीं है",
    })


# ---------------------------------------------------------------- R13
def r13_goal_drift_privacy(ctx: Ctx) -> None:
    """R13: लक्ष्य-भटकाव और निजता। अनजान top-level रास्ते, फ़िल्म-प्रोजेक्ट के संदर्भ, ईमेल-पते, secrets।"""
    C = "R13"
    for p in sorted(ctx.data_root.iterdir()):
        if p.name not in ALLOWED_TOP:
            ctx.add(C, "FAIL", p, "अनुमत ढाँचे से बाहर का top-level रास्ता")
    secret_rx = re.compile(r"(AIza[0-9A-Za-z_-]{30,}|gsk_[0-9A-Za-z]{30,}|ghp_[0-9A-Za-z]{30,}|gho_[0-9A-Za-z]{30,}|sk-ant-[0-9A-Za-z_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\"refresh_token\"\s*:\s*\"[^\"]{20,})")
    for p in ctx.walk():
        if p.suffix in (".png", ".jpg", ".jpeg", ".pdf", ".zip", ".gz", ".sqlite", ".parquet"):
            ctx.add(C, "FAIL", p, "binary/मीडिया फ़ाइल git में (मीडिया Drive में रहता है)")
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = ctx.rel(p)
        for m in EMAIL_RE.finditer(s):
            if not EMAIL_OK.search(m.group(0)) and not EMAIL_OK.search(s[max(0, m.start() - 20): m.end() + 5]):
                ctx.add(C, "FAIL", p, "ईमेल-जैसा पता मिला (किसी का ईमेल repo में नहीं आना चाहिए)")
                break
        if secret_rx.search(s):
            ctx.add(C, "FAIL", p, "secret/key जैसा पाठ मिला")
        if rel.split("/")[0] in CODE_DIRS and p.name != "r_checks.py" and p.suffix != ".md":
            if re.search(r"AI_Movie|gdrive:", s):
                ctx.add(C, "FAIL", p, "फ़िल्म-प्रोजेक्ट का संदर्भ (AI_Movie / gdrive:) code में")


# ---------------------------------------------------------------- R14
def r14_liveness(ctx: Ctx, now: dt.datetime | None = None) -> None:
    """R14: जीवितता। Foreman deploy होने के बाद heartbeat 48 घंटे से पुराना न हो; swarm/STOP की सूचना।"""
    C = "R14"
    now = now or dt.datetime.now(dt.timezone.utc)
    if (ctx.data_root / "swarm" / "STOP").exists():
        ctx.add(C, "WARN", "swarm/STOP", "kill-switch लगा है: स्वार्म रुका हुआ है")
    hb = ctx.data_root / "state" / "heartbeat.json"
    if not hb.exists():
        ctx.add(C, "WARN", "state/heartbeat.json", "Foreman का heartbeat अभी नहीं (क़दम 0.11 से पहले यह अपेक्षित है)")
        return
    try:
        ts = dt.datetime.fromisoformat(load_json(hb)["ts"].replace("Z", "+00:00"))
    except Exception:
        ctx.add(C, "FAIL", hb, "heartbeat पढ़ा नहीं जा सका")
        return
    age_h = (now - ts).total_seconds() / 3600
    if age_h > 48:
        ctx.add(C, "FAIL", hb, f"heartbeat {age_h:.0f} घंटे पुराना (>48)")


# ---------------------------------------------------------------- extra: ID-निरंतरता (A3 का repo-रूप)
def a3_id_continuity(ctx: Ctx) -> None:
    """A3: श्लोक-गिनती और ID-निरंतरता, _text.json के घोषणा-पत्र से; अनुवाद के ID मूल के ID के बराबर (D11)।"""
    for d in ctx.text_dirs():
        try:
            text = load_json(d / "_text.json")
        except Exception:
            continue
        tid = text.get("text_id")
        root_ids: dict[str, set[str]] = {}
        for ch in text.get("chapters", []):
            f = d / "root" / "sa-Deva" / f"{ch['chapter']}.json"
            if not f.exists():
                if text.get("state") in LOCKED_STATES:
                    ctx.add("A3", "FAIL", d, f"अध्याय {ch['chapter']} की मूल-परत नहीं")
                continue
            try:
                ids = list(load_json(f)["segments"].keys())
            except Exception:
                continue
            root_ids[ch["chapter"]] = set(ids)
            bad = [i for i in ids if not SEGMENT_ID_RE.match(i)]
            if bad:
                ctx.add("A3", "FAIL", f, f"अमान्य ID: {bad[:3]}")
            if ids != sorted(ids, key=segment_sort_key):
                ctx.add("A3", "FAIL", f, "ID क्रम में नहीं")
            full = {i for i in ids if not re.search(r"[a-d]$", i)}
            if len(full) != ch["segment_count"]:
                ctx.add("A3", "FAIL", f, f"श्लोक-गिनती {len(full)} ≠ घोषित {ch['segment_count']}")
        tr = d / "translation"
        if tr.exists():
            for f in sorted(tr.rglob("*.json")):
                try:
                    obj = load_json(f)
                except Exception:
                    continue
                ch = obj.get("_meta", {}).get("chapter")
                want = root_ids.get(ch)
                if want is None:
                    ctx.add("D11", "FAIL", f, f"अनुवाद का अध्याय {ch} मूल में नहीं")
                    continue
                got = set(obj.get("segments", {}).keys())
                if got - want:
                    ctx.add("D11", "FAIL", f, f"अनुवाद में ऐसे ID जो मूल में नहीं: {sorted(got - want)[:3]}")
                if want - got:
                    ctx.add("D11", "FAIL", f, f"अनुवाद में छूटे ID: {sorted(want - got, key=segment_sort_key)[:3]} (कुल {len(want - got)})")


ALL = [
    ("R1", r1_schema_unicode), ("R2", r2_sanskrit_lock), ("R3", r3_badge_honesty), ("R4", r4_claims_lint),
    ("R5", r5_deity_first_person), ("R6", r6_licence_gate), ("R7", r7_science_tags), ("R8", r8_ai_label),
    ("R9", r9_allowed_platforms), ("R10", r10_no_colab_automation), ("R11", r11_quota_ledger), ("R12", r12_kpi),
    ("R13", r13_goal_drift_privacy), ("R14", r14_liveness), ("A3/D11", a3_id_continuity),
]
