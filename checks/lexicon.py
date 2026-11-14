"""lint-शब्दसूचियाँ। ये code हैं, डेटा नहीं: बदलाव PR और मालिक की स्वीकृति से।

R4/A9 = निषिद्ध दावे; R5 = देवता-प्रथम-पुरुष; D-जाँचों की सूचियाँ d_checks.py में।
"""
from __future__ import annotations

import re

# --- R3/R4: AI-output पर कभी नहीं (मास्टर योजना §3.7) ---
VERIFIED_WORDS = [
    r"सत्यापित", r"प्रमाणित", r"त्रुटि[-\s]?रहित", r"100\s*%\s*शुद्ध", r"शत[-\s]?प्रतिशत\s+शुद्ध",
    r"\bverified\b", r"\bcertified\b", r"\berror[-\s]?free\b", r"\b100\s*%\s*(accurate|pure|correct)\b",
    r"\bauthenticated\b", r"\bscholar[-\s]?(verified|approved)\b",
]

# --- R4/A9: निषिद्ध दावे (हर AI-परत पर, अनुवाद सहित) ---
FORBIDDEN_CLAIMS = [
    r"वैज्ञानिक\s+रूप\s+से\s+(सिद्ध|प्रमाणित)", r"विज्ञान\s+ने\s+(माना|सिद्ध\s+किया)", r"NASA\s+ने\s+माना",
    r"नासा\s+ने\s+(माना|स्वीकार)", r"\bscientifically\s+prov(en|ed)\b", r"\bNASA\s+(confirm|admit|prov)\w*",
    r"\bcures?\b", r"रोग\s+(ठीक|दूर)\s+(करता|करती|कर\s+देता)", r"(कैंसर|मधुमेह|डायबिटीज़?)\s+का\s+इलाज",
    r"\bguaranteed\b", r"सबसे\s+बड़ा\s+पुस्तकालय", r"\bworld'?s\s+largest\b", r"\bmyth(s|ology|ical)?\b", r"मिथक",
]

# --- R5: AI का देवता/गुरु बनकर प्रथम पुरुष में बोलना ---
_DEITY_HI = r"(कृष्ण|श्रीकृष्ण|शिव|शंकर|महादेव|विष्णु|नारायण|राम|श्रीराम|हनुमान|देवी|दुर्गा|काली|लक्ष्मी|सरस्वती|गणेश|ब्रह्मा|भगवान|ईश्वर|परमात्मा|तुम्हारा\s+(ईश्वर|भगवान|गुरु))"
_DEITY_EN = r"(Krishna|Shiva|Vishnu|Narayana|Rama|Hanuman|Devi|Durga|Kali|Lakshmi|Saraswati|Ganesha|Brahma|God|the\s+Lord|your\s+(Lord|God|guru))"
DEITY_FIRST_PERSON = [
    rf"मैं\s+(ही\s+)?(स्वयं\s+)?{_DEITY_HI}\s+(हूँ|हूं)",
    rf"मैं,?\s+{_DEITY_HI},?\s+(तुम(से|को|्हें)|आप(से|को))",
    rf"{_DEITY_HI}\s+के\s+रूप\s+में\s+मैं",
    rf"\bI\s+am\s+(Lord\s+)?{_DEITY_EN}\b",
    rf"\bI,\s+(Lord\s+)?{_DEITY_EN},",
    rf"\b[Aa]s\s+(Lord\s+)?{_DEITY_EN},?\s+I\b",
    r"मेरे\s+भक्त(ो|ों)?,?\s+मैं\s+तुम(से|्हें)",
    r"\b[Mm]y\s+devotees?,\s+I\b",
]

# --- R13: निजता ---
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_OK = re.compile(r"(noreply@anthropic\.com|@users\.noreply\.github\.com|@example\.(com|org)|git@github\.com|@v\d|@cloudflare/|@types/)")


def compile_all(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


RE_VERIFIED = compile_all(VERIFIED_WORDS)
RE_CLAIMS = compile_all(FORBIDDEN_CLAIMS)
RE_DEITY = compile_all(DEITY_FIRST_PERSON)
