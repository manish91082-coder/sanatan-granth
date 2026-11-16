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
from tools.pilot.llm import Model, Usage, chat_json, family_of, list_groq_models  # noqa: E402

PIPELINE_VERSION = "pilot-e2e-0.2"
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
    "translations, A and B, each with English (en) and Hindi (hi). Output JSON only, exactly: "
    '{"items":[{"id":"<id>","a_label":"OK|MINOR|CONTRADICTED|UNSURE","b_label":"OK|MINOR|CONTRADICTED|UNSURE","agree":true,'
    '"pick":"A|B","rationale":"<at most 40 words, English>","has_empirical_claim":false}]}. '
    "OK = faithful. MINOR = small loss or addition that does not change the meaning. CONTRADICTED = the meaning is wrong: a negation, "
    "number, agent or clause is changed, dropped or invented. UNSURE = you cannot tell. agree = true only if A and B convey the same "
    "meaning. pick = the more faithful one. has_empirical_claim = true only if the Sanskrit itself states a health or natural-science fact. "
    "One item per given id and no other ids."
)


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
        return {"draft_a": Model("mock", "mock-a", "mock-a"), "draft_b": Model("mock", "mock-b", "mock-b"),
                "draft_c": Model("mock", "mock-c", "mock-c"), "judges": [Model("mock", "mock-j", "mock-j"), Model("mock", "mock-a", "mock-a"),
                                                                           Model("mock", "mock-b", "mock-b"), Model("mock", "mock-c", "mock-c")]}
    ids = list_groq_models()
    if not ids:
        raise SystemExit("Groq के मॉडल नहीं मिले (GROQ_API_KEY?)")

    def first(*patterns: str, exclude: str = r"guard|whisper|tts|safeguard|prompt") -> str | None:
        for rx in patterns:
            for i in ids:
                if re.search(rx, i, re.I) and not re.search(exclude, i, re.I):
                    return i
        return None

    qwen = first(r"qwen")
    oss = first(r"gpt-oss-120b", r"gpt-oss")
    llama = first(r"llama.*(maverick|90b|70b|120b)", r"llama-?4", r"llama")
    gem = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
    if not qwen or not oss:
        raise SystemExit(f"ज़रूरी Groq मॉडल नहीं मिले: qwen={qwen} gpt-oss={oss}")
    g = lambda n: Model("groq", n, family_of(n))  # noqa: E731
    judges = ([g(llama)] if llama else []) + [g(oss), Model("google_ai_studio", gem, "google"), g(qwen)]
    return {"draft_a": g(qwen), "draft_b": Model("google_ai_studio", gem, "google"), "draft_c": g(oss), "judges": judges,
            "groq_models_seen": [i for i in ids if not re.search(r"whisper|tts|guard", i, re.I)]}


def choose_judge(judges: list[Model], exclude: set[str]) -> Model:
    for m in judges:
        if m.family not in exclude:
            return m
    raise RuntimeError(f"इन परिवारों से अलग कोई जज नहीं: {sorted(exclude)}")


def chunks(ids: list[str], model: Model) -> list[list[str]]:
    n = 18 if model.provider == "google_ai_studio" else (6 if model.provider == "groq" else 18)
    return [ids[i:i + n] for i in range(0, len(ids), n)]


# ------------------------------------------------------------------ ड्राफ़्ट
def _valid_draft(item: dict, sa: str) -> bool:
    en, hi = item.get("en"), item.get("hi")
    if not isinstance(en, str) or not isinstance(hi, str) or len(en.strip()) < 8 or len(hi.strip()) < 8:
        return False
    if not re.search(r"[ऀ-ॿ]", hi) or re.search(r"[ऀ-ॿ]", en):
        return False
    return sa.strip() not in hi  # संस्कृत की नक़ल अनुवाद नहीं है


def draft(model: Model, segs: dict[str, str], ids: list[str], usage: Usage) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for part in chunks(ids, model):
        todo = list(part)
        for _attempt in range(2):
            if not todo:
                break
            if model.provider == "mock":
                items = [{"id": i, "en": f"Mock translation {model.name} of segment {i.split(':')[1]}.", "hi": f"नक़ली अनुवाद {model.name}, खंड {i.split(':')[1]}।"} for i in todo]
            else:
                user = "Translate these segments.\n" + "\n".join(f"{i}: {segs[i]}" for i in todo)
                try:
                    obj = chat_json(model, DRAFT_SYSTEM, user, usage)
                except RuntimeError:
                    break
                items = obj.get("items", []) if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
            for it in items:
                i = it.get("id") if isinstance(it, dict) else None
                if i in todo and i not in out and _valid_draft(it, segs[i]):
                    out[i] = {"en": it["en"].strip(), "hi": it["hi"].strip()}
            todo = [i for i in todo if i not in out]
            if todo:
                usage.retries += 1
    return out


# ------------------------------------------------------------------ जज
def judge(model: Model, segs: dict[str, str], pairs: dict[str, tuple[dict, dict]], usage: Usage) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for part in chunks(sorted(pairs, key=lambda s: int(s.split(":")[1])), model):
        if model.provider == "mock":
            items = [{"id": i, "a_label": "OK", "b_label": "OK", "agree": int(i.split(":")[1]) % 5 != 0, "pick": "A" if int(i.split(":")[1]) % 2 else "B",
                      "rationale": "mock", "has_empirical_claim": False} for i in part]
        else:
            payload = [{"id": i, "sanskrit": segs[i], "A": pairs[i][0], "B": pairs[i][1]} for i in part]
            try:
                obj = chat_json(model, JUDGE_SYSTEM, "Judge these.\n" + json.dumps(payload, ensure_ascii=False), usage)
            except RuntimeError:
                continue
            items = obj.get("items", []) if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        for it in items:
            if not isinstance(it, dict) or it.get("id") not in part:
                continue
            if it.get("a_label") in LABELS and it.get("b_label") in LABELS and it.get("pick") in ("A", "B") and isinstance(it.get("agree"), bool):
                out[it["id"]] = {"a_label": it["a_label"], "b_label": it["b_label"], "agree": it["agree"], "pick": it["pick"],
                                 "rationale": " ".join(str(it.get("rationale", "")).split()[:40]), "has_empirical_claim": bool(it.get("has_empirical_claim"))}
    return out


def accepted(j: dict | None) -> bool:
    return bool(j) and j["agree"] and j[("a" if j["pick"] == "A" else "b") + "_label"] in OK_LABELS


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

    models = log.run("foreman_code", "मॉडल और परिवार चुनना", lambda: pick_models(a.mock))
    A, B, C = models["draft_a"], models["draft_b"], models["draft_c"]
    if len({A.family, B.family, C.family}) != 3:
        raise SystemExit("ड्राफ़्टरों के परिवार अलग नहीं हैं")

    uA, uB, uC, uJ1, uJ2 = Usage(), Usage(), Usage(), Usage(), Usage()
    dA = log.run("draft_a", "ड्राफ़्ट A", lambda: draft(A, segs, ids, uA), uA, A)
    dB = log.run("draft_b", "ड्राफ़्ट B", lambda: draft(B, segs, ids, uB), uB, B)

    both = [i for i in ids if i in dA and i in dB]
    J1m = choose_judge(models["judges"], {A.family, B.family})
    j1 = log.run("judge", "जज, पहला दौर", lambda: judge(J1m, segs, {i: (dA[i], dB[i]) for i in both}, uJ1), uJ1, J1m) if both else {}

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
    if cascade:
        dC = log.run("draft_c", "ड्राफ़्ट C (केवल असहमति वाले)", lambda: draft(C, segs, cascade, uC), uC, C)
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
            J2m = choose_judge(models["judges"], {fam, C.family})
            res = log.run("judge", f"जज, दूसरा दौर ({fam} बनाम {C.family})",
                          lambda gids=gids, J2m=J2m: judge(J2m, segs, {i: (incumbent[i][0], dC[i]) for i in gids}, uJ2), uJ2, J2m)
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
                confirmed_twice = (j["pick"] == "A" and pick_ok and j1r is not None and i in dA and i in dB
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
    usage_all = {"draft_a": uA.as_dict(), "draft_b": uB.as_dict(), "draft_c": uC.as_dict(), "judge1": uJ1.as_dict(), "judge2": uJ2.as_dict()}
    metrics = {
        "generated_at": now_iso(), "text_id": a.text, "pipeline_version": PIPELINE_VERSION, "mock": a.mock, "status": status,
        "batch_id": a.batch_id, "job_key": a.job_key, "run": os.environ.get("GITHUB_RUN_ID"),
        "segments": n, "segments_done": len(final), "batch_size": n,
        "silent_omissions": 0 if not missing else len(missing),
        "cascade": {"first_pass_agreed": first_pass, "sent_to_cascade": len(cascade), "agreement_rate": round(first_pass / n, 3) if n else None,
                    "go_threshold": 0.6, "by_path": {k: sum(1 for i in ids if record[i].get("path") == k) for k in sorted({record[i].get("path") or "?" for i in ids})}},
        "badges": {"C": sum(1 for b in badges.values() if b == "C"), "D": sum(1 for b in badges.values() if b == "D")},
        "flags_by_code": {k: sum(1 for v in flags.values() for c in v if c.split(":")[0] == k) for k in sorted({c.split(":")[0] for v in flags.values() for c in v})},
        "d_checks": {"implemented": list(d_checks.IMPLEMENTED), "not_run": list(d_checks.NOT_RUN), "veto_counts": d_counts},
        "empirical_claims_flagged_by_judge": sum(1 for i in ids for j in (record[i].get("judge1"), record[i].get("judge2")) if j and j.get("has_empirical_claim")),
        "models": {"draft_a": f"{A.provider}/{A.name}", "draft_b": f"{B.provider}/{B.name}", "draft_c": f"{C.provider}/{C.name}",
                   "judge_pool": [f"{m.provider}/{m.name}" for m in models["judges"]], "groq_models_seen": models.get("groq_models_seen", [])},
        "families": {"draft_a": A.family, "draft_b": B.family, "draft_c": C.family},
        "api": {"calls": sum(u["calls"] for u in usage_all.values()), "retries": sum(u["retries"] for u in usage_all.values()),
                "http_429": sum(u["http_429"] for u in usage_all.values()), "prompt_tokens": sum(u["prompt_tokens"] for u in usage_all.values()),
                "output_tokens": sum(u["output_tokens"] for u in usage_all.values()), "by_role": usage_all},
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
                  "licence": "LicenseRef-sanatan-granth-draft", "note": "संस्कृत पाठ इस फ़ाइल में नहीं है; केवल उसका hash। अनुवाद परीक्षण के हैं।",
                  "mock": a.mock, "run": metrics["run"], "job_key": a.job_key},
        "segments": segments_out})
    print(json.dumps({k: metrics[k] for k in ("status", "segments", "segments_done", "cascade", "badges", "flags_by_code", "models", "api", "seconds_total", "gates", "problems")}, ensure_ascii=False))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
