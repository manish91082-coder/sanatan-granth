"""स्वार्म के नियमों की आत्म-परीक्षा (कोई नेटवर्क नहीं, कोई key नहीं)।

    python -m tools.swarm.selftest

जाँचता है: विफलता का वर्गीकरण, मॉडल कितनी देर रुकता है, रचना का चुनाव (तीन परिवार, योग्य जज, पहले दर्जे का ड्राफ़्टर,
"इंतज़ार, गिरावट नहीं"), बचे हुए काम के साथ रचना, संचालक के फ़ैसले, और canary का चुनाव।
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.pilot import canary, llm  # noqa: E402
from tools.swarm import conductor, health  # noqa: E402

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 17, 10, 0, 0, tzinfo=UTC)
FL = "google_ai_studio:gemini-3.5-flash-lite"
NEMO = "openrouter:nvidia/nemotron-3-ultra-550b-a55b:free"
ERNIE = "openrouter:baidu/ernie-5.5-flash-preview:free"
OSS = "groq:openai/gpt-oss-120b"
QWEN = "groq:qwen/qwen3.8-27b"
GEMMA = "google_ai_studio:gemma-4-31b-it"
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def fresh() -> dict:
    return {"version": 1, "models": {}, "providers": {}}


def hold(h: dict, ref: str, reason: str, minutes: int) -> None:
    h["models"][ref] = {"cooldown_until": health.iso(NOW + dt.timedelta(minutes=minutes)), "reason": reason}


# नियमों की जाँच एक जमे हुए roster पर होती है (17 नवंबर 2026 का v0.1), ताकि असली roster बदलने पर ये जाँचें न बदलें।
# असली roster (policy/model_roster.json) की अपनी जाँचें अलग हैं: संगति, और "कोई एक provider बंद हो तो भी रचना बने"।
ROSTER = health.load_roster(Path(__file__).resolve().parent / "fixtures" / "roster_v0_1.json")
LIVE = health.load_roster()


@test
def roster_is_consistent():
    for roster in (ROSTER, LIVE):
        models, roles, rules = roster["models"], roster["roles"], roster["rules"]
        for role in ("drafters", "judges", "judge_candidates"):
            for ref in roles[role]:
                assert ref in models, f"{role}: {ref} models में नहीं"
        for ref in roles["drafters"]:
            assert models[ref]["draft"]["qualified"], f"ड्राफ़्टर-सूची में अयोग्य मॉडल: {ref}"
            assert models[ref]["draft"].get("evidence"), f"ड्राफ़्टर बिना प्रमाण के: {ref}"
        for ref in roles["judges"]:
            jd = models[ref]["judge"]
            assert jd["qualified"] and jd["catch_rate"] >= rules["judge_min_catch_rate"] and jd["items"] >= rules["judge_min_items"], ref
            assert jd.get("evidence") and jd.get("measured"), f"जज बिना प्रमाण के: {ref}"
        for ref, cfg in models.items():
            assert llm.parse_model(ref).family == cfg["family"], f"{ref}: roster का परिवार code के परिवार से अलग"
            assert health.provider_of(ref) in roster["providers"], f"{ref}: provider का reset-नियम roster में नहीं"
            if not (cfg.get("judge") or {}).get("qualified"):
                assert ref not in roles["judges"], f"अयोग्य जज सूची में: {ref}"


@test
def live_roster_survives_any_single_provider_outage():
    """quota की रुकावट का हल, जाँच के रूप में: कोई एक provider पूरा बंद हो (या उसका दिन का हिस्सा ख़त्म हो) तो भी योग्य रचना बने।"""
    assert health.plan(fresh(), LIVE, NOW, 18, check_key=False)["feasible"]
    used = {health.provider_of(r) for r in LIVE["roles"]["drafters"] + LIVE["roles"]["judges"]}
    assert len(used) >= 3, f"योग्य मॉडल केवल {sorted(used)} पर हैं"
    for prov in sorted(used):
        h = fresh()
        for ref in LIVE["models"]:
            if health.provider_of(ref) == prov:
                hold(h, ref, "overloaded", 24 * 60)  # दिन-भर बंद: "बेहतर का इंतज़ार" लागू न हो
        pl = health.plan(h, LIVE, NOW, 18, check_key=False)
        assert pl["feasible"], f"{prov} बंद हो तो कोई रचना नहीं बनती: {pl.get('reason')}"
        refs = list(pl["chosen"].values())
        assert all(health.provider_of(r) != prov for r in refs), (prov, refs)
        fams = pl["families"]
        assert len({fams["draft_a"], fams["draft_b"], fams["judge"]}) == 3
        tiers = [LIVE["models"][pl["chosen"][k]]["draft"]["tier"] for k in ("draft_a", "draft_b")]
        assert 1 in tiers, f"{prov} बंद: कोई पहले दर्जे का ड्राफ़्टर नहीं"


@test
def classify_failures():
    assert llm.classify(429, "Rate limit reached: tokens per day (TPD): Limit 200000") == "daily_quota"
    assert llm.classify(429, "free-models-per-day") == "daily_quota"
    assert llm.classify(429, "Request too large for model") == "too_large"
    assert llm.classify(429, "slow down") == "rate_limited"
    assert llm.classify(503, "high demand") == "overloaded"
    assert llm.classify(0, "TimeoutError") == "timeout"
    assert llm.classify(401, "") == "auth" and llm.classify(404, "") == "gone"
    assert abs(llm._retry_after_raw("Please try again in 3h2m5.5s. Need more?", {}) - 10925.5) < 0.01


@test
def cooldowns():
    # OpenRouter की दिन की सीमा: अगली UTC आधी रात के बाद तक
    t = health.cooldown_until("daily_quota", ROSTER, ERNIE, 1, NOW, None)
    assert t == dt.datetime(2026, 11, 18, 0, 5, tzinfo=UTC), t
    # Groq की चलती खिड़की: संदेश में बताया समय
    t = health.cooldown_until("daily_quota", ROSTER, OSS, 1, NOW, 3600.0)
    assert t == NOW + dt.timedelta(seconds=3660), t
    # Google: Pacific आधी रात (08:05 UTC)
    t = health.cooldown_until("daily_quota", ROSTER, FL, 1, NOW, None)
    assert t == dt.datetime(2026, 11, 18, 8, 5, tzinfo=UTC), t
    # रुकावट: 15 मिनट से शुरू, हर बार दुगुना, 6 घंटे तक
    mins = [(health.cooldown_until("overloaded", ROSTER, FL, n, NOW, None) - NOW).total_seconds() / 60 for n in (1, 2, 3, 9)]
    assert mins == [15, 30, 60, 360], mins


@test
def absorb_and_recover():
    h = fresh()
    held = health.absorb(h, {OSS: {"requests": 7, "ok": 5, "output_tokens": 900, "fail": {"kind": "daily_quota", "message": "TPD", "retry_after_s": 7200}}}, ROSTER, NOW)
    assert held and held[0]["reason"] == "daily_quota"
    assert not health.usable(h, ROSTER, OSS, "draft", NOW, 1, False)[0]
    assert health.usable(h, ROSTER, OSS, "draft", NOW + dt.timedelta(hours=3), 1, False)[0]
    health.absorb(h, {OSS: {"requests": 1, "ok": 1, "output_tokens": 10, "fail": None}}, ROSTER, NOW + dt.timedelta(hours=3))
    assert "cooldown_until" not in h["models"][OSS] and h["models"][OSS]["fails"] == 0
    # गुणवत्ता की रोक सफल अनुरोध से नहीं हटती
    health.hold_quality(h, ROSTER, ERNIE, "canary", NOW)
    health.absorb(h, {ERNIE: {"requests": 1, "ok": 1, "output_tokens": 10, "fail": None}}, ROSTER, NOW)
    assert h["models"][ERNIE]["reason"] == "quality"
    health.clear_quality(h, ERNIE)
    assert "reason" not in h["models"][ERNIE]


@test
def plan_prefers_best_composition():
    p = health.plan(fresh(), ROSTER, NOW, 18, check_key=False)
    assert p["feasible"] and p["chosen"] == {"draft_a": FL, "draft_b": NEMO, "judge": ERNIE, "draft_c": OSS}, p.get("chosen")
    fams = p["families"]
    assert len({fams["draft_a"], fams["draft_b"], fams["judge"]}) == 3
    for role in ("draft_a", "draft_b", "draft_c"):
        assert all(ROSTER["models"][r]["draft"]["qualified"] for r in p["lists"][role])
    assert p["lists"]["draft_a"] == [FL] and p["lists"]["draft_b"] == [NEMO], "run के भीतर A/B का कोई और विकल्प नहीं होना चाहिए"
    assert all(ROSTER["models"][r]["judge"]["qualified"] for r in p["lists"]["judges"])
    assert QWEN not in p["lists"]["judges"] and OSS not in p["lists"]["judges"]  # अयोग्य जज कभी नहीं


@test
def plan_waits_instead_of_degrading():
    # OpenRouter का दिन का हिस्सा पूरा: बचे हैं google, openai, qwen। योग्य जज केवल google का; तब दोनों ड्राफ़्टर दूसरे दर्जे के होंगे → नहीं चलेगा
    h = fresh()
    health.note_openrouter_usage(h, ROSTER, 50, NOW)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False)
    assert not p["feasible"] and p["next_try"] == "2026-11-18T00:05:00Z", p
    # अगले दिन वही बही: फिर से पूरी रचना
    p2 = health.plan(h, ROSTER, dt.datetime(2026, 11, 18, 0, 6, tzinfo=UTC), 18, check_key=False)
    assert p2["feasible"] and p2["chosen"]["judge"] == ERNIE


@test
def plan_switches_judge_or_waits_briefly():
    # ERNIE थोड़ी देर के लिए रुका: 15 मिनट में बेहतर रचना लौटेगी → इंतज़ार
    h = fresh()
    hold(h, ERNIE, "overloaded", 15)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False)
    assert not p["feasible"] and p["would_be"] == {"draft_a": NEMO, "draft_b": OSS, "judge": FL}, p
    # ERNIE पर गुणवत्ता की लंबी रोक: अब दूसरी योग्य रचना ही चलेगी (Nemotron + gpt-oss, जज Flash-Lite)
    h = fresh()
    hold(h, ERNIE, "quality", 7 * 24 * 60)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False)
    assert p["feasible"] and p["chosen"]["judge"] == FL and p["chosen"]["draft_a"] == NEMO and p["chosen"]["draft_b"] == OSS, p.get("chosen")
    assert p["families"]["draft_c"] not in (p["families"]["draft_a"], p["families"]["draft_b"])


@test
def plan_never_uses_unqualified_judge():
    # दोनों योग्य जज रुके: qwen और gpt-oss उपलब्ध हैं, पर वे जज नहीं बन सकते
    h = fresh()
    hold(h, ERNIE, "quality", 7 * 24 * 60)
    hold(h, FL, "overloaded", 30)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False)
    assert not p["feasible"] and p["next_try"] == health.iso(NOW + dt.timedelta(minutes=30)), p


@test
def plan_respects_saved_work():
    # ड्राफ़्ट A (Flash-Lite) और B (Nemotron) पिछले run में बन चुके; Nemotron अब रुका है, पर उससे नया अनुरोध नहीं चाहिए
    h = fresh()
    hold(h, NEMO, "overloaded", 120)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False, fixed={"draft_a": FL, "draft_b": NEMO})
    assert p["feasible"] and p["chosen"]["draft_a"] == FL and p["chosen"]["draft_b"] == NEMO and p["chosen"]["judge"] == ERNIE, p
    # बचे काम का जज गुणवत्ता की रोक पर हो तो उसके फ़ैसले नहीं माने जाते
    h = fresh()
    hold(h, ERNIE, "quality", 600)
    p = health.plan(h, ROSTER, NOW, 18, check_key=False, fixed={"draft_a": FL, "draft_b": NEMO, "judge": ERNIE})
    assert not p["feasible"]


@test
def provider_wide_exhaustion():
    # OpenRouter के एक मॉडल पर "दिन की सीमा" = पूरे खाते की सीमा: उसी provider का दूसरा मॉडल भी रुका माना जाता है
    h = fresh()
    health.absorb(h, {NEMO: {"requests": 1, "ok": 0, "output_tokens": 0, "fail": {"kind": "daily_quota", "message": "free-models-per-day", "retry_after_s": None}}}, ROSTER, NOW)
    assert not health.usable(h, ROSTER, ERNIE, "judge", NOW, 1, False)[0]
    assert health.usable(h, ROSTER, ERNIE, "judge", dt.datetime(2026, 11, 18, 0, 6, tzinfo=UTC), 1, False)[0]
    # Groq पर ऐसा नहीं: gpt-oss की दिन की सीमा से qwen नहीं रुकता
    h = fresh()
    health.absorb(h, {OSS: {"requests": 1, "ok": 0, "output_tokens": 0, "fail": {"kind": "daily_quota", "message": "TPD", "retry_after_s": 3600}}}, ROSTER, NOW)
    assert health.usable(h, ROSTER, QWEN, "draft", NOW, 1, False)[0]


@test
def replans_are_bounded():
    rules, st = ROSTER["rules"], {"status": "queued", "fails": 0}
    for n in range(1, 4):
        conductor.apply_record(st, {"batch_id": f"t.{n}", "status": "blocked", "blocked_until": health.iso(NOW), "at": health.iso(NOW)}, rules, NOW)
        assert st["status"] == "blocked" and st["replans"] == n
    conductor.apply_record(st, {"batch_id": "t.4", "status": "blocked", "blocked_until": health.iso(NOW), "at": health.iso(NOW)}, rules, NOW)
    assert st["status"] == "failed" and st["fails"] == 1, st


@test
def budgets():
    h = fresh()
    health.absorb(h, {NEMO: {"requests": 30, "ok": 30, "output_tokens": 0, "fail": None}, ERNIE: {"requests": 8, "ok": 8, "output_tokens": 0, "fail": None}}, ROSTER, NOW)
    assert health.remaining_provider(h, ROSTER, "openrouter", NOW) == 2
    b = health.run_budgets(h, ROSTER, NOW)
    assert b["provider:openrouter"] == 2 and b[FL] == 300
    # OpenRouter की अपनी गिनती हमारी गिनती से बड़ी हो तो वही मानी जाती है (मालिक की दूसरी keys)
    health.note_openrouter_usage(h, ROSTER, 45, NOW)
    assert health.remaining_provider(h, ROSTER, "openrouter", NOW) == 0
    assert not health.plan(h, ROSTER, NOW, 18, check_key=False)["feasible"]


@test
def llm_refuses_blocked_and_over_budget():
    m = llm.parse_model(OSS)
    u = llm.Usage()
    llm.BLOCKED[OSS] = "daily_quota"
    try:
        llm.chat_json(m, "s", "u", u)
        raise AssertionError("रुका मॉडल बुलाया गया")
    except RuntimeError:
        pass
    finally:
        llm.BLOCKED.clear()
    llm.BUDGET[OSS] = 0
    try:
        llm.chat_json(m, "s", "u", u)
        raise AssertionError("हिस्सा पूरा होने पर भी अनुरोध गया")
    except RuntimeError:
        assert llm.STATS[OSS]["fail"]["kind"] == "budget" and llm.STATS[OSS]["requests"] == 0
    finally:
        llm.BUDGET.clear()
        llm.STATS.clear()


@test
def canary_pick_is_deterministic():
    drafts = {f"x:{n}": {"en": "He does not go far into darkness, golden and swifter.", "hi": "वह दूर अंधकार में नहीं जाता।"} for n in range(1, 13)}
    order = sorted(drafts, key=lambda i: int(i.split(":")[1]))
    a, b = canary.pick(drafts, order, 4), canary.pick(drafts, order, 4)
    assert a == b and len(a) == 4
    for i, c in a.items():
        assert c["en"] != drafts[i]["en"], "बिगाड़ी नक़ल आधार जैसी है"
    assert canary.pick({"x:1": {"en": "Plain sentence.", "hi": "सादा वाक्य।"}}, ["x:1"], 4) == {}


@test
def conductor_decisions():
    daily, once = {"id": "t", "step": "pilot_e2e", "repeat": "daily"}, {"id": "o", "step": "pilot_e2e", "repeat": "once"}
    assert conductor.due(daily, {}, NOW) and conductor.due(once, {}, NOW)
    assert not conductor.due(daily, {"last_done": "2026-11-17T01:00:00Z"}, NOW)
    assert conductor.due(daily, {"last_done": "2026-11-16T23:00:00Z"}, NOW)
    assert not conductor.due(once, {"last_done": "2026-11-10T01:00:00Z"}, NOW)
    rules = ROSTER["rules"]
    st: dict = {"status": "queued", "fails": 0}
    conductor.apply_record(st, {"batch_id": "t.1", "status": "blocked", "blocked_until": "2026-11-18T00:05:00Z", "at": health.iso(NOW)}, rules, NOW)
    assert st["status"] == "blocked" and st["fails"] == 0, "रुकना विफलता नहीं गिना जाता"
    for n in (1, 2):
        conductor.apply_record(st, {"batch_id": "t.2", "status": "failed", "at": health.iso(NOW)}, rules, NOW)
        assert st["status"] == "failed" and st["fails"] == n
    conductor.apply_record(st, {"batch_id": "t.3", "status": "failed", "at": health.iso(NOW)}, rules, NOW)
    assert st["status"] == "needs_owner"
    conductor.apply_record(st, {"batch_id": "t.4", "status": "done", "at": health.iso(NOW)}, rules, NOW)
    assert st["status"] == "done" and st["fails"] == 0 and st["last_done"] == health.iso(NOW)
    assert conductor.task_of("isha-e2e.20261118.3") == "isha-e2e"


@test
def judge_requal_waits_for_roster_judges():
    task = {"id": "judge-requal", "step": "judge_test", "text_id": "isha", "repeat": "weekly"}
    old = {k: os.environ.pop(k, None) for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY")}
    try:
        assert conductor.feasibility(task, fresh(), ROSTER, None, NOW)["ok"]
        # OpenRouter का दिन पूरा: ERNIE (कड़ी का जज) नहीं नप सकता → परीक्षा टलती है, बाक़ी उम्मीदवार उपलब्ध हों तब भी
        h = fresh()
        health.note_openrouter_usage(h, ROSTER, 50, NOW)
        f = conductor.feasibility(task, h, ROSTER, None, NOW)
        assert not f["ok"] and f["next_try"] == "2026-11-18T00:05:00Z", f
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v


@test
def conductor_tick_dry_run():
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        h = fresh()
        health.note_openrouter_usage(h, ROSTER, 50, health.now_utc())
        health.save(sd, h)
        old = {k: os.environ.get(k) for k in ("SWARM_STATE_DIR", "FOREMAN_URL", "GH_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY")}
        os.environ["SWARM_STATE_DIR"] = d
        for k in list(old)[1:]:
            os.environ.pop(k, None)
        try:
            out = sys.stdout
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
            try:
                assert conductor.cmd_tick(argparse.Namespace(dry_run=True)) == 0
            finally:
                sys.stdout.close()
                sys.stdout = out
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        assert not (sd / "tasks.json").exists(), "dry-run ने हालत लिखी"


@test
def chapters_and_ids():
    from tools.pilot import run_e2e as R  # noqa: PLC0415
    g, i = R.TEXTS["gita"], R.TEXTS["isha"]
    ids = R.expected_ids("isha", i, ["1"])
    assert ids[0] == "isha:1" and len(ids) == 18, "एक अध्याय वाले ग्रंथ के ID में अध्याय नहीं लिखा जाता"
    ids = R.expected_ids("gita", g, ["2"])
    assert ids[0] == "gita:2.1" and ids[-1] == "gita:2.72" and len(ids) == 72
    assert R.chapter_of("gita:2.47", g) == "2" and R.chapter_of("isha:5", i) == "1"
    assert R.pick_chapters("", "gita-2-e2e", g) == ["2"], "अध्याय कतार से आने चाहिए"
    assert R.pick_chapters("", "isha-e2e", i) == ["1"]
    assert R.pick_chapters("2,1", "कोई-काम", g) == ["1", "2"]
    assert sorted(ids, key=R.seg_key) == ids


@test
def backlog_is_valid():
    b = json.loads((REPO / "swarm" / "BACKLOG.json").read_text(encoding="utf-8"))
    ids = [t["id"] for t in b["tasks"]]
    assert len(ids) == len(set(ids))
    for t in b["tasks"]:
        assert t["step"] in ("pilot_e2e", "judge_test") and t["repeat"] in ("once", "daily", "weekly")
        assert "." not in t["id"] and len(t["id"]) <= 40, "काम का id batch-id का पहला भाग बनता है"
        if t["step"] == "pilot_e2e":
            from tools.pilot import run_e2e as R  # noqa: PLC0415
            cfg = R.TEXTS[t["text_id"]]
            chs = [str(c) for c in t.get("chapters", [])] or list(cfg["chapters"])
            assert all(c in cfg["chapters"] for c in chs), f"{t['id']}: अध्याय घोषित नहीं"
            assert t.get("segments") == sum(cfg["chapters"][c] for c in chs), f"{t['id']}: segments घोषणा से अलग"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    failed = 0
    for fn in TESTS:
        snap = copy.deepcopy(ROSTER)
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        assert snap == ROSTER, f"{fn.__name__} ने roster बदल दिया"
    print(json.dumps({"tests": len(TESTS), "failed": failed}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
