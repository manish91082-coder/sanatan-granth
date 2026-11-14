"""P2 2.1 की तैयारी: ईशोपनिषद् के दो e-text गवाहों का पहला मशीन-मिलान (v0)।

    python tools/witness/isha_collate.py --fetch

गवाह (दोनों संस्कृत विकिस्रोत, CC BY-SA → केवल तुलना; पाठ git में नहीं जाता):
  A  'ईशोपनिषत्'                 काण्व क्रम, 18 मंत्र, संधि-युक्त टंकण
  B  'शुक्लयजुर्वेदः/अध्यायः ४०'  माध्यन्दिन पाठ, 17 मंत्र, पदच्छेद-शैली; हर मंत्र पर गवाह का अपना "काण्वN" संदर्भ

ID कहाँ से: A के ॥ N ॥ चिह्नों से; B के लिए गवाह के अपने काण्व-संदर्भ से (lookup)। कोई ID अनुमान से नहीं।
नतीजा: audit/witness/isha_collation_v0.json — हर मंत्र पर कुंजी बराबर/अलग, समानता-अनुपात, और दोनों कुंजियों
के hash। पाठ या उसके अंश रिपोर्ट में नहीं जाते।

यह lock नहीं है। दोनों गवाहों की स्वतंत्रता (नक़ल-परिवार) अभी सिद्ध नहीं, और प्रदर्शन-पाठ के लिए
सार्वजनिक-डोमेन छपा संस्करण (अपना OCR) अभी बाक़ी है।
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from key import key  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / ".cache" / "witness" / "isha"
UA = "sanatan-granth-catalog/0.1 (open library project; github sanatan-granth)"
PAGES = {"sa_ws_isha": "ईशोपनिषत्", "sa_ws_vsm40": "शुक्लयजुर्वेदः/अध्यायः ४०"}
DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for k, title in PAGES.items():
        params = dict(action="query", prop="revisions", rvprop="content|ids|timestamp", rvslots="main", titles=title, format="json", formatversion="2")
        req = urllib.request.Request("https://sa.wikisource.org/w/api.php?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
        (CACHE / f"{k}.json").write_bytes(urllib.request.urlopen(req, timeout=60).read())


def load(k: str) -> tuple[dict, str]:
    rev = json.loads((CACHE / f"{k}.json").read_bytes())["query"]["pages"][0]["revisions"][0]
    text = unicodedata.normalize("NFC", rev["slots"]["main"]["content"])
    meta = {"witness_id": k.replace("_", "-"), "host": "sa.wikisource.org", "title": PAGES[k], "revid": rev["revid"],
            "timestamp": rev["timestamp"], "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "licence": "CC-BY-SA-4.0", "usage": "compare"}
    return meta, text


def parse_a(text: str) -> dict[int, str]:
    body = text[text.find("॥ अथ ईशोपनिषत् ॥") + len("॥ अथ ईशोपनिषत् ॥"): text.find("॥ इति ईशोपनिषत् ॥")]
    out, last = {}, 0
    for m in re.finditer(r"॥\s*([०-९]+)\s*॥", body):
        out[int(m.group(1).translate(DEVA_DIGITS))] = body[last:m.start()].strip()
        last = m.end()
    return out


def parse_b(text: str) -> tuple[dict[int, str], dict[int, int | None]]:
    body = text[: text.find("</poem>")]
    blocks = re.split(r"\n40\.(\d+)\s*\{([^}]*)\}", body)
    out, conc = {}, {}
    for i in range(1, len(blocks), 3):
        n, refs, txt = int(blocks[i]), blocks[i + 1], blocks[i + 2]
        m = re.search(r"काण्व\s*(\d+)", refs)
        conc[n] = int(m.group(1)) if m else None
        out[n] = re.sub(r"<[^>]+>", "", txt).strip()
    return out, conc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if a.fetch or not all((CACHE / f"{k}.json").exists() for k in PAGES):
        fetch()
    ma, ta = load("sa_ws_isha")
    mb, tb = load("sa_ws_vsm40")
    A = parse_a(ta)
    B, conc = parse_b(tb)
    k2m = {k: m for m, k in conc.items() if k is not None}
    rows = []
    for n in sorted(A):
        ka = key(A[n])
        row = {"segment": f"isha:{n}", "a_key_sha256": hashlib.sha256(ka.encode()).hexdigest(), "a_key_len": len(ka)}
        m = k2m.get(n)
        if m is None:
            row.update(b_ref=None, status="b_absent", note="गवाह B में इस काण्व-मंत्र का संदर्भ नहीं")
        else:
            kb = key(B[m])
            ratio = difflib.SequenceMatcher(None, ka, kb).ratio()
            row.update(b_ref=f"VS(M) 40.{m}", b_key_sha256=hashlib.sha256(kb.encode()).hexdigest(), b_key_len=len(kb),
                       similarity=round(ratio, 4), status="key_equal" if ka == kb else ("near" if ratio >= 0.97 else "differs"))
        rows.append(row)
    summary: dict[str, int] = {}
    for r in rows:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    rep = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "text_id": "isha", "tool": "tools/witness/isha_collate.py v0", "key": "tools/witness/key.py",
        "witnesses": [ma, mb],
        "id_source": {"A": "गवाह के ॥ N ॥ चिह्न", "B": "गवाह का अपना काण्व-संदर्भ", "b_concordance_madhyandina_to_kanva": conc},
        "counts": {"a_segments": len(A), "b_segments": len(B)},
        "summary": summary, "segments": rows,
        "limits": ["यह text-lock नहीं है", "दोनों गवाहों की स्वतंत्रता (नक़ल-परिवार) अभी सिद्ध नहीं",
                   "B दूसरी शाखा (माध्यन्दिन) का पाठ है; 'differs' में असली शाखा-भेद भी हैं, केवल टंकण-भूलें नहीं",
                   "प्रदर्शन-पाठ के लिए सार्वजनिक-डोमेन छपा संस्करण (अपना OCR) बाक़ी", "रिपोर्ट में पाठ नहीं, केवल hash और अनुपात"],
    }
    out = REPO / "audit" / "witness" / "isha_collation_v0.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"counts": rep["counts"], "summary": summary,
                      "per_segment": [(r["segment"], r.get("b_ref"), r["status"], r.get("similarity")) for r in rows]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
