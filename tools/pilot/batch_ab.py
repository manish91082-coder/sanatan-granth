"""P2 2.2: batch-आकार की तुलना (एक अनुरोध में कितने श्लोक), गीता अध्याय 1–2 पर।

    python -m tools.pilot.batch_ab --out <dir> [--chapters 1,2] [--sizes 10,30,60] [--models <ref,ref,...>] [--judge-sample 18] [--mock]

हर (मॉडल, आकार) के लिए श्लोक एक ही बार भेजे जाते हैं: जो श्लोक न लौटे वह दोबारा नहीं माँगा जाता, टुकड़ा छोटा नहीं किया जाता
(429 या 5xx पर llm.py का सामान्य दोहराव चलता है, और उसका समय गिना जाता है)। यही नापना है कि
उस आकार पर पहली बार में क्या लौटता है: कितने श्लोक लौटे, कितने चुपचाप छूटे, कितने अमान्य रहे, कितना समय और कितने tokens लगे।
गुणवत्ता का मोटा संकेत: हर स्थिति में वही तय नमूना (हर N-वाँ श्लोक) एक दूसरे परिवार के जज को अकेले-ड्राफ़्ट वाली जाँच
(judge_one) के लिए जाता है। जज AI है; यह मानव-समीक्षा नहीं है।

स्रोत: tools/witness/gita_collate.py (वाहक-गवाह; CC BY-SA, केवल परीक्षण)। कोई अनुवाद repo में नहीं जाता: रिपोर्ट में केवल
गिनतियाँ, समय और label हैं।
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools" / "witness"))

from tools.pilot.llm import Model, Usage, available, chat_json, parse_model  # noqa: E402
from tools.pilot.run_e2e import DRAFT_SYSTEM, LABELS, OK_LABELS, _valid_draft, judge_one, now_iso, seg_key, write_json  # noqa: E402

# क्रम: तेज़ मॉडल पहले; Gemma सबसे धीमा है, इसलिए अंत में (job की समय-सीमा पर वही कटे)।
MODELS = ["google_ai_studio:gemini-3.5-flash-lite", "groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b", "google_ai_studio:gemma-4-31b-it"]
JUDGES = ["google_ai_studio:gemini-3.5-flash-lite", "groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b"]


def run_condition(model: Model, size: int, segs: dict[str, str], ids: list[str], mock: bool) -> tuple[dict, dict[str, dict]]:
    u = Usage()
    got: dict[str, dict] = {}
    stats = {"model": model.ref, "family": model.family, "batch_size": size, "requests": 0, "requests_failed": 0, "returned": 0,
             "invalid": 0, "extra_ids": 0, "stopped_early": False}
    failed_in_a_row = 0
    t0 = time.time()
    for k in range(0, len(ids), size):
        part = ids[k:k + size]
        stats["requests"] += 1
        if mock:
            items = [{"id": i, "en": f"Mock translation of {i}.", "hi": f"नक़ली अनुवाद {i}।"} for i in part]
        else:
            try:
                obj = chat_json(model, DRAFT_SYSTEM, "Translate these segments.\n" + "\n".join(f"{i}: {segs[i]}" for i in part), u, est_out=350 * len(part))
            except RuntimeError:
                stats["requests_failed"] += 1
                failed_in_a_row += 1
                if failed_in_a_row >= 2:  # इस आकार पर यह मॉडल नहीं चल रहा: बाक़ी अनुरोध बेकार हैं
                    stats["stopped_early"] = True
                    break
                continue
            failed_in_a_row = 0
            items = obj.get("items", []) if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        for it in items if isinstance(items, list) else []:
            i = it.get("id") if isinstance(it, dict) else None
            if i not in part:
                stats["extra_ids"] += 1
            elif i not in got:
                if _valid_draft(it, segs[i]):
                    got[i] = {"en": it["en"].strip(), "hi": it["hi"].strip()}
                else:
                    stats["invalid"] += 1
    stats["returned"] = len(got)
    stats["of"] = len(ids)
    stats["missing"] = len(ids) - len(got)
    stats["seconds"] = round(time.time() - t0, 1)
    stats["seconds_per_segment"] = round(stats["seconds"] / len(got), 2) if got else None
    stats["usage"] = u.as_dict()
    return stats, got


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--chapters", default="1,2")
    ap.add_argument("--sizes", default="10,30,60")
    ap.add_argument("--models", default="")
    ap.add_argument("--judge-sample", type=int, default=18)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import gita_collate  # noqa: PLC0415

    chapters = [int(x) for x in a.chapters.split(",") if x.strip()]
    sizes = [int(x) for x in a.sizes.split(",") if x.strip()]
    out, t0 = Path(a.out), time.time()
    for attempt in range(3):
        try:
            gita_collate.fetch(chapters)
            break
        except Exception:  # noqa: BLE001
            if attempt == 2 and not all((gita_collate.CACHE / f"sa_ws_gita_{c}.json").exists() for c in chapters):
                raise
            time.sleep(5 * (attempt + 1))
    segs, metas = gita_collate.segments(chapters)
    ids = sorted(segs, key=seg_key)
    step = max(1, len(ids) // max(1, a.judge_sample))
    sample = ids[::step][:a.judge_sample] if a.judge_sample > 0 else []

    if a.mock:
        models, judges, skipped = [Model("mock", "mock-a", "mock-a")], [], []
    else:
        refs = [r.strip() for r in a.models.split(",") if r.strip()] or MODELS
        models = [m for m in (parse_model(r) for r in refs) if available(m)]
        skipped = [r for r in refs if not available(parse_model(r))]
        judges = [m for m in (parse_model(r) for r in JUDGES) if available(m)]
    dead_judges: set[str] = set()
    results: list[dict] = []

    def save() -> dict:
        rep = {"generated_at": now_iso(), "text_id": "gita", "chapters": chapters, "segments": len(ids), "sizes": sizes, "run": os.environ.get("GITHUB_RUN_ID"),
               "mock": a.mock, "witnesses": [{k: m[k] for k in ("witness_id", "revid", "sha256", "licence")} for m in metas],
               "judge_sample": sample, "no_key": skipped, "seconds_total": round(time.time() - t0, 1), "results": results,
               "limits": ["हर स्थिति एक ही बार चली: दरें संकेत हैं, औसत नहीं", "गुणवत्ता का label AI-जज का है, और केवल नमूने पर",
                          "स्रोत वाहक-गवाह है (lock नहीं); कोई अनुवाद repo में नहीं गया", "मुफ़्त स्तर की सीमाएँ दिन और घंटे के हिसाब से बदलती हैं"]}
        write_json(out / "report" / "batch_ab_gita.json", rep)
        return rep

    for m in models:
        for size in sizes:
            stats, got = run_condition(m, size, segs, ids, a.mock)
            # गुणवत्ता का नमूना: पहला उपलब्ध जज जो ड्राफ़्टर के परिवार का न हो
            jd = {i: got[i] for i in sample if i in got}
            q: dict = {"sampled": len(jd)}
            if jd and not a.mock:
                for j in judges:
                    if j.family == m.family or j.ref in dead_judges:
                        continue
                    ju = Usage()
                    v = judge_one(j, segs, jd, ju)
                    if len(v) * 2 <= len(jd):
                        dead_judges.add(j.ref)
                        continue
                    q.update(judge=j.ref, judged=len(v), labels={lab: sum(1 for x in v.values() if x["label"] == lab) for lab in LABELS},
                             ok_rate=round(sum(1 for x in v.values() if x["label"] in OK_LABELS) / len(v), 3), judge_usage=ju.as_dict())
                    break
            stats["quality_sample"] = q
            results.append(stats)
            print(f"[batch] {m.ref} size={size}: returned {stats['returned']}/{stats['of']} invalid={stats['invalid']} failed_requests={stats['requests_failed']} "
                  f"{stats['seconds']} s quality={ {k: q.get(k) for k in ('judge', 'judged', 'ok_rate')} } errors={stats['usage'].get('errors', [])[:1]}", file=sys.stderr)
            save()
    rep = save()
    print(json.dumps({"segments": rep["segments"], "seconds_total": rep["seconds_total"],
                      "results": [{k: r.get(k) for k in ("model", "batch_size", "requests", "requests_failed", "returned", "missing", "invalid", "seconds", "seconds_per_segment")}
                                  | {"ok_rate": r["quality_sample"].get("ok_rate")} for r in rep["results"]]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
