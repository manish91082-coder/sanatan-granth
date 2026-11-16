"""छपे संस्करण के OCR का e-text गवाह से मिलान (P2 2.1 की तैयारी)।

    python tools/witness/ocr_collate.py --ocr-dir <dir> --witness-id <id> --engine <नाम> --out <report.json>

OCR में शोर होता है, इसलिए यहाँ "कुंजी बराबर" की जगह दो नाप हैं:
  contained  मंत्र की पूरी तुलना-कुंजी OCR की कुंजी-धारा में ज्यों-की-त्यों मिली (यही असली सहमति है)
  coverage   मंत्र की कुंजी के कितने अक्षर, उसी क्रम में, OCR की सबसे अच्छी खिड़की में मिले (0..1)

यह lock नहीं है। coverage ऊँचा होना केवल इतना कहता है कि छपे पन्ने पर लगभग वही पाठ है; असली
पाठभेद और OCR-भूल में फ़र्क़ इससे नहीं होता। रिपोर्ट में पाठ नहीं जाता: केवल hash, लंबाई और अनुपात।
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import isha_collate  # noqa: E402
from key import key  # noqa: E402

STRONG, PARTIAL = 0.95, 0.80


def best_window(mkey: str, stream: str) -> tuple[float, int]:
    """(coverage, खिड़की की शुरुआत)। पहले trigram-गिनती से उम्मीदवार खिड़कियाँ, फिर क्रम-सहित मिलान।"""
    if not mkey or not stream:
        return 0.0, -1
    w = int(len(mkey) * 1.2) + 8
    grams = {mkey[i:i + 3] for i in range(len(mkey) - 2)}
    hits = [1 if stream[i:i + 3] in grams else 0 for i in range(max(len(stream) - 2, 0))]
    pref = [0]
    for h in hits:
        pref.append(pref[-1] + h)
    cands = []
    for i in range(0, max(len(stream) - 2, 1), 4):
        j = min(i + w, len(hits))
        cands.append((pref[j] - pref[i], i))
    cands.sort(reverse=True)
    best, at = 0.0, -1
    for _, i in cands[:25]:
        sm = difflib.SequenceMatcher(None, mkey, stream[i:i + w], autojunk=False)
        cov = sum(b.size for b in sm.get_matching_blocks()) / len(mkey)
        if cov > best:
            best, at = cov, i
    return best, at


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr-dir", required=True)
    ap.add_argument("--witness-id", required=True)
    ap.add_argument("--engine", required=True, help="जैसे 'tesseract 5.x san(best)'")
    ap.add_argument("--source", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    isha_collate.fetch()
    meta, text = isha_collate.load("sa_ws_isha")
    A = isha_collate.parse_a(text)

    pages = sorted(Path(a.ocr_dir).glob("*.txt"))
    raw = "\n".join(unicodedata.normalize("NFC", p.read_text(encoding="utf-8", errors="replace")) for p in pages)
    stream = key(raw)

    rows, summary = [], {}
    for n in sorted(A):
        mk = key(A[n])
        contained = mk in stream
        cov, _ = (1.0, 0) if contained else best_window(mk, stream)
        status = "key_contained" if contained else ("ocr_strong" if cov >= STRONG else ("ocr_partial" if cov >= PARTIAL else "ocr_weak"))
        summary[status] = summary.get(status, 0) + 1
        rows.append({"segment": f"isha:{n}", "a_key_sha256": hashlib.sha256(mk.encode()).hexdigest(), "a_key_len": len(mk),
                     "coverage": round(cov, 4), "status": status})
    covs = [r["coverage"] for r in rows]
    rep = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "text_id": "isha", "tool": "tools/witness/ocr_collate.py v0", "key": "tools/witness/key.py",
        "reference_witness": meta,
        "ocr_witness": {"witness_id": a.witness_id, "engine": a.engine, "source": a.source, "pages": len(pages),
                        "ocr_key_len": len(stream), "ocr_key_sha256": hashlib.sha256(stream.encode()).hexdigest()},
        "thresholds": {"ocr_strong": STRONG, "ocr_partial": PARTIAL},
        "summary": summary,
        "coverage_min_mean_max": [round(min(covs), 4), round(sum(covs) / len(covs), 4), round(max(covs), 4)] if covs else None,
        "segments": rows,
        "limits": ["यह text-lock नहीं है", "coverage OCR-भूल और असली पाठभेद में फ़र्क़ नहीं करता",
                   "संदर्भ-गवाह (विकिस्रोत) का नक़ल-परिवार अज्ञात है", "रिपोर्ट में पाठ नहीं, केवल hash और अनुपात"],
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"witness": a.witness_id, "engine": a.engine, "pages": len(pages), "ocr_key_len": len(stream), "summary": summary,
                      "coverage_min_mean_max": rep["coverage_min_mean_max"],
                      "per_segment": [(r["segment"], r["status"], r["coverage"]) for r in rows]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
