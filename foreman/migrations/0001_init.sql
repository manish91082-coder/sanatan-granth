-- Cloudflare D1: साझा बही-खाता (मास्टर योजना §5.2, क़दम 0.11)
-- नियम: प्रति अध्याय/batch एक job-पंक्ति; प्रति श्लोक कभी नहीं। पाठ यहाँ नहीं, git/Drive में।

CREATE TABLE IF NOT EXISTS books (
  text_id        TEXT PRIMARY KEY,
  work_id        TEXT NOT NULL,
  state          TEXT NOT NULL DEFAULT 'CATALOGUED',
  phase          INTEGER NOT NULL DEFAULT 1,
  priority       REAL NOT NULL DEFAULT 0,
  pipeline_version TEXT,
  segments_total INTEGER,
  segments_c     INTEGER NOT NULL DEFAULT 0,
  segments_d     INTEGER NOT NULL DEFAULT 0,
  paused         INTEGER NOT NULL DEFAULT 0,
  updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  job_key     TEXT PRIMARY KEY,          -- sha256(corpus, batch_id, step, prompt_hash, model)
  text_id     TEXT NOT NULL,
  batch_id    TEXT NOT NULL,
  step        TEXT NOT NULL,
  lane        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|waiting_reset|needs_expert
  provider    TEXT,
  model       TEXT,
  prompt_hash TEXT,
  attempts    INTEGER NOT NULL DEFAULT 0,
  segments    INTEGER,
  started_at  TEXT,
  updated_at  TEXT NOT NULL,
  duration_s  REAL,
  result_ref  TEXT,
  error       TEXT
);
CREATE INDEX IF NOT EXISTS jobs_status_lane ON jobs (status, lane);
CREATE INDEX IF NOT EXISTS jobs_text ON jobs (text_id, step);

CREATE TABLE IF NOT EXISTS provider_state (
  provider     TEXT PRIMARY KEY,
  unit         TEXT NOT NULL,              -- requests | neurons | gpu_hours | runs
  limit_per_window REAL NOT NULL,          -- console में देखी गई सीमा (policy/quotas.md)
  used         REAL NOT NULL DEFAULT 0,
  window_reset_utc TEXT NOT NULL,          -- अगला reset (ISO)
  reset_rule   TEXT NOT NULL,              -- utc_midnight | pacific_midnight | weekly_sat | daily
  breaker_open INTEGER NOT NULL DEFAULT 0,
  breaker_reason TEXT,
  updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  ts     TEXT NOT NULL,
  kind   TEXT NOT NULL,                    -- tick | dispatch | callback | stop | breaker | error | heartbeat
  ref    TEXT,
  detail TEXT
);
CREATE INDEX IF NOT EXISTS events_ts ON events (ts);
