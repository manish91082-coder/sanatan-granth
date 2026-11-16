"""जज-परीक्षा (canary-शैली): जानबूझकर बिगाड़ा गया अनुवाद जज पकड़ता है या नहीं।

    python -m tools.pilot.judge_test --text isha --out <dir> [--judges <ref,ref,...>] [--mock]

तरीका: repo में रखे AI-मसौदे (audit/pilot/<text>_e2e.json) को आधार मानकर हर मंत्र की एक बिगड़ी नक़ल बनती है, जिसमें नियम से
ठीक एक ग़लती डाली जाती है (संख्या बदलना, निषेध हटाना, नाम बदलना, विलोम रखना)। फिर जज को वही जोड़ा मिलता है जो असली कड़ी में
मिलता है (वही prompt, वही A/B क्रम-बदल)। अच्छा जज बिगड़ी नक़ल को CONTRADICTED कहेगा और आधार को चुनेगा।

यह क्या नापता है: मोटी ग़लती पकड़ने की क्षमता (ग़लती हमने डाली है, इसलिए उत्तर पता है)।
यह क्या नहीं नापता: बारीक संस्कृत-अर्थ की समझ, और यह कि आधार-मसौदा ख़ुद सही है या नहीं। यह मानव-समीक्षा नहीं है।
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools" / "witness"))

from tools.pilot.llm import Model, Usage, available, parse_model  # noqa: E402
from tools.pilot.run_e2e import OK_LABELS, accepted, judge, load_source, now_iso, write_json  # noqa: E402

JUDGES = [
    "google_ai_studio:gemma-4-31b-it", "google_ai_studio:gemini-3.5-flash-lite",
    "cloudflare:@cf/mistralai/mistral-small-3.1-24b-instruct", "cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "cloudflare:@cf/openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
]
HI = "[ऀ-ॿ]"
# (नाम, अंग्रेज़ी pattern, बदलाव, [(हिंदी pattern, बदलाव), ...])। हर मंत्र पर पहला लागू नियम, केवल पहली जगह।
RULES: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    ("संख्या: hundred→sixty", r"\bhundred\b", "sixty", [(rf"सौ(?!{HI})", "साठ")]),
    ("नाम: Agni→Indra", r"\bAgni\b", "Indra", [(r"अग्नि", "इंद्र"), (r"अग्ने", "इंद्र")]),
    ("नाम: Pushan→Varuna", r"\bPus(?:h)?an\b", "Varuna", [(r"पूषन्", "वरुण"), (r"पूषन", "वरुण")]),
    ("विलोम: darkness→light", r"\bdarkness\b", "light", [(r"अंधकार", "प्रकाश"), (r"अन्धकार", "प्रकाश")]),
    ("विलोम: far→near", r"\bfar\b", "near", [(r"दूर", "पास")]),
    ("विलोम: swifter→slower", r"\bswifter\b", "slower", [(r"अधिक वेगवान्?", "अधिक धीमा"), (r"तेज़", "धीमा")]),
    ("विलोम: golden→iron", r"\bgolden\b", "iron", [(r"स्वर्ण", "लोहे"), (r"सुनहर[ेा]", "लोहे के")]),
    ("विलोम: all beings→no beings", r"\ball beings\b", "no beings", [(r"सभी प्राणियों", "किसी भी प्राणी"), (r"सब भूत", "कोई भूत नहीं")]),
    ("विलोम: immortality→death", r"\bimmortality\b", "death", [(r"अमृतत्व", "मृत्यु"), (r"अमरत्व", "मृत्यु"), (r"अमृत", "मृत्यु")]),
    ("विलोम: knowledge→ignorance", r"\bknowledge\b", "ignorance", [(r"(?<!अ)विद्या", "अविद्या")]),
    ("निषेध हटाना", r"\b(does|do|did|is|are|was|were|should|can|will) not\b", r"\1", [(r"नहीं\s*", ""), (rf"(?<!{HI})मत\s+", "")]),
    ("विलोम: pervaded→abandoned", r"\bpervaded\b", "abandoned", [(r"व्याप्त", "त्यक्त")]),
    ("विलोम: remember→forget", r"\bremember\b", "forget", [(r"स्मर", "भूल")]),
]


def corrupt(n: int, en: str, hi: str) -> dict | None:
    """मंत्र-संख्या के हिसाब से नियमों का क्रम घुमाया जाता है, ताकि हर मंत्र पर एक ही तरह की ग़लती न पड़े।"""
    k = n % len(RULES)
    for name, en_rx, en_to, hi_alts in RULES[k:] + RULES[:k]:
        en2, hits = re.subn(en_rx, en_to, en, count=1)
        if not hits or en2 == en:
            continue
        hi2, hi_changed = hi, False
        for hi_rx, hi_to in hi_alts:
            cand, h = re.subn(hi_rx, hi_to, hi, count=1)
            if h and cand != hi:
                hi2, hi_changed = cand, True
                break
        return {"rule": name, "en": en2, "hi": hi2, "hi_changed": hi_changed}
    return None


def score(items: dict[str, dict], verdicts: dict[str, dict]) -> dict:
    """verdicts में a = आधार, b = बिगड़ी नक़ल (judge() क्रम-बदल को ख़ुद उलट देता है)।"""
    got = [i for i in items if i in verdicts]
    n = len(got)
    if not n:
        return {"judged": 0}
    caught = [i for i in got if verdicts[i]["b_label"] == "CONTRADICTED"]
    passed = [i for i in got if verdicts[i]["b_label"] in OK_LABELS]
    picked_base = [i for i in got if verdicts[i]["pick"] == "A"]
    return {"judged": n, "of": len(items),
            "caught": len(caught), "catch_rate": round(len(caught) / n, 3),
            "picked_base": len(picked_base), "pick_rate": round(len(picked_base) / n, 3),
            "passed_corrupt_as_ok": len(passed), "passed_ids": passed,
            "said_same_meaning": sum(1 for i in got if verdicts[i]["agree"]),
            "accepted_corrupt": sum(1 for i in got if accepted(verdicts[i]) and verdicts[i]["pick"] == "B"),
            "base_flagged_contradicted": sum(1 for i in got if verdicts[i]["a_label"] == "CONTRADICTED"),
            "missed_ids": [i for i in got if i not in caught]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="isha")
    ap.add_argument("--out", required=True)
    ap.add_argument("--judges", default="")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out, t0 = Path(a.out), time.time()
    base_path = REPO / "audit" / "pilot" / f"{a.text}_e2e.json"
    base_raw = base_path.read_bytes()
    base = {s["id"]: {"en": s["en"], "hi": s["hi"]} for s in json.loads(base_raw.decode("utf-8"))["segments"] if s.get("en") and s.get("hi")}
    segs, src_meta = load_source(a.text)

    items: dict[str, dict] = {}
    for i in sorted(base, key=lambda s: int(s.split(":")[1])):
        if i not in segs:
            continue
        c = corrupt(int(i.split(":")[1]), base[i]["en"], base[i]["hi"])
        if c:
            items[i] = c
    pairs = {i: (base[i], {"en": c["en"], "hi": c["hi"]}) for i, c in items.items()}
    print(f"[जज-परीक्षा] {len(items)}/{len(base)} मंत्रों पर ग़लती डाली गई", file=sys.stderr)

    if a.mock:
        judges = [Model("mock", "mock-j", "mock-j")]
        skipped: list[str] = []
    else:
        refs = [r.strip() for r in a.judges.split(",") if r.strip()] or JUDGES
        judges = [m for m in (parse_model(r) for r in refs) if available(m)]
        skipped = [r for r in refs if not available(parse_model(r))]

    results, detail = [], {i: {"rule": c["rule"], "hi_changed": c["hi_changed"], "verdicts": {}} for i, c in items.items()}

    def save() -> dict:
        ranked = sorted(results, key=lambda r: (-(r.get("catch_rate") or 0), -(r.get("pick_rate") or 0)))
        rep = {"generated_at": now_iso(), "text_id": a.text, "run": os.environ.get("GITHUB_RUN_ID"), "mock": a.mock,
               "base_file": f"audit/pilot/{a.text}_e2e.json", "base_sha256": hashlib.sha256(base_raw).hexdigest(), "carrier_sha256": src_meta["sha256"],
               "items": len(items), "rules_used": sorted({c["rule"] for c in items.values()}), "no_key": skipped,
               "seconds_total": round(time.time() - t0, 1), "results": ranked, "per_item": detail,
               "limits": ["ग़लतियाँ मोटी और नियम से डाली गई हैं: यह बारीक अर्थ की समझ नहीं नापता", "आधार AI-मसौदा है; वह ख़ुद ग़लत हो सकता है",
                          "एक छोटा ग्रंथ: दरें केवल संकेत हैं", "यह मानव-समीक्षा नहीं है"]}
        write_json(out / "report" / f"judge_test_{a.text}.json", rep)
        return rep

    for m in judges:
        u = Usage()
        ts = time.time()
        v = judge(m, segs, pairs, u)
        row = {"judge": m.ref, "family": m.family, **score(items, v), "seconds": round(time.time() - ts, 1), "usage": u.as_dict()}
        results.append(row)
        for i, x in v.items():
            detail[i]["verdicts"][m.ref] = {"base": x["a_label"], "corrupt": x["b_label"], "pick_base": x["pick"] == "A", "agree": x["agree"]}
        print(f"[जज] {m.ref}: {({k: row.get(k) for k in ('judged', 'caught', 'picked_base', 'passed_corrupt_as_ok', 'base_flagged_contradicted', 'seconds')})} errors={u.errors[:1]}", file=sys.stderr)
        save()
    rep = save()
    print(json.dumps({"items": rep["items"], "no_key": skipped, "seconds_total": rep["seconds_total"],
                      "results": [{k: r.get(k) for k in ("judge", "judged", "caught", "catch_rate", "picked_base", "pick_rate", "passed_corrupt_as_ok",
                                                         "accepted_corrupt", "base_flagged_contradicted", "seconds")} for r in rep["results"]]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
