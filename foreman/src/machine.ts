// नियतात्मक state machine: शुद्ध functions, कोई I/O नहीं, कोई LLM नहीं।
// मास्टर योजना §5.2 (अवस्थाएँ), §5.4 (रेलिंग 1, 2, 5, 6, 7)।

export const BOOK_STATES = [
  "CATALOGUED", "SELECTED", "SOURCES_APPROVED", "ACQUIRED", "NORMALISED", "WITNESS_DIFFED",
  "TEXT_LOCKED", "ANALYSED", "DRAFTED", "JUDGED", "REVISED", "SCIENCE_SCREENED",
  "MACHINE_COMPLETE", "RELEASED_INTERNAL",
] as const;
export type BookState = (typeof BOOK_STATES)[number];

export const JOB_STATUSES = ["queued", "running", "done", "failed", "waiting_reset", "needs_expert"] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

export const STEPS = [
  "acquire", "normalise", "witness_diff", "text_lock", "analyse", "draft_a", "draft_b", "draft_c",
  "judge", "revise", "checks", "science", "export", "noop",
] as const;
export type Step = (typeof STEPS)[number];

/** ग्रंथ एक बार में केवल अगली अवस्था में जा सकता है; पीछे कभी नहीं। */
export function validateBookTransition(from: BookState, to: BookState): boolean {
  return BOOK_STATES.indexOf(to) === BOOK_STATES.indexOf(from) + 1;
}

const JOB_NEXT: Record<JobStatus, JobStatus[]> = {
  queued: ["running", "waiting_reset"],
  running: ["done", "failed", "waiting_reset", "needs_expert"],
  failed: ["queued", "needs_expert"], // retry (सीमा के भीतर) या D
  waiting_reset: ["queued"],
  done: [],
  needs_expert: [],
};

export function validateJobTransition(from: JobStatus, to: JobStatus): boolean {
  return JOB_NEXT[from].includes(to);
}

export interface Job {
  job_key: string;
  text_id: string;
  batch_id: string;
  step: Step;
  lane: string;
  status: JobStatus;
  provider: string | null;
  attempts: number;
  started_at: string | null;
  updated_at: string;
}

export interface Provider {
  provider: string;
  limit_per_window: number;
  used: number;
  window_reset_utc: string;
  breaker_open: number;
}

export interface Limits {
  maxRetryPerStep: number; // policy/thresholds.json batch.max_retry_per_step
  switchAt: number; // provider_budget.switch_at (0.90)
  sleepAt: number; // provider_budget.sleep_at (1.00)
  runningTimeoutS: number; // इतनी देर से 'running' हो तो विफल मानें
  maxDispatchPerTick: number;
  retryBackoffS: number; // 'failed' में पड़ा job इतनी देर बाद ही दोबारा देखा जाए
}

export const DEFAULT_LIMITS: Limits = {
  maxRetryPerStep: 2,
  switchAt: 0.9,
  sleepAt: 1.0,
  runningTimeoutS: 7 * 3600, // Actions job की 6 घंटे की सीमा + गुंजाइश
  maxDispatchPerTick: 5,
  retryBackoffS: 600,
};

export type Action =
  | { kind: "dispatch"; job: Job }
  | { kind: "timeout"; job: Job; requeue: boolean }
  | { kind: "retry"; job: Job; requeue: boolean }
  | { kind: "sleep"; job: Job; until: string; reason: string }
  | { kind: "wake"; job: Job };

export function providerHasRoom(p: Provider | undefined, lim: Limits): boolean {
  if (!p) return true; // CPU-only lane (कोई quota नहीं)
  if (p.breaker_open) return false;
  return p.used < lim.sleepAt * p.limit_per_window;
}

/**
 * एक tick की योजना। नियम:
 *  - STOP हो तो कुछ नहीं।
 *  - हर lane में एक समय में अधिकतम एक सक्रिय (running) dispatch।
 *  - provider का quota भरा हो तो job उसकी reset-घड़ी तक सोए (कभी दूसरी key/खाता नहीं)।
 *  - 'running' बहुत देर से हो तो timeout: retry-सीमा के भीतर दोबारा कतार में, वरना needs_expert (D)।
 *  - 'failed' में अटका job (जैसे dispatch की HTTP-त्रुटि) backoff के बाद: retry-सीमा के भीतर दोबारा कतार में, वरना needs_expert (D)।
 *  - एक tick में अधिकतम maxDispatchPerTick dispatch।
 */
export function planTick(
  jobs: Job[],
  providers: Provider[],
  nowIso: string,
  stop: boolean,
  lim: Limits = DEFAULT_LIMITS,
): Action[] {
  if (stop) return [];
  const now = Date.parse(nowIso);
  const prov = new Map(providers.map((p) => [p.provider, p]));
  const actions: Action[] = [];
  const busyLanes = new Set<string>();

  for (const j of jobs) {
    if (j.status !== "running") continue;
    const started = j.started_at ? Date.parse(j.started_at) : now;
    if ((now - started) / 1000 > lim.runningTimeoutS) {
      actions.push({ kind: "timeout", job: j, requeue: j.attempts < lim.maxRetryPerStep + 1 });
    } else {
      busyLanes.add(j.lane);
    }
  }

  for (const j of jobs) {
    if (j.status !== "failed") continue;
    if ((now - Date.parse(j.updated_at)) / 1000 < lim.retryBackoffS) continue;
    actions.push({ kind: "retry", job: j, requeue: j.attempts < lim.maxRetryPerStep + 1 });
  }

  for (const j of jobs) {
    if (j.status !== "waiting_reset") continue;
    const p = j.provider ? prov.get(j.provider) : undefined;
    if (!p || (Date.parse(p.window_reset_utc) <= now && !p.breaker_open)) actions.push({ kind: "wake", job: j });
  }

  let dispatched = 0;
  const queued = jobs.filter((j) => j.status === "queued").sort((a, b) => a.updated_at.localeCompare(b.updated_at));
  for (const j of queued) {
    if (dispatched >= lim.maxDispatchPerTick) break;
    if (busyLanes.has(j.lane)) continue;
    const p = j.provider ? prov.get(j.provider) : undefined;
    if (!providerHasRoom(p, lim)) {
      actions.push({
        kind: "sleep",
        job: j,
        until: p!.window_reset_utc,
        reason: p!.breaker_open ? "breaker खुला" : "quota भरा; reset का इंतज़ार",
      });
      continue;
    }
    actions.push({ kind: "dispatch", job: j });
    busyLanes.add(j.lane);
    dispatched++;
  }
  return actions;
}

/** अगला reset-क्षण (मास्टर योजना §5.7)। */
export function nextReset(rule: string, nowIso: string): string {
  const d = new Date(nowIso);
  if (rule === "pacific_midnight") {
    // Gemini: आधी रात Pacific ≈ 08:00 UTC (PST)। DST में 07:00 UTC; अंतर को सुरक्षित ओर (देर से) रखा है।
    const r = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 8, 0, 0));
    if (r.getTime() <= d.getTime()) r.setUTCDate(r.getUTCDate() + 1);
    return r.toISOString();
  }
  if (rule === "weekly_sat") {
    const r = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 0, 0, 0));
    const add = (6 - r.getUTCDay() + 7) % 7 || 7;
    r.setUTCDate(r.getUTCDate() + add);
    return r.toISOString();
  }
  const r = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 1, 0, 0, 0)); // utc_midnight / daily
  return r.toISOString();
}

/** idempotency-कुंजी: checks/common.py के job_key() से अक्षरशः वही। */
export async function jobKey(corpus: string, batchId: string, step: string, promptHash: string, model: string): Promise<string> {
  const data = new TextEncoder().encode([corpus, batchId, step, promptHash, model].join("\x1f"));
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** HMAC-SHA256 hex (callback और admin अनुरोधों की पहचान)। */
export async function hmacHex(secret: string, body: string): Promise<string> {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let x = 0;
  for (let i = 0; i < a.length; i++) x |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return x === 0;
}
