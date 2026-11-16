"""P2 pilot: एक ग्रंथ पर पूरी कड़ी, शुरू से अंत तक (v0)।

    python -m tools.pilot.run_e2e --text isha --out <dir> [--mock] [--job-key <64hex>] [--batch-id <id>]

कड़ी (अगला क़दम code तय करता है; कोई agent दूसरे agent को नहीं चुनता):
  स्रोत/गवाह → संरेखक (ID केवल गवाह के चिह्नों से) → Draft A और Draft B (दो अलग परिवार) → जज (तीसरा/चौथा परिवार)
  → असहमति पर Draft C + दूसरा जज (cascade) → पक्की जाँचें (D2/D3/D6/D7/D8) → बैज C/D → परतों का पेड़ → R-जाँचें → रिपोर्ट

ईमानदारी की बातें:
  - LLM संस्कृत या श्लोक-ID नहीं लिखता। संस्कृत गवाह से आती है, ID गवाह के ॥ N ॥ चिह्नों से।
  - यह परीक्षण-run है। स्रोत अस्थायी है (मालिक का G1-फ़ैसला बाक़ी), पाठ lock नहीं है। इसलिए बना हुआ पेड़ repo में
    नहीं जाता, और उस पर R2 (lock) और R6 (लाइसेंस) का लाल होना अपेक्षित है। संस्कृत पाठ रिपोर्ट में नहीं जाता।
  - बैज केवल C या D। कोई त्रुटि-दर नहीं छपती।
"""
from __future__ import annotations

import argparse
import datetime as dt
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

from checks import d_checks  # noqa: E402
from checks.common import canonical_segments_hash  # noqa: E402
from checks.run_all import report as checks_report, run as checks_run  # noqa: E402
from tools.pilot.llm import Model, Usage, available, chat_json, parse_model  # noqa: E402

PIPELINE_VERSION = "pilot-e2e-0.4"
OK_LABELS = {"OK", "MINOR"}
LABELS = {"OK", "MINOR", "CONTRADICTED", "UNSURE"}
EXPECTED_RED = {"R2": "पाठ lock नहीं है (स्रोत का फ़ैसला बाक़ी)", "R6": "मूल-पाठ का वाहक गवाह CC BY-SA है; प्रदर्शन-योग्य स्रोत तय नहीं"}

TEXTS = {
    "isha": {
        "work_id": "upanishad.isha",
        "title": {"title_devanagari": "ईशावास्योपनिषद्", "title_iast": "Īśāvāsyopaniṣad", "title_hi": "ईशावास्य उपनिषद्", "title_en": "Isha Upanishad"},
        "base_edition": "ia-nsp-108-1925",  # अस्थायी: भारतीय संपादक वाला छपा संस्करण (मालिक का फ़ैसला बाक़ी)
        "carrier_witness": "sa-ws-isha",    # मशीन-पठनीय पाठ का वाहक (केवल तुलना-लाइसेंस; repo में नहीं जाता)
        "witnesses": ["ia-nsp-108-1925", "sa-ws-isha", "sa-ws-vsm40", "ia-roer-1850"],
        "citation_scheme": ["mantra"], "chapter": "1", "segment_count": 18, "genre": "upanishad",
    },
}

DRAFT_SYSTEM = (
    "You translate Sanskrit scripture segments faithfully into English and Hindi. Output JSON only, exactly: "
    '{"items":[{"id":"<id>","en":"<English>","hi":"<Hindi in Devanagari>"}]}. '
    "Rules: one item per given id and no other ids; never output the Sanskrit itself; no commentary, no headings, no notes; "
    "keep every negation, number, proper name and speaker exactly as in the Sanskrit; do not add ideas that are not in the text; "
    "prefer a literal rendering over an elegant one; never use the words myth, mythology or mythical."
)
JUDGE_SYSTEM = (
    "You are a strict judge of translation fidelity for Sanskrit scripture. For each id you receive the Sanskrit and two candidate "
    "translations, A and B, each with English (en) and Hindi (hi). Judge each candidate on its own against the Sanskrit, word by word; "
    "the order A/B carries no information. Output JSON only, exactly: "
    '{"items":[{"id":"<id>","a_label":"OK|MINOR|CONTRADICTED|UNSURE","a_evidence":"","b_label":"OK|MINOR|CONTRADICTED|UNSURE","b_evidence":"",'
    '"agree":true,"pick":"A|B","has_empirical_claim":false}]}. '
    "OK = faithful. MINOR = small loss, addition or awkwardness that does not change the meaning. CONTRADICTED = the meaning is wrong: a negation, "
    "number, agent, object or clause is changed, dropped or invented, or en and hi say different things. UNSURE = you cannot tell. "
    "For every label other than OK, the evidence field must name the Sanskrit word(s) in question and the wrong rendering, in at most 25 words; "
    "for OK leave it empty. Do not label CONTRADICTED for a legitimate alternative reading of an ambiguous or traditionally disputed word. "
    "agree = true only if A and B convey the same meaning. pick = the more faithful one. "
    "has_empirical_claim = true only if the Sanskrit itself states a health or natural-science fact. One item per given id and no other ids."
)
JUDGE_ONE_SYSTEM = (
    "You are a strict judge of translation fidelity for Sanskrit scripture. For each id you receive the Sanskrit and one translation with "
    "English (en) and Hindi (hi). Check it against the Sanskrit word by word. Output JSON only, exactly: "
    '{"items":[{"id":"<id>","label":"OK|MINOR|CONTRADICTED|UNSURE","evidence":""}]}. '
    "OK = faithful. MINOR = small loss, addition or awkwardness that does not change the meaning. CONTRADICTED = the meaning is wrong: a negation, "
    "number, agent, object or clause is changed, dropped or invented, or en and hi say different things. UNSURE = you cannot tell. "
    "For every label other than OK, evidence must name the Sanskrit word(s) in question and the wrong rendering, in at most 25 words; for OK leave it empty. "
    "Do not label CONTRADICTED for a legitimate alternative reading of an ambiguous or traditionally disputed word. One item per given id and no other ids."
)

# मॉडलों का चुनाव। env से बदला जा सकता है: PILOT_DRAFT_A, PILOT_DRAFT_B, PILOT_DRAFT_C, PILOT_JUDGES (अल्पविराम से)।
#   आधार: जज-परीक्षा (tools/pilot/judge_test.py; pilot-e2e run 43935550508, 16 नवंबर 2026)। Gemini 3.5 Flash-Lite ने 18 में से 17 डाली गई
#   ग़लतियाँ पकड़ीं और आधार-मसौदे की तीन असली ग़लतियों (ईश 10, 13, 18) पर भी आपत्ति की; qwen ने 15 पकड़ीं; gpt-oss-120b ने असली run में
#   इन्हीं तीन मंत्रों पर ग़लत ड्राफ़्ट चुना था। इसलिए जज = Flash-Lite (मास्टर योजना §3.3 की मूल रचना), और ड्राफ़्टर Google-परिवार
#   से बाहर के (जज अपने परिवार का काम नहीं जाँचता)। क़ीमत: Gemma 4 31B, जो तुलना में सबसे अच्छा ड्राफ़्टर दिखा, ड्राफ़्टर नहीं रहता।
#   यह चुनाव अस्थायी है: बाक़ी जजों (Gemma, Mistral, Llama, gpt-oss) की परीक्षा होने पर दोबारा देखा जाएगा।
#   हर भूमिका की सूची क्रम से आज़माई जाती है: पहला मॉडल उत्तर न दे (503, quota) तो अगला। कभी दूसरी key या दूसरा खाता नहीं।
DEFAULT_MODELS = {
    "draft_a": ["groq:qwen/qwen3.8-27b", "cloudflare:@cf/meta/llama-4-scout-17b-16e-instruct"],
    "draft_b": ["groq:openai/gpt-oss-120b", "cloudflare:@cf/openai/gpt-oss-120b"],
    "draft_c": ["cloudflare:@cf/mistralai/mistral-small-3.1-24b-instruct", "cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast"],
    "judges": ["google_ai_studio:gemini-3.5-flash-lite", "google_ai_studio:gemma-4-31b-it", "cloudflare:@cf/mistralai/mistral-small-3.1-24b-instruct",
               "cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast", "groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b"],
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Log:
    def __init__(self) -> None:
        self.stages: list[dict] = []

    def run(self, agent: str, name: str, fn, usage: Usage | None = None, model: Model | None = None):
        t0 = time.time()
        rec = {"agent": agent, "stage": name, "started": now_iso(), "status": "ok"}
        if model:
            rec["model"] = f"{model.provider}/{model.name}"
            rec["family"] = model.family
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            rec["status"] = "failed"
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            raise
        finally:
            rec["duration_s"] = round(time.time() - t0, 2)
            if usage:
                rec["usage"] = usage.as_dict()
            self.stages.append(rec)
            print(f"[{rec['status']}] {agent} · {name} · {rec['duration_s']} s", file=sys.stderr)


# ------------------------------------------------------------------ स्रोत
def load_source(text_id: str) -> tuple[dict[str, str], dict]:
    import isha_collate  # noqa: PLC0415
    if text_id != "isha":
        raise SystemExit(f"text '{text_id}' का स्रोत-loader अभी नहीं है")
    for attempt in range(3):
        try:
            isha_collate.fetch()
            break
        except Exception:  # noqa: BLE001  नेटवर्क की अस्थायी विफलता: दोबारा, फिर cache
            if attempt == 2 and not (isha_collate.CACHE / "sa_ws_isha.json").exists():
                raise
            time.sleep(5 * (attempt + 1))
    meta, text = isha_collate.load("sa_ws_isha")
    parsed = isha_collate.parse_a(text)
    segs = {f"isha:{n}": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", parsed[n])).strip() for n in sorted(parsed)}
    return segs, meta


def print_evidence(text_id: str) -> dict:
    """छपे आधार-संस्करण से मिलान का जो प्रमाण repo में पहले से है (OCR-coverage); न हो तो ख़ाली।"""
    p = REPO / "audit" / "witness" / f"{text_id}_ocr_ia-nsp-108-1925_Devanagari.json"
    if not p.exists():
        return {}
    rep = json.loads(p.read_text(encoding="utf-8"))
    return {r["segment"]: r["coverage"] for r in rep.get("segments", [])}


# ------------------------------------------------------------------ मॉडल
def pick_models(mock: bool) -> dict:
    if mock:
        return {"draft_a": [Model("mock", "mock-a", "mock-a")], "draft_b": [Model("mock", "mock-b", "mock-b")],
                "draft_c": [Model("mock", "mock-c", "mock-c")], "judges": [Model("mock", "mock-j", "mock-j"), Model("mock", "mock-k", "mock-k"),
                                                                             Model("mock", "mock-a", "mock-a"), Model("mock", "mock-b", "mock-b"),
                                                                             Model("mock", "mock-c", "mock-c")], "unavailable": []}
    out: dict = {"unavailable": []}
    for role, env in (("draft_a", "PILOT_DRAFT_A"), ("draft_b", "PILOT_DRAFT_B"), ("draft_c", "PILOT_DRAFT_C"), ("judges", "PILOT_JUDGES")):
        refs = [r.strip() for r in (os.environ.get(env) or "").split(",") if r.strip()] or DEFAULT_MODELS[role]
        out[role] = []
        for r in refs:
            m = parse_model(r)
            if available(m):
                out[role].append(m)
            else:
                out["unavailable"].append(m.ref)
        if not out[role]:
            raise SystemExit(f"{role}: किसी मॉडल की key env में नहीं है")
    return out


def draft_fb(log: "Log", agent: str, title: str, cands: list[Model], taken: set[str], dead: set[str], segs: dict[str, str], ids: list[str],
             usage: Usage) -> tuple[Model | None, dict[str, dict], list[dict]]:
    """सूची का पहला मॉडल जो आधे से ज़्यादा ids का ड्राफ़्ट दे और जिसका परिवार `taken` में न हो। जो उत्तर न दे वह `dead` में जाता है।"""
    best: tuple[Model | None, dict[str, dict]] = (None, {})
    tried: list[dict] = []
    for m in cands:
        if m.family in taken or m.ref in dead:
            continue
        d = log.run(agent, f"{title} · {m.name}", lambda m=m: draft(m, segs, ids, usage), usage, m)
        tried.append({"model": m.ref, "drafted": len(d)})
        if not d:
            dead.add(m.ref)
        if best[0] is None or len(d) > len(best[1]):
            best = (m, d)
        if len(d) * 2 > len(ids):
            break
    return best[0], best[1], tried


def judge_fb(log: "Log", title: str, pool: list[Model], exclude: set[str], dead: set[str], segs: dict[str, str], pairs: dict[str, tuple[dict, dict]],
             usage: Usage) -> tuple[Model | None, dict[str, dict], list[dict]]:
    """जज-सूची का पहला मॉडल जो `exclude` परिवारों से बाहर हो और आधे से ज़्यादा जोड़ों पर फ़ैसला दे।"""
    tried: list[dict] = []
    for m in pool:
        if m.family in exclude or m.ref in dead:
            continue
        v = log.run("judge", f"{title} · {m.name}", lambda m=m: judge(m, segs, pairs, usage), usage, m)
        tried.append({"model": m.ref, "judged": len(v)})
        if not v:
            dead.add(m.ref)
        if len(v) * 2 > len(pairs):
            return m, v, tried
    return None, {}, tried


def choose_judge(judges: list[Model], exclude: set[str]) -> Model:
    for m in judges:
        if m.family not in exclude:
            return m
    raise RuntimeError(f"इन परिवारों से अलग कोई जज नहीं: {sorted(exclude)}")


def chunk_size(model: Model) -> int:
    return {"google_ai_studio": 18, "groq": 6, "cloudflare": 6}.get(model.provider, 18)


def ask_items(model: Model, system: str, make_user, ids: list[str], usage: Usage, accept, est_out_per_id: int, mock_items=None) -> dict[str, dict]:
    """ids को टुकड़ों में भेजता है। जो id न लौटे या अमान्य लौटे, वह छोटे टुकड़ों में दोबारा जाती है (कुल 3 दौर)।
    किसी दौर में एक भी टुकड़ा सफल न हो तो आगे नहीं बढ़ता (provider बंद है; और अनुरोध बेकार हैं)।"""
    out: dict[str, dict] = {}
    pending, size = list(ids), chunk_size(model)
    for _round in range(3):
        if not pending:
            break
        any_ok, failed_in_a_row = False, 0
        for k in range(0, len(pending), size):
            part = pending[k:k + size]
            if model.provider == "mock":
                items = mock_items(part)
            else:
                if failed_in_a_row >= 2:  # लगातार दो टुकड़े विफल: provider अभी नहीं चल रहा
                    break
                try:
                    obj = chat_json(model, system, make_user(part), usage, est_out=est_out_per_id * len(part))
                except RuntimeError:
                    failed_in_a_row += 1
                    continue
                failed_in_a_row = 0
                items = obj.get("items", []) if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
            any_ok = True
            for it in items if isinstance(items, list) else []:
                i = it.get("id") if isinstance(it, dict) else None
                if i in part and i not in out:
                    v = accept(i, it)
                    if v is not None:
                        out[i] = v
        pending = [i for i in pending if i not in out]
        if not any_ok:
            break
        if pending:
            usage.retries += 1
        size = max(1, size // 2)
    return out


# ------------------------------------------------------------------ ड्राफ़्ट
def _valid_draft(item: dict, sa: str) -> bool:
    en, hi = item.get("en"), item.get("hi")
    if not isinstance(en, str) or not isinstance(hi, str) or len(en.strip()) < 8 or len(hi.strip()) < 8:
        return False
    if not re.search(r"[ऀ-ॿ]", hi) or re.search(r"[ऀ-ॿ]", en):
        return False
    return sa.strip() not in hi  # संस्कृत की नक़ल अनुवाद नहीं है


def draft(model: Model, segs: dict[str, str], ids: list[str], usage: Usage) -> dict[str, dict]:
    def mock_items(part: list[str]) -> list[dict]:
        return [{"id": i, "en": f"Mock translation {model.name} of segment {i.split(':')[1]}.", "hi": f"नक़ली अनुवाद {model.name}, खंड {i.split(':')[1]}।"} for i in part]

    def accept(i: str, it: dict) -> dict | None:
        return {"en": it["en"].strip(), "hi": it["hi"].strip()} if _valid_draft(it, segs[i]) else None

    return ask_items(model, DRAFT_SYSTEM, lambda part: "Translate these segments.\n" + "\n".join(f"{i}: {segs[i]}" for i in part),
                     ids, usage, accept, 350, mock_items)


# ------------------------------------------------------------------ जज
def _swapped(i: str, flip: bool) -> bool:
    """जज को A/B किस क्रम में दिखें, यह id के hash से तय होता है (स्थान-पक्षपात घटाने के लिए); flip उसे उलट देता है।"""
    return bool(hashlib.sha256(i.encode("utf-8")).digest()[0] & 1) ^ flip


def _evidence(v: object) -> str:
    return " ".join(str(v or "").split()[:25])


def judge(model: Model, segs: dict[str, str], pairs: dict[str, tuple[dict, dict]], usage: Usage, flip: bool = False) -> dict[str, dict]:
    def view(d: dict) -> dict:
        return {"en": d["en"], "hi": d["hi"]}

    def make_user(part: list[str]) -> str:
        payload = []
        for i in part:
            x, y = pairs[i]
            if _swapped(i, flip):
                x, y = y, x
            payload.append({"id": i, "sanskrit": segs[i], "A": view(x), "B": view(y)})
        return "Judge these.\n" + json.dumps(payload, ensure_ascii=False)

    def mock_items(part: list[str]) -> list[dict]:
        return [{"id": i, "a_label": "OK", "b_label": "OK", "a_evidence": "", "b_evidence": "", "agree": int(i.split(":")[1]) % 5 != 0,
                 "pick": "A" if _swapped(i, flip) ^ bool(int(i.split(":")[1]) % 2) else "B", "has_empirical_claim": False} for i in part]

    def accept(i: str, it: dict) -> dict | None:
        if not (it.get("a_label") in LABELS and it.get("b_label") in LABELS and it.get("pick") in ("A", "B") and isinstance(it.get("agree"), bool)):
            return None
        r = {"a_label": it["a_label"], "b_label": it["b_label"], "a_evidence": _evidence(it.get("a_evidence")), "b_evidence": _evidence(it.get("b_evidence")),
             "agree": it["agree"], "pick": it["pick"], "has_empirical_claim": bool(it.get("has_empirical_claim"))}
        if _swapped(i, flip):
            r["a_label"], r["b_label"] = r["b_label"], r["a_label"]
            r["a_evidence"], r["b_evidence"] = r["b_evidence"], r["a_evidence"]
            r["pick"] = "B" if r["pick"] == "A" else "A"
        for side in ("a", "b"):  # बिना प्रमाण का CONTRADICTED नहीं माना जाता
            if r[side + "_label"] == "CONTRADICTED" and not r[side + "_evidence"]:
                r[side + "_label"] = "UNSURE"
                r["downgraded_no_evidence"] = True
        return r

    return ask_items(model, JUDGE_SYSTEM, make_user, sorted(pairs, key=lambda s: int(s.split(":")[1])), usage, accept, 300, mock_items)


def judge_one(model: Model, segs: dict[str, str], drafts: dict[str, dict], usage: Usage) -> dict[str, dict]:
    """एक ही ड्राफ़्ट की जाँच (bake-off के लिए)।"""
    def accept(i: str, it: dict) -> dict | None:
        if it.get("label") not in LABELS:
            return None
        ev = _evidence(it.get("evidence"))
        return {"label": "UNSURE" if it["label"] == "CONTRADICTED" and not ev else it["label"], "evidence": ev}

    def make_user(part: list[str]) -> str:
        return "Judge these.\n" + json.dumps([{"id": i, "sanskrit": segs[i], "translation": {"en": drafts[i]["en"], "hi": drafts[i]["hi"]}} for i in part], ensure_ascii=False)

    return ask_items(model, JUDGE_ONE_SYSTEM, make_user, sorted(drafts, key=lambda s: int(s.split(":")[1])), usage, accept, 200,
                     lambda part: [{"id": i, "label": "OK", "evidence": ""} for i in part])


def accepted(j: dict | None) -> bool:
    return bool(j) and j["agree"] and j[("a" if j["pick"] == "A" else "b") + "_label"] in OK_LABELS


def stability(j_ref: dict[str, dict], j_other: dict[str, dict]) -> dict:
    """दो जज-दौरों की तुलना, एक ही ड्राफ़्ट-जोड़ों पर: label (ठीक/ग़लत), स्वीकार और चुनाव कितनी बार मिले।"""
    ids = [i for i in j_ref if i in j_other]
    if not ids:
        return {"n": 0}

    def ok(x: str) -> bool:
        return x in OK_LABELS

    lab = sum((ok(j_ref[i]["a_label"]) == ok(j_other[i]["a_label"])) + (ok(j_ref[i]["b_label"]) == ok(j_other[i]["b_label"])) for i in ids)
    return {"n": len(ids), "label_match": round(lab / (2 * len(ids)), 3),
            "accept_match": round(sum(accepted(j_ref[i]) == accepted(j_other[i]) for i in ids) / len(ids), 3),
            "pick_match": round(sum(j_ref[i]["pick"] == j_other[i]["pick"] for i in ids) / len(ids), 3),
            "accept_differs": [i for i in ids if accepted(j_ref[i]) != accepted(j_other[i])]}


# ------------------------------------------------------------------ पेड़
def write_json(p: Path, obj: object) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def assemble(root: Path, text_id: str, cfg: dict, segs: dict, src_meta: dict, final: dict, badges: dict, flags: dict, models_used: list[str], job_key: str | None) -> None:
    d = root / "texts" / text_id
    write_json(d / "_text.json", {
        "text_id": text_id, "work_id": cfg["work_id"], "title": cfg["title"], "base_edition": cfg["base_edition"], "witnesses": cfg["witnesses"],
        "citation_scheme": cfg["citation_scheme"], "chapters": [{"chapter": cfg["chapter"], "segment_count": cfg["segment_count"]}],
        "state": "WITNESS_DIFFED", "pipeline_version": PIPELINE_VERSION, "genre": cfg["genre"],
        "notes": "PILOT परीक्षण: आधार-संस्करण अस्थायी है (मालिक का G1-फ़ैसला बाक़ी); पाठ lock नहीं।"})
    created = now_iso()
    write_json(d / "root" / "sa-Deva" / f"{cfg['chapter']}.json", {
        "_meta": {"layer": "root", "text_id": text_id, "chapter": cfg["chapter"], "lang": "sa-Deva", "licence": src_meta["licence"], "redistribute": False,
                  "version": "0", "ai_generated": False,
                  "provenance": {"created_at": created, "by": "source_witness", "tool": "tools/pilot/run_e2e.py",
                                 "sources": [{"witness_id": cfg["carrier_witness"], "licence": src_meta["licence"], "usage": "compare", "sha256": src_meta["sha256"]}]}},
        "segments": segs, "witness_status": {i: "W1" for i in segs}})
    prov = {"created_at": created, "by": "jury_pick", "model": "+".join(models_used)[:200], "model_family": "mixed",
            "prompt_hash": hashlib.sha256((DRAFT_SYSTEM + JUDGE_SYSTEM).encode()).hexdigest()[:32], "tool": "tools/pilot/run_e2e.py"}
    if job_key:
        prov["job_key"] = job_key
    for lang in ("hi", "en"):
        layer = {"_meta": {"layer": "translation", "text_id": text_id, "chapter": cfg["chapter"], "lang": lang, "translation_id": "pilot-v0",
                           "licence": "LicenseRef-sanatan-granth-draft", "version": "0.1", "pipeline_version": PIPELINE_VERSION, "ai_generated": True,
                           "follows_commentary": "none-declared", "provenance": prov},
                 "segments": {i: final[i][lang] for i in segs}, "badges": badges}
        if flags:
            layer["flags"] = flags
        write_json(d / "translation" / lang / "pilot-v0" / f"{cfg['chapter']}.json", layer)


# ------------------------------------------------------------------ मुख्य
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="isha")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mock", action="store_true", help="कोई API-call नहीं; केवल कड़ी की जाँच")
    ap.add_argument("--job-key", default=None)
    ap.add_argument("--batch-id", default="manual")
    ap.add_argument("--no-probe", action="store_true", help="जज की स्थिरता का माप न चलाएँ (कम API-calls)")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cfg = TEXTS[a.text]
    out = Path(a.out)
    log, t_start = Log(), time.time()
    status, problems = "ok", []

    segs, src_meta = log.run("source_witness", "गवाह से पाठ लाना", lambda: load_source(a.text))
    ids = sorted(segs, key=lambda s: int(s.split(":")[1]))

    def align() -> None:
        if len(ids) != cfg["segment_count"] or ids != [f"{a.text}:{n}" for n in range(1, cfg["segment_count"] + 1)]:
            raise RuntimeError(f"ID-गिनती {len(ids)} ≠ घोषित {cfg['segment_count']} या क्रम टूटा")
    log.run("aligner", "ID और गिनती (गवाह के चिह्नों से)", align)
    evidence = print_evidence(a.text)

    models = log.run("foreman_code", "मॉडलों की सूचियाँ", lambda: pick_models(a.mock))
    dead: set[str] = set()   # इस run में जो मॉडल उत्तर नहीं दे रहे
    tried: dict[str, list] = {}

    uA, uB, uC, uJ1, uJ2, uP = Usage(), Usage(), Usage(), Usage(), Usage(), Usage()
    A, dA, tried["draft_a"] = draft_fb(log, "draft_a", "ड्राफ़्ट A", models["draft_a"], set(), dead, segs, ids, uA)
    B, dB, tried["draft_b"] = draft_fb(log, "draft_b", "ड्राफ़्ट B", models["draft_b"], {A.family} if A else set(), dead, segs, ids, uB)
    if A is None or B is None:
        raise SystemExit("ड्राफ़्ट A या B के लिए कोई मॉडल उपलब्ध नहीं")
    C: Model | None = None

    both = [i for i in ids if i in dA and i in dB]
    pairs1 = {i: (dA[i], dB[i]) for i in both}
    J1m, j1, tried["judge1"] = judge_fb(log, "जज, पहला दौर", models["judges"], {A.family, B.family}, dead, segs, pairs1, uJ1) if both else (None, {}, [])

    # जज की स्थिरता का माप: वही जोड़े (1) उसी जज को उलटे क्रम में, (2) एक और परिवार के जज को। फ़ैसला इससे नहीं बदलता।
    probe: dict = {}
    if J1m and j1 and not a.no_probe:
        try:
            j1_flip = log.run("judge_probe", "स्थिरता: वही जज, उलटा क्रम", lambda: judge(J1m, segs, pairs1, uP, flip=True), uP, J1m)
            probe["same_judge_flipped"] = {"model": J1m.ref, **stability(j1, j1_flip)}
        except Exception as e:  # noqa: BLE001
            probe["same_judge_flipped"] = {"error": type(e).__name__}
        try:
            Jalt, j1_alt, tried["judge_probe"] = judge_fb(log, "स्थिरता: दूसरे परिवार का जज", models["judges"], {A.family, B.family, J1m.family}, dead, segs, pairs1, uP)
            probe["other_family_judge"] = {"model": Jalt.ref, "family": Jalt.family, **stability(j1, j1_alt)} if Jalt else {"error": "दूसरे परिवार का कोई जज उत्तर नहीं दे रहा"}
        except Exception as e:  # noqa: BLE001
            probe["other_family_judge"] = {"error": f"{type(e).__name__}: {str(e)[:120]}"}

    final: dict[str, dict] = {}
    record: dict[str, dict] = {i: {} for i in ids}
    cascade: list[str] = []
    for i in ids:
        j = j1.get(i)
        record[i]["judge1"] = j
        if accepted(j):
            src = (dA, A) if j["pick"] == "A" else (dB, B)
            final[i] = {**src[0][i], "model": src[1].name, "family": src[1].family}
            record[i]["path"] = "पहले दौर में सहमति"
        else:
            cascade.append(i)

    flags: dict[str, list[str]] = {}
    j2: dict[str, dict] = {}
    judge2_used: list[str] = []
    j2_family: dict[str, str] = {}
    if cascade:
        C, dC, tried["draft_c"] = draft_fb(log, "draft_c", "ड्राफ़्ट C (केवल असहमति वाले)", models["draft_c"], {A.family, B.family}, dead, segs, cascade, uC)
        groups: dict[str, list[str]] = {}
        incumbent: dict[str, tuple[dict, Model]] = {}
        for i in cascade:
            j = j1.get(i)
            if j and i in dA and i in dB:
                incumbent[i] = (dA[i], A) if j["pick"] == "A" else (dB[i], B)
            elif i in dA:
                incumbent[i] = (dA[i], A)
            elif i in dB:
                incumbent[i] = (dB[i], B)
            if i in incumbent and i in dC:
                groups.setdefault(incumbent[i][1].family, []).append(i)
        for fam, gids in groups.items():
            J2m, res, t2 = judge_fb(log, f"जज, दूसरा दौर ({fam} बनाम {C.family})", models["judges"], {fam, C.family}, dead, segs,
                                    {i: (incumbent[i][0], dC[i]) for i in gids}, uJ2)
            tried.setdefault("judge2", []).extend(t2)
            if J2m:
                judge2_used.append(J2m.ref)
                j2_family.update({i: J2m.family for i in res})
            j2.update(res)
        for i in cascade:
            j = j2.get(i)
            record[i]["judge2"] = j
            inc = incumbent.get(i)
            c = dC.get(i)
            if j and inc and c:
                src = inc if j["pick"] == "A" else (c, C)
                final[i] = {**src[0], "model": src[1].name, "family": src[1].family}
                pick_ok = j[("a" if j["pick"] == "A" else "b") + "_label"] in OK_LABELS
                j1r = j1.get(i)
                # दूसरे दौर में "A" वही ड्राफ़्ट है जिसे पहले जज ने चुना था। अगर दूसरे परिवार का जज भी उसी को चुनकर ठीक कहे,
                # तो दो अलग परिवारों के जज एक ही ड्राफ़्ट पर सहमत हैं; हारे हुए ड्राफ़्ट की ग़लती से झंडा नहीं लगता।
                # यह छूट तभी है जब दूसरा जज सचमुच दूसरे परिवार का हो; वही जज दोबारा वही कहे तो वह स्वतंत्र पुष्टि नहीं है।
                confirmed_twice = (j["pick"] == "A" and pick_ok and j1r is not None and i in dA and i in dB
                                   and J1m is not None and j2_family.get(i) not in (None, J1m.family)
                                   and j1r[("a" if j1r["pick"] == "A" else "b") + "_label"] in OK_LABELS)
                if accepted(j):
                    record[i]["path"] = "cascade के बाद सहमति"
                elif confirmed_twice:
                    record[i]["path"] = "दो जजों ने वही ड्राफ़्ट चुना"
                else:
                    record[i]["path"] = "cascade के बाद भी असहमति"
                    flags.setdefault(i, []).append("CONTRADICTED" if "CONTRADICTED" in (j["a_label"], j["b_label"]) else "JURY_DISAGREE")
            elif inc or c:
                src = inc or (c, C)
                final[i] = {**src[0], "model": src[1].name, "family": src[1].family}
                record[i]["path"] = "जूरी अधूरी"
                flags.setdefault(i, []).append("JURY_INCOMPLETE")
            else:
                record[i]["path"] = "कोई ड्राफ़्ट नहीं"
                problems.append(f"{i}: कोई ड्राफ़्ट नहीं बना")

    missing = [i for i in ids if i not in final]
    if missing:
        status = "failed"
    incomplete = [i for i in ids if record[i].get("path") in ("जूरी अधूरी", "कोई ड्राफ़्ट नहीं")]
    if len(incomplete) * 2 > len(ids):
        # provider बंद या quota ख़त्म: आधे से ज़्यादा मंत्रों पर जूरी पूरी नहीं हुई। ऐसा नतीजा PR नहीं बनता; Foreman बाद में दोबारा चलाए।
        status = "failed"
        problems.append(f"{len(incomplete)}/{len(ids)} मंत्रों पर जूरी अधूरी (मॉडल उत्तर नहीं दे रहे: {sorted(dead)}); बाद में दोबारा चलाएँ")

    def hard_checks() -> dict:
        counts: dict[str, int] = {}
        for i in ids:
            if i not in final:
                continue
            for lang in ("hi", "en"):
                for f in d_checks.run_segment(segs[i], final[i][lang], lang):
                    if f.veto:
                        code = f"{f.check}:{lang}"
                        if code not in flags.setdefault(i, []):
                            flags[i].append(code)
                        counts[f.check] = counts.get(f.check, 0) + 1
            if i in flags and not flags[i]:
                del flags[i]
        return counts
    d_counts = log.run("hard_checks", "पक्की जाँचें D2/D3/D6/D7/D8", hard_checks)
    badges = {i: ("D" if i in flags else "C") for i in ids if i in final}

    gates: dict = {}
    if status == "ok":
        def build_and_check() -> None:
            models_used = sorted({final[i]["model"] for i in final})
            assemble(out / "tree", a.text, cfg, segs, src_meta, final, badges, flags, models_used, a.job_key)
            rep = checks_report(checks_run(out / "tree"))
            for name, c in rep["by_check"].items():
                gates[name] = "red" if c["fail"] else "green"
            gates["_findings"] = [{"check": f["check"], "path": f["path"], "msg": f["msg"][:160]} for f in rep["findings"] if f["level"] == "FAIL"][:20]
        log.run("export_prep", "परतों का पेड़ + R-जाँचें", build_and_check)
        unexpected = sorted(k for k, v in gates.items() if v == "red" and k not in EXPECTED_RED)
        if unexpected:
            status = "failed"
            problems.append(f"अनपेक्षित लाल जाँचें: {unexpected}")

    n = len(ids)
    first_pass = sum(1 for i in ids if record[i].get("path") == "पहले दौर में सहमति")
    usage_all = {"draft_a": uA.as_dict(), "draft_b": uB.as_dict(), "draft_c": uC.as_dict(), "judge1": uJ1.as_dict(), "judge2": uJ2.as_dict(), "judge_probe": uP.as_dict()}
    judged1 = [i for i in ids if j1.get(i)]
    metrics = {
        "generated_at": now_iso(), "text_id": a.text, "pipeline_version": PIPELINE_VERSION, "mock": a.mock, "status": status,
        "batch_id": a.batch_id, "job_key": a.job_key, "run": os.environ.get("GITHUB_RUN_ID"),
        "segments": n, "segments_done": len(final), "batch_size": n,
        "silent_omissions": 0 if not missing else len(missing),
        "cascade": {"first_pass_agreed": first_pass, "sent_to_cascade": len(cascade), "agreement_rate": round(first_pass / n, 3) if n else None,
                    "judged_in_round1": len(judged1), "agreement_rate_of_judged": round(first_pass / len(judged1), 3) if judged1 else None,
                    "draft_missing": {"a": [i for i in ids if i not in dA], "b": [i for i in ids if i not in dB]},
                    "judge1_missing": [i for i in both if i not in j1],
                    "go_threshold": 0.6, "by_path": {k: sum(1 for i in ids if record[i].get("path") == k) for k in sorted({record[i].get("path") or "?" for i in ids})}},
        "badges": {"C": sum(1 for b in badges.values() if b == "C"), "D": sum(1 for b in badges.values() if b == "D")},
        "flags_by_code": {k: sum(1 for v in flags.values() for c in v if c.split(":")[0] == k) for k in sorted({c.split(":")[0] for v in flags.values() for c in v})},
        "judge_stability": probe,
        "d_checks": {"implemented": list(d_checks.IMPLEMENTED), "not_run": list(d_checks.NOT_RUN), "veto_counts": d_counts},
        "empirical_claims_flagged_by_judge": sum(1 for i in ids for j in (record[i].get("judge1"), record[i].get("judge2")) if j and j.get("has_empirical_claim")),
        "models": {"draft_a": A.ref, "draft_b": B.ref, "draft_c": C.ref if C else None, "judge1": J1m.ref if J1m else None, "judge2": sorted(set(judge2_used)),
                   "judge_pool": [m.ref for m in models["judges"]], "tried": tried, "not_responding": sorted(dead), "no_key": models.get("unavailable", [])},
        "families": {"draft_a": A.family, "draft_b": B.family, "draft_c": C.family if C else None, "judge1": J1m.family if J1m else None},
        "api": {"calls": sum(u["calls"] for u in usage_all.values()), "retries": sum(u["retries"] for u in usage_all.values()),
                "http_429": sum(u["http_429"] for u in usage_all.values()), "prompt_tokens": sum(u["prompt_tokens"] for u in usage_all.values()),
                "output_tokens": sum(u["output_tokens"] for u in usage_all.values()), "paced_s": round(sum(u["paced_s"] for u in usage_all.values()), 1),
                "waited_s": round(sum(u["waited_s"] for u in usage_all.values()), 1), "neurons": round(sum(u["neurons"] for u in usage_all.values()), 1), "by_role": usage_all},
        "seconds_total": round(time.time() - t_start, 1), "stages": log.stages,
        "gates": {k: v for k, v in gates.items() if not k.startswith("_")}, "gates_expected_red": EXPECTED_RED,
        "gate_findings": gates.get("_findings", []), "problems": problems,
        "source": {"base_edition_provisional": cfg["base_edition"], "carrier_witness": cfg["carrier_witness"], "carrier_licence": src_meta["licence"],
                   "carrier_sha256": src_meta["sha256"], "witness_status": "W1 (lock नहीं)",
                   "print_coverage_min_mean": [min(evidence.values()), round(sum(evidence.values()) / len(evidence), 4)] if evidence else None},
        "limits": ["परीक्षण-run: स्रोत अस्थायी, पाठ lock नहीं; बना पेड़ repo में नहीं गया", "बैज C/D मशीन-जाँच के हैं; किसी इंसान ने अनुवाद नहीं देखा",
                   "D1, D4, D5, D9, D10, D12 नहीं चलीं", "एक छोटा ग्रंथ (18 मंत्र): दरें pilot-संकेत हैं, निष्कर्ष नहीं"],
    }
    segments_out = [{
        "id": i, "sa_sha256": hashlib.sha256(segs[i].encode("utf-8")).hexdigest(), "badge": badges.get(i), "flags": flags.get(i, []),
        "path": record[i].get("path"), "judge1": record[i].get("judge1"), "judge2": record[i].get("judge2"),
        "print_coverage": evidence.get(i), "final_model": (final.get(i) or {}).get("model"), "final_family": (final.get(i) or {}).get("family"),
        "en": (final.get(i) or {}).get("en"), "hi": (final.get(i) or {}).get("hi")} for i in ids]
    write_json(out / "report" / "pilot_metrics.json", metrics)
    write_json(out / "report" / f"{a.text}_e2e.json", {
        "_meta": {"label": "AI-मसौदा · मानव-समीक्षा नहीं", "ai_generated": True, "pipeline_version": PIPELINE_VERSION, "generated_at": metrics["generated_at"],
                  "licence": "LicenseRef-sanatan-granth-draft", "note": "पूरा संस्कृत पाठ इस फ़ाइल में नहीं है; केवल उसका hash (जज के प्रमाण में एक-दो शब्द आ सकते हैं)। अनुवाद परीक्षण के हैं।",
                  "mock": a.mock, "run": metrics["run"], "job_key": a.job_key},
        "segments": segments_out})
    print(json.dumps({k: metrics[k] for k in ("status", "segments", "segments_done", "cascade", "judge_stability", "badges", "flags_by_code", "models", "api", "seconds_total", "gates", "problems")}, ensure_ascii=False))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
