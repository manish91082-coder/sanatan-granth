"""P2 2.2 की तैयारी: भगवद्गीता के अध्यायों का वाहक-गवाह (संस्कृत विकिस्रोत) और उससे श्लोक-विभाजन (v0)।

    python tools/witness/gita_collate.py --fetch [--chapters 1,2]

गवाह: संस्कृत विकिस्रोत के पन्ने 'भगवद्गीता/<अध्याय-नाम>' (CC BY-SA → केवल तुलना और परीक्षण; पाठ git में नहीं जाता)।
पन्ने में हर श्लोक अपने <poem> खंड में है और उसका क्रमांक गवाह का अपना है (॥१-२॥ = अध्याय 1, श्लोक 2); व्याख्याएँ
{{व्याख्या}} साँचों में हैं और यहाँ नहीं ली जातीं। ID कहाँ से: केवल गवाह के इन चिह्नों से। कोई ID अनुमान से नहीं।
'उवाच' वाली पंक्तियाँ (जैसे सञ्जय उवाच) गवाह में श्लोक के खंड के भीतर हैं; वे उसी श्लोक के पाठ के साथ रहती हैं।

नतीजा: audit/witness/gita_ws_parse_v0.json — हर अध्याय की गिनती, छूटे या दोहरे क्रमांक, और हर श्लोक की कुंजी का hash।
पाठ या उसके अंश रिपोर्ट में नहीं जाते।

यह lock नहीं है। प्रदर्शन-पाठ के लिए सार्वजनिक-डोमेन छपा संस्करण (catalog/_base_editions.json के उम्मीदवार) बाक़ी है,
और 700-श्लोक वाले प्रचलित पाठ से इस गवाह की गिनती का मिलान भी (अध्याय 13 में 34 बनाम 35 श्लोक का प्रसिद्ध भेद)।
"""
from __future__ import annotations

import argparse
import datetime as dt
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
CACHE = REPO / ".cache" / "witness" / "gita"
UA = "sanatan-granth-catalog/0.1 (open library project; github sanatan-granth)"
# केवल वे अध्याय जिनका पन्ना खोलकर जाँचा गया है (17 नवंबर 2026)। बाक़ी नाम जाँचकर ही जोड़े जाएँ।
PAGES = {1: "भगवद्गीता/अर्जुनविषादयोगः", 2: "भगवद्गीता/साङ्ख्ययोगः"}
DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
HEADING = re.compile(r"अथ श्रीमद्भगवद्गीता|(अथ )?\S*ऽध्यायः")   # अध्याय का शीर्षक, एक या दो पंक्तियों में
SPEAKER = re.compile(r"(धृतराष्ट्र उवाच|सञ्जय उवाच|संजय उवाच|अर्जुन उवाच|श्रीभगवानुवाच) ")
MARK = re.compile(r"॥\s*([०-९0-9]+)\s*[-–]\s*([०-९0-9]+)\s*॥")


def fetch(chapters: list[int]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for ch in chapters:
        params = dict(action="query", prop="revisions", rvprop="content|ids|timestamp", rvslots="main", titles=PAGES[ch], format="json", formatversion="2")
        req = urllib.request.Request("https://sa.wikisource.org/w/api.php?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
        (CACHE / f"sa_ws_gita_{ch}.json").write_bytes(urllib.request.urlopen(req, timeout=90).read())


def load(ch: int) -> tuple[dict, str]:
    rev = json.loads((CACHE / f"sa_ws_gita_{ch}.json").read_bytes())["query"]["pages"][0]["revisions"][0]
    text = unicodedata.normalize("NFC", rev["slots"]["main"]["content"])
    meta = {"witness_id": f"sa-ws-gita-{ch}", "host": "sa.wikisource.org", "title": PAGES[ch], "revid": rev["revid"], "timestamp": rev["timestamp"],
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "licence": "CC-BY-SA-4.0", "usage": "compare"}
    return meta, text


def parse(ch: int, text: str) -> tuple[dict[int, str], dict]:
    """{श्लोक-क्रमांक: पाठ} और विभाजन की समस्याएँ। केवल <poem> खंड; क्रमांक गवाह के चिह्न से।"""
    out: dict[int, str] = {}
    problems: dict = {"unmarked_blocks": 0, "multi_marked_blocks": 0, "other_chapter_marks": [], "duplicates": []}
    for block in re.findall(r"<poem>(.*?)</poem>", text, flags=re.S):
        marks = MARK.findall(block)
        if not marks:
            problems["unmarked_blocks"] += 1  # मंगलाचरण या पुष्पिका ("ॐ तत्सदिति ..."): श्लोक नहीं
            continue
        if len(marks) > 1:
            problems["multi_marked_blocks"] += 1
            continue
        c, n = (int(x.translate(DEVA_DIGITS)) for x in marks[0])
        if c != ch:
            problems["other_chapter_marks"].append(f"{c}.{n}")
            continue
        if n in out:
            problems["duplicates"].append(n)
            continue
        body = MARK.sub("", block)
        body = re.sub(r"'''(.*?)'''", r"\1", body)          # मोटे अक्षर का चिह्न हटे, शब्द रहें
        body = re.sub(r"<[^>]+>", " ", body)
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        # अध्याय के पहले खंड का मंगलाचरण और शीर्षक ("अथ ... प्रथमोऽध्यायः") श्लोक के अंग नहीं
        lines = [ln for ln in lines if ln not in ("ॐ", "श्रीपरमात्मने नमः") and not HEADING.fullmatch(ln)]
        out[n] = re.sub(r"\s+", " ", " ".join(lines)).strip()
    top = max(out) if out else 0
    problems["missing"] = sorted(set(range(1, top + 1)) - set(out))
    return out, problems


def segments(chapters: list[int]) -> tuple[dict[str, str], list[dict]]:
    """कड़ी के लिए: {'gita:1.1': पाठ, ...} और गवाहों का विवरण।"""
    segs: dict[str, str] = {}
    metas = []
    for ch in chapters:
        meta, text = load(ch)
        verses, problems = parse(ch, text)
        if problems["missing"] or problems["duplicates"] or problems["multi_marked_blocks"] or problems["other_chapter_marks"]:
            raise SystemExit(f"गीता अध्याय {ch}: गवाह का विभाजन साफ़ नहीं: {problems}")
        segs.update({f"gita:{ch}.{n}": verses[n] for n in sorted(verses)})
        metas.append(meta)
    return segs, metas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--chapters", default="1,2")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    chapters = [int(x) for x in a.chapters.split(",") if x.strip()]
    unknown = [c for c in chapters if c not in PAGES]
    if unknown:
        raise SystemExit(f"इन अध्यायों का पन्ना अभी जाँचा नहीं गया: {unknown}")
    if a.fetch or not all((CACHE / f"sa_ws_gita_{c}.json").exists() for c in chapters):
        fetch(chapters)
    rows = []
    for ch in chapters:
        meta, text = load(ch)
        verses, problems = parse(ch, text)
        rows.append({"chapter": ch, "witness": meta, "segment_count": len(verses), "first": min(verses) if verses else None, "last": max(verses) if verses else None,
                     "problems": problems,
                     "segments": [{"segment": f"gita:{ch}.{n}", "key_sha256": hashlib.sha256(key(verses[n]).encode()).hexdigest(), "key_len": len(key(verses[n])),
                                   "has_speaker_line": bool(SPEAKER.match(verses[n]))} for n in sorted(verses)]})
    rep = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "text_id": "gita", "tool": "tools/witness/gita_collate.py v0",
           "key": "tools/witness/key.py", "id_source": "गवाह के ॥ अध्याय-श्लोक ॥ चिह्न", "chapters": rows,
           "limits": ["यह text-lock नहीं है", "एक ही गवाह (संस्कृत विकिस्रोत): स्वतंत्र दूसरा गवाह और छपा सार्वजनिक-डोमेन संस्करण बाक़ी",
                      "केवल वे अध्याय जिनके पन्ने जाँचे गए", "'उवाच' की पंक्तियाँ गवाह में जहाँ हैं वहीं ली गई हैं; गवाह में कुछ छूटी भी हो सकती हैं", "रिपोर्ट में पाठ नहीं, केवल गिनतियाँ और hash"]}
    out = REPO / "audit" / "witness" / "gita_ws_parse_v0.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps([{"chapter": r["chapter"], "segment_count": r["segment_count"], "first": r["first"], "last": r["last"], "problems": r["problems"],
                       "speaker_lines": sum(1 for s in r["segments"] if s["has_speaker_line"])} for r in rows], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
