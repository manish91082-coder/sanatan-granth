// ForemanAgent: Cloudflare पर हमेशा जागती नियंत्रण-परत (मास्टर योजना §5.1–5.4, क़दम 0.11)।
//
// नियम जो यहाँ code में बँधे हैं:
//  - रास्ता code तय करता है (machine.ts का planTick); यहाँ कोई LLM-call नहीं, कोई LLM-routing नहीं।
//  - Agent कभी लंबा इंतज़ार नहीं करता: वह केवल बही पढ़ता है, GitHub Actions को dispatch करता है और सो जाता है।
//  - हर बाहरी असर idempotent है: job_key ही प्राथमिक कुंजी है; दोबारा चलना no-op।
//  - swarm/STOP फ़ाइल या /admin/stop → कोई dispatch नहीं।
//  - बड़ा पाठ यहाँ कभी नहीं आता; प्रति batch एक पंक्ति।

import { Agent, getAgentByName } from "agents";
import {
  conductBatch, DEFAULT_LIMITS, ENQUEUEABLE, hmacHex, jobKey, nextReset, planTick, timingSafeEqual, validateJobTransition,
  type Job, type JobStatus, type Provider,
} from "./machine";

interface Env {
  FOREMAN: DurableObjectNamespace<ForemanAgent>;
  LEDGER: D1Database;
  GITHUB_REPO: string; // "owner/name"
  FOREMAN_SHARED_SECRET: string; // secret: callback/admin के HMAC के लिए
  GITHUB_DISPATCH_TOKEN: string; // secret: fine-grained token, केवल इसी repo पर
}

interface ForemanState {
  lastTick: string | null;
  lastTickSource: string | null;
  lastActions: number;
  stopped: boolean;
  stopReason: string | null;
  publicOrigin: string | null;
  consecutiveErrors: number;
}

const TICK_SECONDS = 300;
const nowIso = () => new Date().toISOString();

export class ForemanAgent extends Agent<Env, ForemanState> {
  initialState: ForemanState = {
    lastTick: null, lastTickSource: null, lastActions: 0, stopped: false, stopReason: null,
    publicOrigin: null, consecutiveErrors: 0,
  };

  async onStart(): Promise<void> {
    // idempotent: DO जितनी बार जागे, schedule एक ही रहता है
    await this.scheduleEvery(TICK_SECONDS, "tick");
  }

  /** Scheduler callback। eviction के बाद दोबारा चल सकता है, इसलिए सब कुछ idempotent है। */
  async tick(source: string = "schedule"): Promise<{ actions: number; stopped: boolean }> {
    const db = this.env.LEDGER;
    const now = nowIso();
    try {
      const stopFile = await this.stopFileExists();
      const stopped = this.state.stopped || stopFile;
      if (stopped) {
        this.setState({ ...this.state, lastTick: now, lastTickSource: source, lastActions: 0,
          stopReason: stopFile ? "swarm/STOP फ़ाइल मौजूद" : this.state.stopReason });
        return { actions: 0, stopped: true };
      }

      // reset-घड़ियाँ: जिन providers की खिड़की बीत गई, उनका उपयोग शून्य
      const provs = (await db.prepare("SELECT * FROM provider_state").all<Provider & { reset_rule: string }>()).results;
      for (const p of provs) {
        if (Date.parse(p.window_reset_utc) <= Date.parse(now)) {
          await db.prepare("UPDATE provider_state SET used = 0, window_reset_utc = ?, updated_at = ? WHERE provider = ?")
            .bind(nextReset(p.reset_rule, now), now, p.provider).run();
          p.used = 0;
        }
      }

      // स्वार्म की घड़ी: हर समय-खाँचे में संचालक का एक चक्कर कतार में (पहले से कोई कतार में या चलता हो तो नहीं)।
      // संचालक GitHub Actions में चलता है और repo की कतार (swarm/BACKLOG.json) से अगला काम चुनकर यहीं enqueue करता है।
      const pendingConduct = await db.prepare("SELECT 1 AS x FROM jobs WHERE step = 'conduct' AND status IN ('queued','running') LIMIT 1").first();
      if (!pendingConduct) {
        const c = await this.enqueue("swarm", conductBatch(now), "conduct");
        if ("created" in c && c.created) {
          // बही छोटी रहे: संचालक के दो दिन से पुराने, निपट चुके चक्कर हटें
          await db.prepare("DELETE FROM jobs WHERE step = 'conduct' AND status IN ('done','needs_expert') AND updated_at < ?")
            .bind(new Date(Date.parse(now) - 2 * 86400 * 1000).toISOString()).run();
        }
      }

      const jobs = (await db.prepare(
        "SELECT job_key, text_id, batch_id, step, lane, status, provider, attempts, started_at, updated_at FROM jobs WHERE status IN ('queued','running','waiting_reset','failed') ORDER BY updated_at LIMIT 200",
      ).all<Job>()).results;

      const actions = planTick(jobs, provs, now, false, DEFAULT_LIMITS);
      for (const a of actions) {
        if (a.kind === "dispatch") await this.dispatch(a.job, now);
        else if (a.kind === "timeout") {
          const to: JobStatus = a.requeue ? "queued" : "needs_expert";
          await this.move(a.job, "failed", now, "timeout");
          await this.move({ ...a.job, status: "failed" }, to, now, a.requeue ? "retry" : "retry-सीमा पार");
        } else if (a.kind === "retry") {
          await this.move(a.job, a.requeue ? "queued" : "needs_expert", now, a.requeue ? "retry" : "retry-सीमा पार");
        } else if (a.kind === "sleep") await this.move(a.job, "waiting_reset", now, a.reason);
        else if (a.kind === "wake") await this.move(a.job, "queued", now, "reset हुआ");
      }
      this.setState({ ...this.state, lastTick: now, lastTickSource: source, lastActions: actions.length, consecutiveErrors: 0 });
      return { actions: actions.length, stopped: false };
    } catch (e) {
      const n = this.state.consecutiveErrors + 1;
      await this.event("error", "tick", String(e).slice(0, 500));
      // लगातार 3 विफलताएँ → अपने-आप रुकें (मास्टर योजना §5.3 Foreman escalation)
      this.setState({ ...this.state, lastTick: now, lastTickSource: source, consecutiveErrors: n,
        stopped: n >= 3 ? true : this.state.stopped, stopReason: n >= 3 ? "लगातार 3 tick-विफलताएँ" : this.state.stopReason });
      return { actions: 0, stopped: n >= 3 };
    }
  }

  private async stopFileExists(): Promise<boolean> {
    const r = await fetch(`https://raw.githubusercontent.com/${this.env.GITHUB_REPO}/main/swarm/STOP`, {
      headers: { "user-agent": "sanatan-granth-foreman" }, cf: { cacheTtl: 120 },
    } as RequestInit);
    return r.status === 200;
  }

  private async event(kind: string, ref: string | null, detail: string | null): Promise<void> {
    await this.env.LEDGER.prepare("INSERT INTO events (ts, kind, ref, detail) VALUES (?, ?, ?, ?)")
      .bind(nowIso(), kind, ref, detail).run();
  }

  /** अवस्था-बदलाव केवल validateJobTransition से; WHERE status = पुरानी अवस्था → दौड़ में दोहराव no-op। */
  private async move(job: Job, to: JobStatus, now: string, note: string | null): Promise<boolean> {
    if (!validateJobTransition(job.status, to)) {
      await this.event("error", job.job_key, `अवैध बदलाव ${job.status} → ${to}`);
      return false;
    }
    const r = await this.env.LEDGER.prepare(
      "UPDATE jobs SET status = ?, updated_at = ?, error = CASE WHEN ? IN ('failed','needs_expert','waiting_reset') THEN ? ELSE error END WHERE job_key = ? AND status = ?",
    ).bind(to, now, to, note, job.job_key, job.status).run();
    return (r.meta.changes ?? 0) > 0;
  }

  private async dispatch(job: Job, now: string): Promise<void> {
    if (!this.state.publicOrigin) {
      await this.event("error", job.job_key, "publicOrigin अज्ञात: पहले /status खोलें");
      return;
    }
    // पहले बही में 'running' (शर्त: अभी भी queued) → तभी बाहर dispatch; दो ticks एक ही job दो बार नहीं भेज सकते
    const claimed = await this.env.LEDGER.prepare(
      "UPDATE jobs SET status = 'running', started_at = ?, updated_at = ?, attempts = attempts + 1 WHERE job_key = ? AND status = 'queued'",
    ).bind(now, now, job.job_key).run();
    if ((claimed.meta.changes ?? 0) === 0) return;
    const r = await fetch(`https://api.github.com/repos/${this.env.GITHUB_REPO}/dispatches`, {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.env.GITHUB_DISPATCH_TOKEN}`,
        accept: "application/vnd.github+json",
        "user-agent": "sanatan-granth-foreman",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        event_type: "foreman-job",
        client_payload: {
          job_key: job.job_key, step: job.step, text_id: job.text_id, batch_id: job.batch_id,
          callback_url: `${this.state.publicOrigin}/callback`,
        },
      }),
    });
    if (r.status === 204) {
      if (job.provider) {
        await this.env.LEDGER.prepare("UPDATE provider_state SET used = used + 1, updated_at = ? WHERE provider = ?")
          .bind(now, job.provider).run();
      }
      await this.event("dispatch", job.job_key, `${job.step} ${job.text_id}/${job.batch_id}`);
    } else {
      await this.move({ ...job, status: "running" }, "failed", now, `dispatch HTTP ${r.status}`);
      await this.event("error", job.job_key, `dispatch HTTP ${r.status}`);
    }
  }

  // ---- Worker से बुलाए जाने वाले RPC-तरीक़े ----

  async noteOrigin(origin: string): Promise<void> {
    if (this.state.publicOrigin !== origin) this.setState({ ...this.state, publicOrigin: origin });
  }

  async callback(body: { job_key: string; status: string; result_ref?: string; duration_s?: number }): Promise<{ ok: boolean }> {
    const now = nowIso();
    const to: JobStatus = body.status === "done" ? "done" : "failed";
    const row = await this.env.LEDGER.prepare("SELECT job_key, status, attempts FROM jobs WHERE job_key = ?")
      .bind(body.job_key).first<{ job_key: string; status: JobStatus; attempts: number }>();
    if (!row) return { ok: false };
    if (row.status !== "running") return { ok: true }; // दोहराया callback: no-op
    await this.env.LEDGER.prepare(
      "UPDATE jobs SET status = ?, updated_at = ?, duration_s = ?, result_ref = ? WHERE job_key = ? AND status = 'running'",
    ).bind(to, now, body.duration_s ?? null, body.result_ref ?? null, body.job_key).run();
    if (to === "failed") {
      // retry-सीमा के भीतर दोबारा कतार में, वरना needs_expert (D)
      const next: JobStatus = row.attempts < DEFAULT_LIMITS.maxRetryPerStep + 1 ? "queued" : "needs_expert";
      await this.env.LEDGER.prepare("UPDATE jobs SET status = ?, updated_at = ? WHERE job_key = ? AND status = 'failed'")
        .bind(next, now, body.job_key).run();
    }
    await this.event("callback", body.job_key, `${to} ${body.result_ref ?? ""}`);
    return { ok: true };
  }

  async enqueueNoop(batchId: string): Promise<{ job_key: string; created: boolean }> {
    const key = await jobKey("selftest", batchId, "noop", "none", "none");
    const now = nowIso();
    const r = await this.env.LEDGER.prepare(
      "INSERT OR IGNORE INTO jobs (job_key, text_id, batch_id, step, lane, status, updated_at) VALUES (?, 'selftest', ?, 'noop', 'selftest', 'queued', ?)",
    ).bind(key, batchId, now).run();
    return { job_key: key, created: (r.meta.changes ?? 0) > 0 };
  }

  /** अनुमत step का एक job कतार में (idempotent: वही corpus/batch/step दोबारा डालने पर नया job नहीं बनता)। */
  async enqueue(textId: string, batchId: string, step: string): Promise<{ job_key: string; created: boolean } | { error: string }> {
    const spec = ENQUEUEABLE[step];
    if (!spec) return { error: "step अनुमत नहीं" };
    const key = await jobKey(textId, batchId, step, spec.promptHash, spec.model);
    const now = nowIso();
    const r = await this.env.LEDGER.prepare(
      "INSERT OR IGNORE INTO jobs (job_key, text_id, batch_id, step, lane, status, prompt_hash, model, updated_at) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?)",
    ).bind(key, textId, batchId, step, spec.lane, spec.promptHash, spec.model, now).run();
    return { job_key: key, created: (r.meta.changes ?? 0) > 0 };
  }

  async setStop(stop: boolean, reason: string): Promise<void> {
    this.setState({ ...this.state, stopped: stop, stopReason: stop ? reason : null, consecutiveErrors: 0 });
    await this.event("stop", null, `${stop ? "रोका" : "चालू"}: ${reason}`);
  }

  async status(): Promise<Record<string, unknown>> {
    const db = this.env.LEDGER;
    const jobs = (await db.prepare("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status").all<{ status: string; n: number }>()).results;
    const books = (await db.prepare("SELECT state, COUNT(*) AS n FROM books GROUP BY state").all<{ state: string; n: number }>()).results;
    const provs = (await db.prepare("SELECT provider, unit, limit_per_window, used, window_reset_utc, breaker_open FROM provider_state").all()).results;
    const recent = (await db.prepare("SELECT ts, kind, ref, detail FROM events ORDER BY id DESC LIMIT 15").all()).results;
    return {
      now: nowIso(), last_tick: this.state.lastTick, last_tick_source: this.state.lastTickSource,
      stopped: this.state.stopped, stop_reason: this.state.stopReason, consecutive_errors: this.state.consecutiveErrors,
      jobs: Object.fromEntries(jobs.map((j) => [j.status, j.n])),
      books: Object.fromEntries(books.map((b) => [b.state, b.n])),
      providers: provs, recent_events: recent,
    };
  }

  async exportJobs(): Promise<unknown[]> {
    return (await this.env.LEDGER.prepare("SELECT * FROM jobs ORDER BY updated_at DESC LIMIT 5000").all()).results;
  }
}

// ---------------------------------------------------------------- Worker

const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj, null, 2), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

function statusHtml(s: Record<string, unknown>): string {
  const stopped = Boolean(s.stopped);
  const row = (k: string, v: unknown) => `<tr><th>${esc(k)}</th><td>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</td></tr>`;
  const events = (s.recent_events as Array<Record<string, unknown>>).map((e) => `<li><code>${esc(e.ts)}</code> ${esc(e.kind)} ${esc(e.detail)}</li>`).join("");
  return `<!doctype html><html lang="hi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Foreman स्थिति</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:24px auto;padding:0 16px;background:#fffdf8;color:#1f1a14}
th{text-align:left;padding-right:16px;vertical-align:top}.b{display:inline-block;padding:4px 12px;border-radius:6px;color:#fff;background:${stopped ? "#b3261e" : "#1b6e3c"}}
@media(prefers-color-scheme:dark){body{background:#17140f;color:#eee6d8}}</style>
<h1>sanatan-granth · Foreman</h1><p><span class="b">${stopped ? "रुका हुआ" : "चालू"}</span> ${esc(s.stop_reason ?? "")}</p>
<table>${row("अभी (UTC)", s.now)}${row("पिछला tick", s.last_tick)}${row("tick का स्रोत", s.last_tick_source)}${row("jobs", s.jobs)}${row("ग्रंथ", s.books)}${row("providers", s.providers)}</table>
<h2>हाल की घटनाएँ</h2><ul>${events || "<li>कोई नहीं</li>"}</ul>
<p><small>यह केवल मशीन की प्रक्रिया-स्थिति है। यहाँ कोई त्रुटि-दर या सत्यापन का दावा नहीं है।</small></p></html>`;
}

async function signed(req: Request, env: Env): Promise<string | null> {
  const body = await req.text();
  const sig = req.headers.get("x-foreman-signature") ?? "";
  const want = await hmacHex(env.FOREMAN_SHARED_SECRET, body);
  return timingSafeEqual(sig, want) ? body : null;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const foreman = await getAgentByName<Env, ForemanAgent>(env.FOREMAN, "main");

    if (req.method === "GET" && (url.pathname === "/status" || url.pathname === "/status.json" || url.pathname === "/")) {
      await foreman.noteOrigin(url.origin);
      const s = await foreman.status();
      return url.pathname === "/status.json" ? json(s)
        : new Response(statusHtml(s), { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
    }

    if (req.method === "POST" && url.pathname === "/callback") {
      const body = await signed(req, env);
      if (body === null) return json({ error: "हस्ताक्षर अमान्य" }, 401);
      const b = JSON.parse(body) as { job_key: string; status: string; result_ref?: string; duration_s?: number };
      if (!/^[0-9a-f]{64}$/.test(b.job_key ?? "")) return json({ error: "job_key अमान्य" }, 400);
      return json(await foreman.callback(b));
    }

    if (req.method === "POST" && url.pathname.startsWith("/admin/")) {
      const body = await signed(req, env);
      if (body === null) return json({ error: "हस्ताक्षर अमान्य" }, 401);
      const b = (body ? JSON.parse(body) : {}) as Record<string, string>;
      if (url.pathname === "/admin/enqueue-noop") {
        if (!/^[A-Za-z0-9_.:-]{1,80}$/.test(b.batch_id ?? "")) return json({ error: "batch_id अमान्य" }, 400);
        return json(await foreman.enqueueNoop(b.batch_id));
      }
      if (url.pathname === "/admin/enqueue") {
        if (!/^[a-z][a-z0-9_]{0,40}$/.test(b.text_id ?? "")) return json({ error: "text_id अमान्य" }, 400);
        if (!/^[A-Za-z0-9_.:-]{1,80}$/.test(b.batch_id ?? "")) return json({ error: "batch_id अमान्य" }, 400);
        const r = await foreman.enqueue(b.text_id, b.batch_id, b.step ?? "");
        return json(r, "error" in r ? 400 : 200);
      }
      if (url.pathname === "/admin/tick") return json(await foreman.tick("admin"));
      if (url.pathname === "/admin/stop") { await foreman.setStop(true, (b.reason ?? "admin").slice(0, 200)); return json({ ok: true }); }
      if (url.pathname === "/admin/resume") { await foreman.setStop(false, (b.reason ?? "admin").slice(0, 200)); return json({ ok: true }); }
      if (url.pathname === "/admin/export-jobs") return json(await foreman.exportJobs());
    }
    return json({ error: "नहीं मिला" }, 404);
  },

  // dead-man's switch: एक असली Cron Trigger, जो Foreman को जगाए अगर DO के alarms अटक जाएँ।
  async scheduled(_event: ScheduledController, env: Env): Promise<void> {
    const foreman = await getAgentByName<Env, ForemanAgent>(env.FOREMAN, "main");
    const s = (await foreman.status()) as { last_tick: string | null };
    const stale = !s.last_tick || Date.now() - Date.parse(s.last_tick) > 2 * TICK_SECONDS * 1000;
    if (stale) await foreman.tick("dead-man-cron");
  },
} satisfies ExportedHandler<Env>;
