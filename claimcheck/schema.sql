-- ClaimCheck evaluation storage. Idempotent: safe to run repeatedly.

CREATE TABLE IF NOT EXISTS runs (
    run_id            UUID PRIMARY KEY,
    split             TEXT NOT NULL CHECK (split IN ('development', 'check')),
    agent_version     TEXT NOT NULL CHECK (agent_version IN ('v1', 'v2')),
    prompt_version    TEXT NOT NULL,
    dataset_version   TEXT NOT NULL,
    evaluator_version TEXT NOT NULL,
    fact_version      TEXT NOT NULL,
    provider          TEXT NOT NULL,
    model             TEXT NOT NULL,
    settings          JSONB NOT NULL,
    source_revision   TEXT,
    file_hashes       JSONB NOT NULL,
    status            TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    counts            JSONB,
    metrics           JSONB,          -- NULL for check runs
    scoring           JSONB,          -- missed / extra / wrong-label IDs (development only)
    error             TEXT,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS answer_results (
    run_id        UUID NOT NULL REFERENCES runs (run_id) ON DELETE CASCADE,
    answer_id     TEXT NOT NULL,
    position      INTEGER NOT NULL,
    brand_id      TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_type    TEXT,
    error_message TEXT,
    claim_count   INTEGER NOT NULL DEFAULT 0 CHECK (claim_count >= 0),
    latency_ms    INTEGER,
    model_turns   INTEGER,
    tool_calls    JSONB NOT NULL DEFAULT '[]'::jsonb,
    usage         JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_ref     TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, answer_id),
    CHECK ((status = 'error') = (error_type IS NOT NULL)),
    CHECK (status = 'ok' OR claim_count = 0)
);

CREATE TABLE IF NOT EXISTS claim_results (
    id             BIGSERIAL PRIMARY KEY,
    run_id         UUID NOT NULL,
    answer_id      TEXT NOT NULL,
    claim_id       TEXT NOT NULL,
    start_char     INTEGER NOT NULL CHECK (start_char >= 0),
    end_char       INTEGER NOT NULL,
    quote          TEXT NOT NULL,
    label          TEXT NOT NULL CHECK (label IN ('supported', 'contradicted', 'unknown')),
    fact_ids       JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason         TEXT NOT NULL,
    matched_gold   BOOLEAN,           -- development only; NULL for check runs
    expected_label TEXT,              -- development only
    label_correct  BOOLEAN,           -- development only
    FOREIGN KEY (run_id, answer_id) REFERENCES answer_results (run_id, answer_id) ON DELETE CASCADE,
    UNIQUE (run_id, answer_id, start_char, end_char),
    UNIQUE (run_id, claim_id),
    CHECK (end_char > start_char)
);

CREATE INDEX IF NOT EXISTS claim_results_run_order ON claim_results (run_id, answer_id, start_char);
