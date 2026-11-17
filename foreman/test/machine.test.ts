// node --experimental-strip-types --test test/*.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  conductBatch, CONDUCT_EVERY_S, DEFAULT_LIMITS, ENQUEUEABLE, jobKey, nextReset, planTick, validateBookTransition, validateJobTransition, hmacHex, timingSafeEqual,
  type Job, type Provider,
} from "../src/machine.ts";

const T = "2026-11-15T10:00:00.000Z";
const job = (o: Partial<Job>): Job => ({
  job_key: "k", text_id: "isha", batch_id: "1", step: "noop", lane: "L1", status: "queued", provider: null,
  attempts: 0, started_at: null, updated_at: T, ...o,
});
const prov = (o: Partial<Provider>): Provider => ({
  provider: "gemini", limit_per_window: 100, used: 0, window_reset_utc: "2026-11-16T08:00:00.000Z", breaker_open: 0, ...o,
});

test("STOP पर कोई action नहीं", () => {
  assert.deepEqual(planTick([job({})], [], T, true), []);
});

test("एक lane में एक समय में एक ही dispatch", () => {
  const a = planTick([job({ job_key: "a" }), job({ job_key: "b" })], [], T, false);
  assert.equal(a.filter((x) => x.kind === "dispatch").length, 1);
});

test("चलती lane में नया dispatch नहीं", () => {
  const a = planTick([job({ job_key: "a", status: "running", started_at: T }), job({ job_key: "b" })], [], T, false);
  assert.equal(a.length, 0);
});

test("quota भरा हो तो job reset तक सोए, dispatch न हो", () => {
  const a = planTick([job({ provider: "gemini" })], [prov({ used: 100 })], T, false);
  assert.equal(a.length, 1);
  assert.equal(a[0].kind, "sleep");
});

test("breaker खुला हो तो dispatch नहीं", () => {
  const a = planTick([job({ provider: "gemini" })], [prov({ breaker_open: 1 })], T, false);
  assert.equal(a[0].kind, "sleep");
});

test("reset के बाद सोया job जागे", () => {
  const a = planTick([job({ status: "waiting_reset", provider: "gemini" })], [prov({ window_reset_utc: "2026-11-15T08:00:00.000Z" })], T, false);
  assert.equal(a[0].kind, "wake");
});

test("बहुत देर से running → timeout; retry-सीमा के बाद requeue नहीं", () => {
  const old = "2026-11-15T00:00:00.000Z";
  const a1 = planTick([job({ status: "running", started_at: old, attempts: 1 })], [], T, false);
  assert.deepEqual(a1.map((x) => x.kind), ["timeout"]);
  assert.equal((a1[0] as { requeue: boolean }).requeue, true);
  const a2 = planTick([job({ status: "running", started_at: old, attempts: DEFAULT_LIMITS.maxRetryPerStep + 1 })], [], T, false);
  assert.equal((a2[0] as { requeue: boolean }).requeue, false);
});

test("failed में अटका job: backoff के बाद requeue; retry-सीमा के बाद needs_expert; backoff से पहले कुछ नहीं", () => {
  const old = "2026-11-15T09:00:00.000Z";
  const a1 = planTick([job({ status: "failed", attempts: 1, updated_at: old })], [], T, false);
  assert.deepEqual(a1.map((x) => x.kind), ["retry"]);
  assert.equal((a1[0] as { requeue: boolean }).requeue, true);
  const a2 = planTick([job({ status: "failed", attempts: DEFAULT_LIMITS.maxRetryPerStep + 1, updated_at: old })], [], T, false);
  assert.equal((a2[0] as { requeue: boolean }).requeue, false);
  const a3 = planTick([job({ status: "failed", attempts: 1, updated_at: "2026-11-15T09:55:00.000Z" })], [], T, false);
  assert.deepEqual(a3, []);
  assert.deepEqual(planTick([job({ status: "failed", attempts: 1, updated_at: old })], [], T, true), []);
});

test("एक tick में dispatch की सीमा", () => {
  const jobs = Array.from({ length: 12 }, (_, i) => job({ job_key: "k" + i, lane: "L" + i }));
  assert.equal(planTick(jobs, [], T, false).length, DEFAULT_LIMITS.maxDispatchPerTick);
});

test("अवस्था-बदलाव: केवल वैध", () => {
  assert.ok(validateJobTransition("queued", "running"));
  assert.ok(!validateJobTransition("done", "queued"));
  assert.ok(!validateJobTransition("queued", "done"));
  assert.ok(validateBookTransition("WITNESS_DIFFED", "TEXT_LOCKED"));
  assert.ok(!validateBookTransition("CATALOGUED", "TEXT_LOCKED"));
  assert.ok(!validateBookTransition("TEXT_LOCKED", "WITNESS_DIFFED"));
});

test("reset-घड़ियाँ", () => {
  assert.equal(nextReset("utc_midnight", T), "2026-11-16T00:00:00.000Z");
  assert.equal(nextReset("pacific_midnight", T), "2026-11-16T08:00:00.000Z");
  assert.equal(nextReset("pacific_midnight", "2026-11-15T07:00:00.000Z"), "2026-11-15T08:00:00.000Z");
  assert.equal(nextReset("weekly_sat", T), "2026-11-21T00:00:00.000Z"); // 15 नवंबर 2026 रविवार है
});

test("job_key स्थिर और Python वाले से वही", async () => {
  // python -c "from checks.common import job_key; print(job_key('selftest','b1','noop','none','none'))"
  assert.equal(await jobKey("selftest", "b1", "noop", "none", "none"), "fa4f51f51c89e94219febbb07f9e2ed25964b2ffdbe6e7ee46bd63c7441f540a");
});

test("pilot_e2e का job_key Python वाले से वही; अनुमत steps की सूची", async () => {
  // python -c "from checks.common import job_key; print(job_key('isha','b1','pilot_e2e','pilot-e2e-0.1','cascade'))"
  const spec = ENQUEUEABLE["pilot_e2e"]!;
  assert.equal(await jobKey("isha", "b1", "pilot_e2e", spec.promptHash, spec.model), "1aeb3c35d459f367747b7bc95810f28576337f5a30665e8473cb68b544edd0d0");
  assert.deepEqual(Object.keys(ENQUEUEABLE).sort(), ["conduct", "judge_test", "noop", "pilot_e2e"]);
  assert.notEqual(ENQUEUEABLE["noop"]!.lane, spec.lane);
});

test("HMAC और समय-सुरक्षित तुलना", async () => {
  const h = await hmacHex("secret", "body");
  assert.equal(h.length, 64);
  assert.ok(timingSafeEqual(h, h));
  assert.ok(!timingSafeEqual(h, h.replace(/.$/, "0") === h ? h.replace(/.$/, "1") : h.replace(/.$/, "0")));
});

test("स्वार्म की घड़ी: एक ही समय-खाँचे में एक ही batch; अगले खाँचे में नया", () => {
  const a = conductBatch("2026-11-17T10:00:00.000Z");
  assert.equal(a, conductBatch("2026-11-17T10:19:59.000Z"));
  assert.notEqual(a, conductBatch("2026-11-17T10:20:00.000Z"));
  assert.match(a, /^slot-[0-9]+$/);
  assert.equal(CONDUCT_EVERY_S, 1200);
});

test("संचालक और जज-परीक्षा कतार में डाले जा सकते हैं; मॉडल-काम एक ही lane में", () => {
  assert.equal(ENQUEUEABLE["conduct"]!.lane, "conduct");
  assert.equal(ENQUEUEABLE["judge_test"]!.lane, ENQUEUEABLE["pilot_e2e"]!.lane);
  const a = planTick([
    job({ job_key: "p", step: "pilot_e2e", lane: "pilot", status: "running", started_at: T }),
    job({ job_key: "j", step: "judge_test", lane: "pilot" }),
    job({ job_key: "c", step: "conduct", lane: "conduct" }),
  ], [], T, false);
  assert.deepEqual(a.map((x) => [x.kind, x.job.job_key]), [["dispatch", "c"]]);
});

test("step की अपनी समय-सीमा: संचालक 20 मिनट पर, pilot 90 मिनट पर", () => {
  const started = "2026-11-15T09:30:00.000Z"; // 30 मिनट पहले
  const c = planTick([job({ step: "conduct", lane: "conduct", status: "running", started_at: started, attempts: 1 })], [], T, false);
  assert.deepEqual(c.map((x) => x.kind), ["timeout"]);
  const p = planTick([job({ step: "pilot_e2e", lane: "pilot", status: "running", started_at: started, attempts: 1 })], [], T, false);
  assert.equal(p.length, 0);
});
