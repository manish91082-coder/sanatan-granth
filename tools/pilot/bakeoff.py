"""Bake-off: मुफ़्त मॉडलों में कौन ड्राफ़्टर के रूप में कितना ठीक है (एक ग्रंथ पर माप)।

    python -m tools.pilot.bakeoff --text isha --out <dir> [--candidates <ref,ref,...>]

हर उम्मीदवार पूरा ग्रंथ अनुवाद करता है; फिर दो जज (उम्मीदवार से अलग परिवार के) हर ड्राफ़्ट को अकेले जाँचते हैं।
यह मानव-समीक्षा नहीं है: जज भी मॉडल हैं। नतीजा केवल मॉडल चुनने का संकेत है, गुणवत्ता का प्रमाण नहीं।
"~<regex>" वाला Google-संदर्भ AI Studio की मॉडल-सूची से नाम खोजता है (जैसे "google_ai_studio:~3\\.8-flash$")।
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools" / "witness"))

from tools.pilot.llm import GEMINI_BASE, Model, Usage, _http, available, parse_model  # noqa: E402
from tools.pilot.run_e2e import LABELS, OK_LABELS, draft, judge_one, load_source, now_iso, write_json  # noqa: E402

# Flash-वर्ग (मुफ़्त quota 20/दिन, 16 नवंबर को ख़त्म मिला) और nemotron (अनुरोध अटकता रहा) default सूची में नहीं; --candidates से जोड़े जा सकते हैं।
CANDIDATES = [
    "google_ai_studio:~gemma-4-31b-it$", "groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b", "google_ai_studio:gemini-3.5-flash-lite",
]
PANEL = ["google_ai_studio:gemini-3.5-flash-lite", "groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b"]
_GEMINI_NAMES: list[str] | None = None


def gemini_names() -> list[str]:
    global _GEMINI_NAMES
    if _GEMINI_NAMES is None:
        st, js, _ = _http("GET", f"{GEMINI_BASE}/models?pageSize=200", {"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "")}, None, 60)
        _GEMINI_NAMES = sorted(m["name"].split("/")[-1] for m in js.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])) if st == 200 else []
    return _GEMINI_NAMES


def resolve(ref: str) -> Model | None:
    provider, _, name = ref.partition(":")
    if name.startswith("~"):
        hits = sorted((n for n in gemini_names() if re.search(name[1:], n)), key=len)
        if not hits:
            return None
        ref = f"{provider}:{hits[0]}"
    m = parse_model(ref)
    return m if available(m) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="isha")
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidates", default="")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out, t0 = Path(a.out), time.time()
    segs, src_meta = load_source(a.text)
    ids = sorted(segs, key=lambda s: int(s.split(":")[1]))
    refs = [r.strip() for r in a.candidates.split(",") if r.strip()] or CANDIDATES
    panel = [m for m in (resolve(r) for r in PANEL) if m]
    rows, drafts_out, skipped, dead = [], {}, [], []
    panel_start = [m.ref for m in panel]

    def save() -> dict:
        ranked = sorted(rows, key=lambda r: (-(r["ok_by_all_judges"] / r["of"]), r["not_ok_by_all_judges"]))
        rep = {"generated_at": now_iso(), "text_id": a.text, "segments": len(ids), "run": os.environ.get("GITHUB_RUN_ID"), "carrier_sha256": src_meta["sha256"],
               "panel": panel_start, "judges_dropped": dead, "skipped": skipped, "seconds_total": round(time.time() - t0, 1), "results": ranked,
               "limits": ["जज भी मॉडल हैं; यह मानव-समीक्षा नहीं", "एक छोटा ग्रंथ (18 मंत्र): क्रम केवल संकेत है",
                          "हर उम्मीदवार को उसके अपने परिवार का जज नहीं जाँचता, इसलिए जज-जोड़ी हर उम्मीदवार के लिए एक-सी नहीं"]}
        write_json(out / "report" / f"bakeoff_{a.text}.json", rep)
        write_json(out / "report" / f"bakeoff_{a.text}_drafts.json", {"_meta": {"label": "AI-मसौदा · मानव-समीक्षा नहीं", "ai_generated": True, "generated_at": rep["generated_at"]}, "drafts": drafts_out})
        return rep
    for ref in refs:
        m = resolve(ref)
        if not m:
            skipped.append(ref)
            continue
        u = Usage()
        ts = time.time()
        d = draft(m, segs, ids, u)
        row: dict = {"model": m.ref, "family": m.family, "drafted": len(d), "of": len(ids), "draft_seconds": round(time.time() - ts, 1), "draft_usage": u.as_dict(), "judges": {}}
        print(f"[draft] {m.ref}: {len(d)}/{len(ids)} · {row['draft_seconds']} s · 429={u.http_429} · errors={u.errors[:2]}", file=sys.stderr)
        verdicts: dict[str, dict[str, dict]] = {}
        if d:
            seen_fam: set[str] = set()
            for jm in list(panel):
                if len(verdicts) >= 2:
                    break
                if jm.family == m.family or jm.family in seen_fam:
                    continue
                uj = Usage()
                v = judge_one(jm, segs, d, uj)
                if not v:  # यह जज अभी उत्तर नहीं दे रहा: बाक़ी उम्मीदवारों के लिए भी हटा दें
                    panel.remove(jm)
                    dead.append({"judge": jm.ref, "errors": uj.errors[:2]})
                    print(f"  [judge बंद] {jm.ref}: {uj.errors[:2]}", file=sys.stderr)
                    continue
                seen_fam.add(jm.family)
                verdicts[jm.ref] = v
                counts = {lab: sum(1 for x in v.values() if x["label"] == lab) for lab in sorted(LABELS)}
                row["judges"][jm.ref] = {"family": jm.family, "judged": len(v), "counts": counts,
                                         "not_ok_ids": [i for i in ids if i in v and v[i]["label"] not in OK_LABELS], "usage": uj.as_dict()}
                print(f"  [judge] {jm.ref}: {counts}", file=sys.stderr)
        full = [i for i in d if verdicts and all(i in v for v in verdicts.values())]
        row["judged_by_all"] = len(full)
        row["ok_by_all_judges"] = sum(1 for i in full if all(v[i]["label"] in OK_LABELS for v in verdicts.values()))
        row["not_ok_by_all_judges"] = sum(1 for i in full if all(v[i]["label"] not in OK_LABELS for v in verdicts.values()))
        row["judges_split"] = len(full) - row["ok_by_all_judges"] - row["not_ok_by_all_judges"]
        rows.append(row)
        drafts_out[m.ref] = [{"id": i, "en": d[i]["en"], "hi": d[i]["hi"], "verdicts": {k: v.get(i) for k, v in verdicts.items()}} for i in ids if i in d]
        save()  # हर उम्मीदवार के बाद: run बीच में रुके तो भी अब तक का माप बचे
    rep = save()
    print(json.dumps({"panel": rep["panel"], "judges_dropped": dead, "skipped": skipped, "seconds_total": rep["seconds_total"],
                      "results": [{k: r[k] for k in ("model", "drafted", "ok_by_all_judges", "not_ok_by_all_judges", "judges_split", "draft_seconds")} | {"judges": {k: v["counts"] for k, v in r["judges"].items()}, "errors": r["draft_usage"]["errors"][:1]}
                                  for r in rep["results"]]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
