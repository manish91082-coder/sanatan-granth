"""D1–D12 (v0): संस्कृत-अर्थ की पक्की जाँचें, एक श्लोक और उसके अनुवाद पर।

v0 में वही जाँचें चलती हैं जो बिना रूप-विश्लेषक के नियतात्मक हैं:
  D2 निषेध · D3 संख्या · D6 नाम/विशेषण · D7 उवाच-वक्ता · D8 शब्द-आधार (वर्जित रूप) · D11 ID (r_checks.a3_id_continuity)
बाक़ी (D1, D4, D5, D9, D10, D12) को रूप-विश्लेषक (Vidyut/ByT5/Heritage) और NLI चाहिए; वे 'not_run' लौटाती हैं
और pipeline_version की घोषणा में 'checks_not_run' में दर्ज रहती हैं। not_run कभी 'पास' नहीं गिना जाता।

ये जाँचें गंभीर, मशीन से पकड़ने-योग्य ग़लतियाँ पकड़ती हैं। बारीक अर्थ-भूल ये नहीं पकड़तीं।
पदच्छेद-परत (padaccheda) मिले तो उसी पर चलती हैं; न मिले तो मूल पाठ के शब्दों पर (संधि के कारण कम सटीक)।
"""
from __future__ import annotations

import re
from dataclasses import dataclass

NOT_RUN = ("D1", "D4", "D5", "D9", "D10", "D12")
IMPLEMENTED = ("D2", "D3", "D6", "D7", "D8")


@dataclass
class Flag:
    check: str
    veto: bool
    msg: str


def _tok_deva(s: str) -> list[str]:
    return [t for t in re.split(r"[\s।॥,;:!?\-–—\"'()\[\]०-९0-9.]+", s) if t]


def _has(rx: str, s: str) -> bool:
    return re.search(rx, s, re.IGNORECASE) is not None


# ------------------------------------------------------------------ D2 निषेध
# स्वतंत्र निषेध-निपात। अ-/अन्- उपसर्ग और संधि में घुला 'न' (नास्ति, नैनं) v0 में केवल पदच्छेद से पकड़े जाते हैं।
SA_NEG_STANDALONE = {"न", "मा", "नहि", "नैव", "नापि", "नच", "नतु", "नवा"}
# दो-अर्थी रूप: 'नो' प्रायः 'नः' (हमें/हमारा) का संधि-रूप है (गीता 1.33 काङ्क्षितं नो, 2.6 कतरन्नो), और 'ना' = नर।
# इन पर केवल संकेत (veto नहीं); पक्का फ़ैसला पदच्छेद-परत से।
SA_NEG_AMBIG = {"नो", "ना"}
SA_NEG_SANDHI_PREFIX = re.compile(r"^(नैन|नैत|नैव|नास्|नाह|नाय|नानु|नाभि|नाप|नात्|नेह|नेद|नोप|नोत्|मास्म)")
HI_NEG = r"(?<![\wऀ-ॿ])(नहीं|नही|न|ना|मत|बिना|कभी\s+नहीं|न\s+तो|नहिं)(?![\wऀ-ॿ])|रहित|अ(?:विनाशी|जन्मा|मर|चल|व्यक्त|नित्य|सत्)"
EN_NEG = r"\b(not|no|never|neither|nor|none|nothing|nobody|cannot|without|nowhere)\b|n't\b|\b(un|non)[a-z]{4,}|\b(im|in)(perishable|mortal|destructible|visible|capable|possible|mutable|action|active|finite|comprehensible|exhaustible|conceivable|auspicious|different|movable)\w*|\w{3,}less\b"


def d2_negation(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    toks = _tok_deva(padaccheda or sa)
    explicit = [t for t in toks if t in SA_NEG_STANDALONE]
    sandhi = [] if padaccheda else [t for t in toks if SA_NEG_SANDHI_PREFIX.match(t)]
    ambig = [t for t in toks if t in SA_NEG_AMBIG]
    tr_has = _has(HI_NEG if lang == "hi" else EN_NEG, tr)
    out = []
    if explicit and not tr_has:
        out.append(Flag("D2", True, f"संस्कृत में निषेध ({' '.join(explicit[:3])}) पर अनुवाद में कोई निषेध-शब्द नहीं"))
    elif (sandhi or ambig) and not explicit and not tr_has:
        t0 = (sandhi or ambig)[0]
        out.append(Flag("D2", False, f"संभावित निषेध ({t0}…) पर अनुवाद में निषेध नहीं (संकेत; दो-अर्थी या संधि-रूप, पदच्छेद से पक्का होगा)"))
    return out


# ------------------------------------------------------------------ D3 संख्याएँ
# (संस्कृत रूप का regex, मान, हिंदी रूप, अंग्रेज़ी रूप)। 'नव' (नया/नौ) और 'एक' (अकेला/एक) अस्पष्ट हैं: केवल संकेत।
NUMS = [
    (r"^(द्वौ|द्वे|द्वाभ्याम्|द्वयोः|द्वि\w*|उभौ|उभे|उभयोः)$", 2, r"दो|दोनों|द्वि|युगल|२|\b2\b", r"\b(two|both|twice|pair|twofold|2)\b", True),
    (r"^(त्रयः|त्रीणि|त्रीन्|तिस्रः|त्रिभिः|त्रिषु|त्रि\w+|त्रय\w*)$", 3, r"तीन|तीनों|त्रि|३|\b3\b", r"\b(three|thrice|triple|threefold|triad|3)\b", True),
    (r"^(चत्वारः|चत्वारि|चतुरः|चतस्रः|चतुर्भिः|चतुर्\w+|चतुः\w*)$", 4, r"चार|चारों|चतुर्|चतु|४|\b4\b", r"\b(four|fourfold|4)\b", True),
    (r"^(पञ्च|पञ्चभिः|पञ्चसु|पञ्चानाम्|पञ्च\w+)$", 5, r"पाँच|पांच|पाँचों|पंच|पञ्च|५|\b5\b", r"\b(five|fivefold|5)\b", True),
    (r"^(षट्|षड्\w*|षण्\w*|षड्भिः)$", 6, r"छह|छः|छ:|छहों|षट्|षड्|६|\b6\b", r"\b(six|sixfold|6)\b", True),
    (r"^(सप्त|सप्तभिः|सप्तसु|सप्तानाम्)$", 7, r"सात|सातों|सप्त|७|\b7\b", r"\b(seven|sevenfold|7)\b", True),
    (r"^(अष्ट|अष्टौ|अष्टभिः|अष्टधा)$", 8, r"आठ|आठों|अष्ट|८|\b8\b", r"\b(eight|eightfold|8)\b", True),
    (r"^(दश|दशभिः|दशसु)$", 10, r"दस|दसों|दश|१०|\b10\b", r"\b(ten|tenfold|10)\b", True),
    (r"^(शतम्|शतानि|शतैः|शतशः|शत)$", 100, r"सौ|सैकड़ों|शत|१००|\b100\b", r"\b(hundred|hundreds|100)\b", True),
    (r"^(सहस्रम्|सहस्राणि|सहस्रैः|सहस्रशः|सहस्र)$", 1000, r"हज़ार|हजार|हज़ारों|हजारों|सहस्र|१०००|\b1000\b", r"\b(thousand|thousands|1000|1,000)\b", True),
    (r"^(नव|नवभिः)$", 9, r"नौ|नव|नया|नये|नए|नई|नवीन|९|\b9\b", r"\b(nine|new|fresh|9)\b", False),
    (r"^(एकः|एकम्|एका|एकेन|एकस्मिन्|एक)$", 1, r"एक|अकेल|केवल|एकमात्र|अद्वितीय|१|\b1\b", r"\b(one|single|alone|only|sole|a|an|1)\b", False),
]


def d3_numbers(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    out = []
    seen = set()
    for t in _tok_deva(padaccheda or sa):
        for rx, val, hi, en, veto in NUMS:
            if val in seen or not re.match(rx, t):
                continue
            seen.add(val)
            if not _has(hi if lang == "hi" else en, tr):
                out.append(Flag("D3", veto, f"संस्कृत संख्या-शब्द '{t}' (={val}) का रूप अनुवाद में नहीं मिला"))
    return out


# ------------------------------------------------------------------ अंग्रेज़ी में नामों की वर्तनी
# अंग्रेज़ी अनुवाद IAST (Kṛṣṇa, Keśava) भी लिखते हैं और सादी वर्तनी (Krishna, Keshava, Hrishikesha, Varshneya) भी।
# पैटर्न IAST-वर्गों में लिखे हैं; _rom उन्हें सादी वर्तनी के रूप भी मानने वाला बनाता है।
_ROM = {"[sś]": "(?:sh|s|ś)", "[sṣ]": "(?:sh|s|ṣ)", "[rṛ]": "(?:ri|ru|r|ṛ)", "c[iī]": "ch?[iī]", "Acyuta": "Ach?yuta"}


def _rom(rx: str) -> str:
    for k, v in _ROM.items():
        rx = rx.replace(k, v)
    return rx


# ------------------------------------------------------------------ D6 नाम और विशेषण
# विशेषण → (हिंदी में स्वीकार्य रूप, अंग्रेज़ी में स्वीकार्य रूप)। अनुवाद में इनमें से कोई एक होना चाहिए।
EPITHETS = {
    "arjuna": (r"अर्जुन|पार्थ|कौन्तेय|कुन्ती\s*-?\s*(पुत्र|नन्दन)|कुंती\s*-?\s*(पुत्र|नंदन)|पृथा\s*-?\s*पुत्र|धनञ्जय|धनंजय|गुडाकेश|पाण्डव|पांडव|भारत|परन्तप|परंतप|महाबाहो|महाबाहु|कुरु(नन्दन|श्रेष्ठ|सत्तम)|भरत(श्रेष्ठ|र्षभ|वंशी)|सव्यसाची",
               r"Arjuna|P[aā]rtha|Kaunteya|son\s+of\s+(Kunt[iī]|P[rṛ]th[aā])|Dhana[nñ]jaya|Gu[dḍ][aā]ke[sś]a|P[aā][nṇ][dḍ]ava|Bh[aā]rata|Parantapa|mighty[- ]armed|scorcher\s+of\s+(foes|enemies)|(best|scion|descendant|joy|bull)\s+(of|among)\s+the\s+(Kurus?|Bharatas?)|Savyas[aā]c[iī]"),
    "krishna": (r"कृष्ण|केशव|माधव|गोविन्द|गोविंद|मधुसूदन|हृषीकेश|जनार्दन|वासुदेव|अच्युत|वार्ष्णेय|भगवान|श्रीभगवान|हरि|यादव|पुरुषोत्तम|केशिनिषूदन",
                r"K[rṛ][sṣ][nṇ]a|Ke[sś]ava|M[aā]dhava|Govinda|Madhus[uū]dana|H[rṛ][sṣ][iī]ke[sś]a|Jan[aā]rdana|V[aā]sudeva|Acyuta|Achyuta|V[aā]r[sṣ][nṇ]eya|Lord|Blessed\s+One|Hari|slayer\s+of\s+Madhu|Y[aā]dava|Puru[sṣ]ottama"),
}
EPITHET_FORMS = [
    (r"^(कौन्तेय|कौन्तेयः|कौन्तेयम्)$", "arjuna"), (r"^(पार्थ|पार्थः|पार्थम्|पार्थस्य|पार्थाय)$", "arjuna"),
    (r"^(गुडाकेश|गुडाकेशः|गुडाकेशेन)$", "arjuna"), (r"^(धनञ्जय|धनञ्जयः|धनंजय)$", "arjuna"),
    (r"^(अर्जुन|अर्जुनः|अर्जुनम्)$", "arjuna"), (r"^(परन्तप|परन्तपः)$", "arjuna"), (r"^(कुरुनन्दन|भरतर्षभ|भरतश्रेष्ठ|कुरुसत्तम|कुरुश्रेष्ठ)$", "arjuna"),
    (r"^(हृषीकेश|हृषीकेशः|हृषीकेशम्)$", "krishna"), (r"^(केशव|केशवः|केशवम्)$", "krishna"),
    (r"^(मधुसूदन|मधुसूदनः)$", "krishna"), (r"^(गोविन्द|गोविन्दः|गोविन्दम्)$", "krishna"),
    (r"^(जनार्दन|जनार्दनः)$", "krishna"), (r"^(माधव|माधवः)$", "krishna"), (r"^(अच्युत|अच्युतः)$", "krishna"),
    (r"^(वार्ष्णेय|वासुदेव|वासुदेवः|कृष्ण|कृष्णः|कृष्णम्)$", "krishna"),
]
EPITHETS = {k: (hi, _rom(en)) for k, (hi, en) in EPITHETS.items()}
# ग़लत व्यक्ति: विशेषण X का है, पर अनुवाद में केवल Y का नाम है
WRONG_PERSON = {"arjuna": ("krishna",), "krishna": ("arjuna",)}


def d6_names(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    out, done = [], set()
    idx = 0 if lang == "hi" else 1
    for t in _tok_deva(padaccheda or sa):
        for rx, who in EPITHET_FORMS:
            if who in done or not re.match(rx, t):
                continue
            done.add(who)
            if not _has(EPITHETS[who][idx], tr):
                out.append(Flag("D6", True, f"विशेषण/नाम '{t}' ({who}) का कोई स्वीकार्य रूप अनुवाद में नहीं"))
    return out


# ------------------------------------------------------------------ D7 उवाच-वक्ता
SPEAKERS = [
    (r"(श्री\s*भगवान्?\s*उवाच|श्रीभगवानुवाच|भगवानुवाच)", r"भगवान|श्रीभगवान|कृष्ण", r"Lord|Blessed|Bhagav[aā]n|K[rṛ][sṣ][nṇ]a|God"),
    (r"(अर्जुन\s+उवाच|अर्जुन\s*उवाच)", r"अर्जुन", r"Arjuna"),
    (r"(सञ्जय\s+उवाच|संजय\s+उवाच)", r"सञ्जय|संजय", r"Sa[nñṃ]jaya"),
    (r"(धृतराष्ट्र\s+उवाच)", r"धृतराष्ट्र", r"Dh[rṛ]tar[aā][sṣ][tṭ]ra|Dhritarashtra"),
]
SPEAKERS = [(rx, hi, _rom(en)) for rx, hi, en in SPEAKERS]
HI_SAID = r"कहा|बोले|बोला|कहते|उवाच|ने\s+पूछा|पूछा"
EN_SAID = r"\b(said|spoke|says|replied|asked|uv[aā]ca)\b"


def d7_speaker(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    out = []
    for rx, hi, en in SPEAKERS:
        if re.search(rx, sa):
            name_ok = _has(hi if lang == "hi" else en, tr)
            said_ok = _has(HI_SAID if lang == "hi" else EN_SAID, tr)
            if not name_ok:
                out.append(Flag("D7", True, "उवाच का वक्ता अनुवाद में नहीं या ग़लत"))
            elif not said_ok:
                out.append(Flag("D7", False, "वक्ता है पर 'कहा/said' जैसा शब्द नहीं (संकेत)"))
            # ग़लत वक्ता: दूसरे वक्ता का नाम 'कहा' के ठीक पहले
            for rx2, hi2, en2 in SPEAKERS:
                if rx2 == rx:
                    continue
                other = hi2 if lang == "hi" else en2
                said = HI_SAID if lang == "hi" else EN_SAID
                if not name_ok and re.search(rf"({other})\W{{0,12}}({said})", tr, re.IGNORECASE):
                    out.append(Flag("D7", True, "उवाच दूसरे वक्ता के नाम से जोड़ा गया"))
                    break
            break
    return out


# ------------------------------------------------------------------ D8 शब्द-आधार (वर्जित रूप)
FORBIDDEN_RENDERINGS = [
    (r"\bmyth(s|ology|ical)?\b|मिथक", "'myth/मिथक' वर्जित; 'पारंपरिक वृत्तांत' लिखें"),
    (r"\bidol(s|atry)?\b", "'idol' की जगह 'image/mūrti'"),
    (r"\bheathen|\bpagan", "औपनिवेशिक शब्द वर्जित"),
]


def d8_termbase(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    return [Flag("D8", True, msg) for rx, msg in FORBIDDEN_RENDERINGS if _has(rx, tr)]


CHECKS = [d2_negation, d3_numbers, d6_names, d7_speaker, d8_termbase]


def run_segment(sa: str, tr: str, lang: str, padaccheda: str | None = None) -> list[Flag]:
    """एक श्लोक पर v0 की सारी D-जाँचें। ख़ाली सूची = v0 की जाँचों में कोई आपत्ति नहीं (यह 'सही' का प्रमाण नहीं)।"""
    flags: list[Flag] = []
    if not tr or not tr.strip():
        return [Flag("D11", True, "अनुवाद ख़ाली")]
    for fn in CHECKS:
        flags.extend(fn(sa, tr, lang, padaccheda))
    return flags
