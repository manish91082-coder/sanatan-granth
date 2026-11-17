"""जज के लिए canary: नियम से बिगाड़ा गया अनुवाद (ठीक एक मोटी ग़लती), जिसका सही उत्तर हमें पता है।

दो जगह काम आता है:
  - tools/pilot/judge_test.py: जजों की योग्यता-परीक्षा (पूरा ग्रंथ)।
  - tools/pilot/run_e2e.py: हर run में जज की चलती जाँच (कुछ ही मंत्र), ताकि जज के बिगड़ने का पता उसी run में चले।

यह मोटी ग़लती पकड़ने की क्षमता नापता है; बारीक संस्कृत-अर्थ की समझ नहीं। यह मानव-समीक्षा नहीं है।
"""
from __future__ import annotations

import re

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


def pick(drafts: dict[str, dict], order: list[str], k: int) -> dict[str, dict]:
    """`order` में फैले हुए अधिकतम k मंत्र जिन पर कोई नियम लागू होता है: {id: बिगड़ी नक़ल}। चुनाव नियतात्मक है।"""
    if k <= 0:
        return {}
    usable: dict[str, dict] = {}
    for pos, i in enumerate(order):
        d = drafts.get(i)
        if not d:
            continue
        c = corrupt(pos + 1, d["en"], d["hi"])
        if c:
            usable[i] = c
    ids = list(usable)
    if len(ids) <= k:
        return usable
    step = len(ids) / k
    return {ids[int(j * step)]: usable[ids[int(j * step)]] for j in range(k)}
