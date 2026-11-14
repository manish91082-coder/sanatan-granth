"""P1 क़दम 1.1: बीज-सूचियाँ, हर पंक्ति पर मूल-श्लोक का हवाला और मशीन-मिलान।

    python tools/catalog/build_seeds.py --fetch      # स्रोत लाकर (.cache/seed_sources/) सूचियाँ बनाए
    python tools/catalog/build_seeds.py              # पहले से लाए स्रोतों पर

क्या करता है:
  1. तीन मूल अंश संस्कृत विकिस्रोत से लाता है (केवल मिलान के लिए; पाठ git में नहीं जाता):
       मुक्तिकोपनिषत् 1.30–39 · विष्णुपुराण 3.6.20–24, 3.6.28–29 · भागवत 12.7.23–24
  2. नीचे लिखी सूचियों (शीर्षक इंसान/Claude के लिखे, पाठ नहीं) के हर नाम का अंश उसी क्रम में
     श्लोकों में खोजता है। जो न मिले, उस पर 'variant'/'not_found' लिखता है; कुछ छिपाता नहीं।
  3. मुक्तिका के लिए दूसरा, स्वतंत्र स्रोत (English Wikipedia की तालिका) मिलाकर वेद और वर्ग जोड़ता है।
  4. catalog/seed/*.csv और catalog/seed/_sources.json (revid, sha256, लाइसेंस) लिखता है।

सीमा: विकिस्रोत के ये पन्ने टंकित e-text हैं, छपे संस्करण नहीं; इनमें टंकण-भूलें हैं (नीचे दर्ज)। यह मिलान
"सूची का नाम इस गवाह के श्लोक में इसी क्रम में मिला" भर कहता है। विद्वत्-समीक्षा बाक़ी है।
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / ".cache" / "seed_sources"
OUT = REPO / "catalog" / "seed"
UA = "sanatan-granth-catalog/0.1 (open library project; github sanatan-granth)"

SOURCES = {
    "muktika_sa": ("sa.wikisource.org", "मुक्तिकोपनिषत्"),
    "vp_3_6": ("sa.wikisource.org", "विष्णुपुराणम्/तृतीयांशः/अध्यायः ६"),
    "bhp_12_7": ("sa.wikisource.org", "श्रीमद्भागवतपुराणम्/स्कन्धः १२/अध्यायः ७"),
    "muktika_enwiki": ("en.wikipedia.org", "Muktikā"),
}
WIKI_LICENCE = "CC-BY-SA-4.0"  # compare_only: इन पन्नों का पाठ repo में नहीं आता


def fetch_all() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for key, (host, title) in SOURCES.items():
        params = dict(action="query", prop="revisions", rvprop="content|ids|timestamp", rvslots="main",
                      titles=title, format="json", formatversion="2")
        req = urllib.request.Request(f"https://{host}/w/api.php?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
        (CACHE / f"{key}.json").write_bytes(urllib.request.urlopen(req, timeout=60).read())


def load(key: str) -> dict:
    host, title = SOURCES[key]
    raw = (CACHE / f"{key}.json").read_bytes()
    rev = json.loads(raw)["query"]["pages"][0]["revisions"][0]
    text = unicodedata.normalize("NFC", rev["slots"]["main"]["content"])
    return {"key": key, "host": host, "title": title, "revid": rev["revid"], "timestamp": rev["timestamp"],
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "bytes": len(text.encode("utf-8")),
            "licence": WIKI_LICENCE, "usage": "compare", "text": text}


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    j = text.find(end, i + 1)
    if i < 0 or j < 0:
        raise SystemExit(f"स्रोत में अंश नहीं मिला: {start!r} … {end!r}")
    return text[i:j]


def ordered_find(block: str, stems: list[str | None]) -> list[str]:
    """हर stem को पिछले मिलान के बाद खोजे। 'found' / 'not_found' / 'no_stem'।"""
    pos, out = 0, []
    for st in stems:
        if st is None:
            out.append("no_stem")
            continue
        k = block.find(st, pos)
        if k < 0:
            out.append("not_found")
        else:
            out.append("found")
            pos = k + len(st)
    return out


# ------------------------------------------------------------------ 14/18 विद्याएँ (विष्णुपुराण 3.6.28–29)
VIDYA = [
    # (क्रम, समूह, नाम, taxonomy l1, श्लोक, श्लोक में अंश)
    (1, "वेद", "ऋग्वेद", "veda", "3.6.28", "वेदा"), (2, "वेद", "यजुर्वेद", "veda", "3.6.28", None),
    (3, "वेद", "सामवेद", "veda", "3.6.28", None), (4, "वेद", "अथर्ववेद", "veda", "3.6.28", None),
    (5, "वेदांग", "शिक्षा", "vedanga", "3.6.28", "गानि"), (6, "वेदांग", "कल्प", "vedanga", "3.6.28", None),
    (7, "वेदांग", "व्याकरण", "vedanga", "3.6.28", None), (8, "वेदांग", "निरुक्त", "vedanga", "3.6.28", None),
    (9, "वेदांग", "छन्द", "vedanga", "3.6.28", None), (10, "वेदांग", "ज्योतिष", "vedanga", "3.6.28", None),
    (11, "विद्यास्थान", "मीमांसा", "mimamsa", "3.6.28", "मीमांसा"), (12, "विद्यास्थान", "न्याय", "nyaya", "3.6.28", "न्यायविस्तर"),
    (13, "विद्यास्थान", "पुराण", "purana", "3.6.28", "पुराण"), (14, "विद्यास्थान", "धर्मशास्त्र", "dharmashastra", "3.6.28", "धर्मशास्त्र"),
    (15, "उपवेद", "आयुर्वेद", "ayurveda", "3.6.29", "आयुर्वेद"), (16, "उपवेद", "धनुर्वेद", "dhanurveda", "3.6.29", "धनुर्वेद"),
    (17, "उपवेद", "गान्धर्ववेद", "gandharvaveda", "3.6.29", "गान्धर्व"), (18, "उपवेद", "अर्थशास्त्र", "arthashastra", "3.6.29", "अर्थशास्त्र"),
]
# श्लोक केवल "अङ्गानि" (छह) और "चतुरो वेदाः" (चार) कहता है; उनके अलग-अलग नाम इस श्लोक में नहीं हैं।
VIDYA_NOTE_UNNAMED = "श्लोक समूह का नाम देता है (चार वेद / छह अंग); अलग-अलग नाम इस श्लोक में नहीं, दूसरे स्रोत से मिलाना बाक़ी"

# ------------------------------------------------------------------ 18 महापुराण (विष्णुपुराण 3.6.20–24; भागवत 12.7.23–24)
MAHAPURANA = [
    # (VP क्रम, work_id, नाम, VP अंश, भागवत अंश)
    (1, "pur.maha.brahma", "ब्रह्मपुराण", "ब्राह्मं", "ब्राह्मं"), (2, "pur.maha.padma", "पद्मपुराण", "पाद्मं", "पाद्मं"),
    (3, "pur.maha.vishnu", "विष्णुपुराण", "वैष्णव", "वैष्णवं"), (4, "pur.maha.shiva", "शिवपुराण", "शैवं", "शैवं"),
    (5, "pur.maha.bhagavata", "भागवतपुराण", "भागवतं", "भागवतं"), (6, "pur.maha.narada", "नारदपुराण", "नारदीय", "नारदीयं"),
    (7, "pur.maha.markandeya", "मार्कण्डेयपुराण", "मार्कण्डेय", "मार्कण्डेयं"), (8, "pur.maha.agni", "अग्निपुराण", "आग्नेय", "आग्नेयं"),
    (9, "pur.maha.bhavishya", "भविष्यपुराण", "भविष्यं", "भविष्यं"), (10, "pur.maha.brahmavaivarta", "ब्रह्मवैवर्तपुराण", "ब्रह्मवैवर्तं", "ब्रह्मवैवर्तं"),
    (11, "pur.maha.linga", "लिङ्गपुराण", "लैङ्ग", "लैङ्"), (12, "pur.maha.varaha", "वराहपुराण", "वाराहं", "वाराहं"),
    (13, "pur.maha.skanda", "स्कन्दपुराण", "स्कान्द", "स्कान्द"), (14, "pur.maha.vamana", "वामनपुराण", "वामन", "वामन"),
    (15, "pur.maha.kurma", "कूर्मपुराण", "कौर्मं", "कौर्मं"), (16, "pur.maha.matsya", "मत्स्यपुराण", "मात्स्य", "मात्स्यं"),
    (17, "pur.maha.garuda", "गरुडपुराण", "गारु", "गारुडं"), (18, "pur.maha.brahmanda", "ब्रह्माण्डपुराण", "ब्रह्माण्ड", "ब्रह्माण्ड"),
]

# ------------------------------------------------------------------ मुक्तिका की 108 उपनिषदें (मुक्तिकोपनिषत् 1.30–39)
# (देवनागरी शीर्षक, IAST, श्लोक, श्लोक में अंश, Wikipedia-नाम जहाँ वर्तनी बहुत अलग है)
M = [
    ("ईश", "Īśa", 30, "ईश", None), ("केन", "Kena", 30, "केन", None), ("कठ", "Kaṭha", 30, "कठ", None),
    ("प्रश्न", "Praśna", 30, "प्रश्न", None), ("मुण्डक", "Muṇḍaka", 30, "मुण्ड", None), ("माण्डूक्य", "Māṇḍūkya", 30, "माण्डूक्य", None),
    ("तैत्तिरीय", "Taittirīya", 30, "तित्तिरि", None), ("ऐतरेय", "Aitareya", 30, "ऐतरेय", None),
    ("छान्दोग्य", "Chāndogya", 30, "न्दोग्य", None), ("बृहदारण्यक", "Bṛhadāraṇyaka", 30, "बृहदारण्यक", None),
    ("ब्रह्म", "Brahma", 31, "ब्रह्म", None), ("कैवल्य", "Kaivalya", 31, "कैवल्य", None), ("जाबाल", "Jābāla", 31, "जाबाल", None),
    ("श्वेताश्वतर", "Śvetāśvatara", 31, "श्वेताश्व", None), ("हंस", "Haṃsa", 31, "हंस", None), ("आरुणिक", "Āruṇika", 31, "आरुणि", "Āruṇeya"),
    ("गर्भ", "Garbha", 31, "गर्भ", None), ("नारायण", "Nārāyaṇa", 31, "नारायण", None), ("परमहंस", "Paramahaṃsa", 31, "हंस", None),
    ("अमृतबिन्दु", "Amṛtabindu", 31, "बिन्दु", None), ("अमृतनाद", "Amṛtanāda", 31, "नाद", None),
    ("अथर्वशिरस्", "Atharvaśiras", 31, "शिर", None), ("अथर्वशिखा", "Atharvaśikhā", 31, "शिखा", None),
    ("मैत्रायणी", "Maitrāyaṇī", 32, "मैत्रायणी", None), ("कौषीतकि", "Kauṣītaki", 32, "कौषीतकी", None),
    ("बृहज्जाबाल", "Bṛhajjābāla", 32, "बृहज्जाबाल", None), ("नृसिंहतापनी", "Nṛsiṃhatāpanī", 32, "तापनी", None),
    ("कालाग्निरुद्र", "Kālāgnirudra", 32, "कालाग्निरुद्र", None), ("मैत्रेयी", "Maitreyī", 32, "मैत्रेयी", "Maitreya"),
    ("सुबाल", "Subāla", 32, "सुबाल", None), ("क्षुरिका", "Kṣurikā", 32, "क्षुरि", None), ("मन्त्रिका", "Mantrikā", 32, "मन्त्रिका", None),
    ("सर्वसार", "Sarvasāra", 33, "सर्वसार", None), ("निरालम्ब", "Nirālamba", 33, "निरालम्ब", None),
    ("शुकरहस्य", "Śukarahasya", 33, "रहस्य", None), ("वज्रसूचिका", "Vajrasūcikā", 33, "वज्रसूचिक", "Vajrasūchi"),
    ("तेजोबिन्दु", "Tejobindu", 33, "तेजो", None), ("नादबिन्दु", "Nādabindu", 33, "नाद", None),
    ("ध्यानबिन्दु", "Dhyānabindu", 33, "ध्यान", None), ("ब्रह्मविद्या", "Brahmavidyā", 33, "विद्या", None),
    ("योगतत्त्व", "Yogatattva", 33, "योगतत्त्व", None), ("आत्मबोध", "Ātmabodha", 33, "त्मबोध", None),
    ("नारदपरिव्राजक", "Nāradaparivrājaka", 34, "परिव्राट्", None), ("त्रिशिखिब्राह्मण", "Triśikhibrāhmaṇa", 34, "त्रिशिखी", "Triśikhi"),
    ("सीता", "Sītā", 34, "सीता", None), ("योगचूडामणि", "Yogacūḍāmaṇi", 34, "चूडा", None), ("निर्वाण", "Nirvāṇa", 34, "निर्वाण", None),
    ("मण्डलब्राह्मण", "Maṇḍalabrāhmaṇa", 34, "मण्डल", None), ("दक्षिणामूर्ति", "Dakṣiṇāmūrti", 34, "दक्षिणा", None),
    ("शरभ", "Śarabha", 34, "शरभ", None), ("स्कन्द", "Skanda", 34, "स्कन्द", None),
    ("त्रिपाद्विभूतिमहानारायण", "Tripādvibhūtimahānārāyaṇa", 34, "महानारायण", "Mahānārāyaṇa"),
    ("अद्वयतारक", "Advayatāraka", 34, "द्वय", None),
    ("रामरहस्य", "Rāmarahasya", 35, "रहस्य", None), ("रामतापनी", "Rāmatāpanī", 35, "रामतपन", None),
    ("वासुदेव", "Vāsudeva", 35, "वासुदेव", None), ("मुद्गल", "Mudgala", 35, "मुद्गल", None), ("शाण्डिल्य", "Śāṇḍilya", 35, "शाण्डिल्य", None),
    ("पैङ्गल", "Paiṅgala", 35, "पैङ्गल", None), ("भिक्षुक", "Bhikṣuka", 35, "भिक्षु", None), ("महा", "Mahā", 35, "मह", "Maha"),
    ("शारीरक", "Śārīraka", 35, "छारीरक", None), ("योगशिखा", "Yogaśikhā", 35, "शिखा", None),
    ("तुरीयातीत", "Turīyātīta", 36, "तुरीयातीत", None), ("संन्यास", "Saṃnyāsa", 36, "संन्यास", "Sannyāsa"),
    ("परमहंसपरिव्राजक", "Paramahaṃsaparivrājaka", 36, "परिव्राज", "Paramahaṃsa parivrājaka"),
    ("अक्षमालिका", "Akṣamālikā", 36, "क्षमालिका", "Akṣamālika"), ("अव्यक्त", "Avyakta", 36, "अव्यक्त", None),
    ("एकाक्षर", "Ekākṣara", 36, "काक्षर", None), ("अन्नपूर्णा", "Annapūrṇā", 36, "पूर्णा", None), ("सूर्य", "Sūrya", 36, "सूर्य", None),
    ("अक्षि", "Akṣi", 36, "क्ष्य", None), ("अध्यात्म", "Adhyātma", 36, "ध्यात्म", None), ("कुण्डिका", "Kuṇḍikā", 36, "कुण्डिका", None),
    ("सावित्री", "Sāvitrī", 37, "सावित्र", None), ("आत्मा", "Ātmā", 37, "त्मा", None),
    ("पाशुपतब्रह्म", "Pāśupatabrahma", 37, "पाशुपत", "Pāśupata"), ("परब्रह्म", "Parabrahma", 37, "परं ब्रह्म", None),
    ("अवधूत", "Avadhūta", 37, "वधूतक", None), ("त्रिपुरातापनी", "Tripurātāpanī", 37, "त्रिपुरातपन", "Tripurātapini"),
    ("देवी", "Devī", 37, "देवी", None), ("त्रिपुरा", "Tripurā", 37, "त्रिपुरा", "Tripura"), ("कठरुद्र", "Kaṭharudra", 37, "कठ", None),
    ("भावना", "Bhāvanā", 37, "भावना", None), ("रुद्रहृदय", "Rudrahṛdaya", 37, "हृदय", None),
    ("योगकुण्डलिनी", "Yogakuṇḍalinī", 37, "कुण्डली", None), ("भस्मजाबाल", "Bhasmajābāla", 37, "भस्म", "Bhasma"),
    ("रुद्राक्षजाबाल", "Rudrākṣajābāla", 37, "रुद्राक्ष", "Rudrākṣa"), ("गणपति", "Gaṇapati", 37, "गण", None),
    ("जाबालदर्शन", "Jābāladarśana", 37, "दर्शन", "Darśana"),
    ("तारसार", "Tārasāra", 38, "तारसार", None), ("महावाक्य", "Mahāvākya", 38, "महावाक्य", None), ("पञ्चब्रह्म", "Pañcabrahma", 38, "पञ्चब्रह्म", None),
    ("प्राणाग्निहोत्र", "Prāṇāgnihotra", 38, "ग्निहोत्र", None), ("गोपालतापनी", "Gopālatāpanī", 38, "गोपालतपन", None),
    ("कृष्ण", "Kṛṣṇa", 38, "कृष्ण", None), ("याज्ञवल्क्य", "Yājñavalkya", 38, "याज्ञवल्क्य", None), ("वराह", "Varāha", 38, "वराह", None),
    ("शाट्यायनीय", "Śāṭyāyanīya", 39, "शाट्यायनी", None), ("हयग्रीव", "Hayagrīva", 39, "हयग्रीव", None),
    ("दत्तात्रेय", "Dattātreya", 39, "दत्तात्रेय", None), ("गरुड", "Garuḍa", 39, "गारुड", None),
    ("कलिसंतरण", "Kalisaṃtaraṇa", 39, "कलि", "Kali-Saṇṭāraṇa"), ("जाबालि", "Jābāli", 39, "जाबालि", None),
    ("सौभाग्यलक्ष्मी", "Saubhāgyalakṣmī", 39, "सौभाग्य", None), ("सरस्वतीरहस्य", "Sarasvatīrahasya", 39, "रहस्य", None),
    ("बह्वृच", "Bahvṛca", 39, "ऋच", None), ("मुक्तिका", "Muktikā", 39, "मुक्तिका", None),
]
KNOWN_VARIANTS = {
    53: "इस गवाह में 1.34 का अंत 'महानारायणाह्वयम्' है; छपे पाठों में 'महानारायणाद्वयम्' बताया जाता है (अद्वय = अद्वयतारक) [अपुष्ट; छपे संस्करण से मिलाना बाक़ी]",
    9: "इस गवाह में 'च्हान्दोग्यं' टंकित है (छान्दोग्यं की टंकण-भूल)",
}


def fold(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()
    s = s.replace("ch", "c").replace("sh", "s").replace("ṃ", "m")
    return re.sub(r"[^a-z]", "", s)


def parse_enwiki(text: str) -> list[dict]:
    tab = text[text.find("{|"): text.find("\n|}", text.find("{|"))]
    vedas = ["शुक्ल यजुर्वेद", "कृष्ण यजुर्वेद", "अथर्ववेद", "सामवेद", "ऋग्वेद"]

    def clean(x: str) -> str:
        x = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", x, flags=re.S)
        x = re.sub(r"\{\{IAST\|([^}]*)\}\}", r"\1", x)
        x = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", x)
        return x.replace("&nbsp;", " ").strip()

    out = []
    for row in tab.split("\n|-")[2:]:
        cells = re.split(r"\n\|(?!-)", row)
        cat = re.split(r"[;{<\n]", clean(cells[1]))[0].strip()
        for veda, cell in zip(vedas, cells[2:]):
            for nm in re.split(r"<br\s*/?>", cell):
                nm = re.sub(r"\s*\(.*?\)", "", clean(nm)).strip()
                if nm:
                    out.append({"name": nm, "veda": veda, "category": cat})
    return out


def match_enwiki(wp: list[dict]) -> dict[int, dict]:
    cand = []
    for i, (_, iast, _, _, alias) in enumerate(M, 1):
        for j, w in enumerate(wp):
            a, b = fold(alias or iast), fold(w["name"])
            sc = 1.0 if a == b else difflib.SequenceMatcher(None, fold(iast), b).ratio()
            if sc >= 0.84:
                cand.append((sc, i, j))
    used_i, used_j, res = set(), set(), {}
    for sc, i, j in sorted(cand, reverse=True):
        if i in used_i or j in used_j:
            continue
        used_i.add(i); used_j.add(j)
        res[i] = dict(wp[j], score=round(sc, 2))
    return res


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if a.fetch or not all((CACHE / f"{k}.json").exists() for k in SOURCES):
        fetch_all()
    src = {k: load(k) for k in SOURCES}
    report: dict = {}

    def ref(k: str) -> str:
        return f"{src[k]['host']} · {src[k]['title']} · revid {src[k]['revid']}"

    # --- विद्याएँ
    vp = src["vp_3_6"]["text"]
    blk = between(vp, "२७ ।।", "ज्ञेया")
    # श्लोक में 'अङ्गानि' 'वेदाः' से पहले आता है, और हमारी सूची का क्रम परंपरागत है: यहाँ केवल उपस्थिति देखी जाती है
    st = ["no_stem" if v[5] is None else ("found" if v[5] in blk else "not_found") for v in VIDYA]
    rows = []
    for v, s in zip(VIDYA, st):
        note = VIDYA_NOTE_UNNAMED if s == "no_stem" else ("श्लोक में केवल समूह-शब्द मिला (चतुरो वेदाः / अङ्गानि); यह नाम अलग से नहीं" if v[0] in (1, 5) else "")
        rows.append([v[0], v[1], v[2], v[3], f"विष्णुपुराण {v[4]}", s, ref("vp_3_6"), note])
    write_csv("vidya_18.csv", ["rank", "group", "name", "taxonomy_l1", "primary_ref", "primary_stem", "primary_witness", "note"], rows)
    report["vidya_18"] = {"rows": len(rows), "found": st.count("found"), "group_only": st.count("no_stem"), "not_found": st.count("not_found"),
                          "count_words": {"चतुर्दश": "चतुर्दश" in blk, "ष्टादश": "ष्टादश" in blk}}

    # --- महापुराण
    blk_vp = between(vp, "१९ ।।", "२४ ।।")
    blk_bh = between(src["bhp_12_7"]["text"], "२२ ॥", "२५ ॥")
    st_vp = ordered_find(blk_vp, [p[3] for p in MAHAPURANA])
    st_bh = ["found" if p[4] in blk_bh else "not_found" for p in MAHAPURANA]  # भागवत का क्रम अलग है: केवल उपस्थिति
    rows = [[p[0], p[1], p[2], "विष्णुपुराण 3.6.20–23", s1, "भागवत 12.7.23–24", s2, 2 if s1 == s2 == "found" else 1,
             ref("vp_3_6"), ref("bhp_12_7"), ""] for p, s1, s2 in zip(MAHAPURANA, st_vp, st_bh)]
    rows[3][-1] = "दोनों गवाह यहाँ 'शैव' पढ़ते हैं; कुछ परंपरागत सूचियाँ इस जगह वायुपुराण गिनती हैं [अपुष्ट; दूसरी सूचियों से मिलाना बाक़ी]"
    write_csv("mahapurana_18.csv", ["rank_vp", "work_id", "name", "ref_1", "stem_1", "ref_2", "stem_2", "attestation_count", "witness_1", "witness_2", "note"], rows)
    report["mahapurana_18"] = {"rows": len(rows), "vp_found_in_order": st_vp.count("found"), "bhp_found": st_bh.count("found")}

    # --- मुक्तिका 108
    blk = between(src["muktika_sa"]["text"], "ईशकेन", "एवमष्टोत्तरशतं")
    st = ordered_find(blk, [m[3] for m in M])
    wp = parse_enwiki(src["muktika_enwiki"]["text"])
    mt = match_enwiki(wp)
    rows = []
    for i, (m, s) in enumerate(zip(M, st), 1):
        w = mt.get(i, {})
        note = KNOWN_VARIANTS.get(i, "")
        if s == "not_found" and i in KNOWN_VARIANTS:
            s = "variant"
        rows.append([i, f"veda.upanishad.{fold(m[1])}", m[0], m[1], f"मुक्तिकोपनिषत् 1.{m[2]}", s, ref("muktika_sa"),
                     w.get("name", ""), w.get("veda", ""), w.get("category", ""), "found" if w else "not_matched",
                     ref("muktika_enwiki"), (1 if s == "found" else 0) + (1 if w else 0), note])
    write_csv("muktika_108.csv", ["rank", "work_id", "title_devanagari", "title_iast", "primary_ref", "primary_stem", "primary_witness",
                                  "secondary_name", "veda_per_secondary", "category_per_secondary", "secondary_match", "secondary_witness",
                                  "attestation_count", "note"], rows)
    ids = [r[1] for r in rows]
    report["muktika_108"] = {"rows": len(rows), "primary_found_in_order": [r[5] for r in rows].count("found"),
                             "primary_variant": [r[0] for r in rows if r[5] == "variant"],
                             "primary_not_found": [r[0] for r in rows if r[5] == "not_found"],
                             "secondary_table_names": len(wp), "secondary_matched": len(mt),
                             "secondary_unmatched_ours": [r[3] for r in rows if r[10] != "found"],
                             "secondary_unmatched_theirs": sorted({w["name"] for w in wp} - {v["name"] for v in mt.values()}),
                             "duplicate_work_ids": sorted({x for x in ids if ids.count(x) > 1})}

    meta = {"_comment": "बीज-सूचियों के स्रोत। पाठ यहाँ नहीं रखा जाता; केवल पहचान। लाइसेंस CC BY-SA → केवल तुलना।",
            "sources": [{k: v for k, v in s.items() if k != "text"} for s in src.values()], "report": report}
    (OUT / "_sources.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
