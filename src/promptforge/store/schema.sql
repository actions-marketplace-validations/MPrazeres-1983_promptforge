-- PromptForge SQLite Schema

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    prompt_id       TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,
    prompt_hash     TEXT NOT NULL,
    dataset_id      TEXT NOT NULL,
    dataset_hash    TEXT NOT NULL,
    model           TEXT NOT NULL,
    provider        TEXT NOT NULL,
    params_json     TEXT NOT NULL,
    total_cases     INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    started_at      TEXT NOT NULL,
    finished_at     TEXT
);

CREATE TABLE IF NOT EXISTS case_results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              TEXT NOT NULL,
    case_id             TEXT NOT NULL,
    input_json          TEXT NOT NULL,
    output_raw          TEXT NOT NULL,
    output_parsed_json  TEXT,
    latency_ms          REAL NOT NULL,
    tokens_in           INTEGER DEFAULT 0,
    tokens_out          INTEGER DEFAULT 0,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    case_id         TEXT NOT NULL,
    evaluator       TEXT NOT NULL,
    dimension       TEXT NOT NULL,
    score           REAL NOT NULL,
    rationale       TEXT DEFAULT '',
    metadata_json   TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_case_results_run ON case_results(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_run ON scores(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_evaluator ON scores(run_id, evaluator);