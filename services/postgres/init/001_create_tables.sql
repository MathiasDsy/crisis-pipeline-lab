CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- DATASETS
-- =====================================================

CREATE TABLE IF NOT EXISTS datasets (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name               TEXT NOT NULL,
    path               TEXT NOT NULL,
    hash               TEXT NOT NULL UNIQUE,
    is_valid           BOOLEAN NOT NULL DEFAULT FALSE,
    validation_errors  JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- MODEL REGISTRY
-- =====================================================

CREATE TABLE IF NOT EXISTS model_registry (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_key                TEXT NOT NULL UNIQUE,
    name                     TEXT NOT NULL,
    version                  TEXT NOT NULL,
    model_type               TEXT NOT NULL,
    compatible_components_key JSONB NOT NULL DEFAULT '[]'::jsonb,
    local_path               TEXT NOT NULL,
    is_available             BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- PIPELINE CONFIGS
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_configs (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                     TEXT NOT NULL,
    version                  TEXT NOT NULL DEFAULT '1.0.0',
    description              TEXT,
    config_json              JSONB NOT NULL DEFAULT '{}'::jsonb,
    required_models_json     JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_components_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    original_filename        TEXT,
    config_hash              TEXT NOT NULL UNIQUE,
    is_valid                 BOOLEAN NOT NULL DEFAULT FALSE,
    validation_errors        JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- EVENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS events (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id           UUID NULL,
    center_lat       DOUBLE PRECISION,
    center_lon       DOUBLE PRECISION,
    radius_km        DOUBLE PRECISION NOT NULL DEFAULT 20.0,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    finished_at      TIMESTAMP NULL,
    tweet_count      INTEGER NOT NULL DEFAULT 0,
    latest_tweet_text TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- BENCHMARKS
-- =====================================================

CREATE TABLE IF NOT EXISTS benchmarks (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                  TEXT,
    dataset_id            UUID NULL REFERENCES datasets(id) ON DELETE SET NULL,
    classifier_model_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    location_model_keys   JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_runs            INTEGER NOT NULL DEFAULT 0,
    completed_runs        INTEGER NOT NULL DEFAULT 0,
    status                TEXT NOT NULL DEFAULT 'running',
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at           TIMESTAMP NULL
);

-- =====================================================
-- PIPELINE RUNS
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_config_id   UUID NULL REFERENCES pipeline_configs(id) ON DELETE SET NULL,
    dataset_id           UUID NULL REFERENCES datasets(id) ON DELETE SET NULL,
    benchmark_id         UUID NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
    mode                 TEXT NOT NULL DEFAULT 'simulation',
    status               TEXT NOT NULL DEFAULT 'running',
    started_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at          TIMESTAMP NULL,
    model_snapshot_json  JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_benchmark_id ON pipeline_runs(benchmark_id);

-- =====================================================
-- TWEETS
-- =====================================================

CREATE TABLE IF NOT EXISTS tweets (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id   UUID NULL REFERENCES events(id) ON DELETE SET NULL,
    run_id     UUID NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'dataset',
    label      BOOLEAN NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- PIPELINE STEP EXECUTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_step_executions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id      UUID NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    tweet_id    UUID NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
    step_name   TEXT NOT NULL,
    status      TEXT NOT NULL,
    duration_ms DOUBLE PRECISION,
    input_json  JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    step_index  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_step_exec_run_id   ON pipeline_step_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_step_exec_tweet_id ON pipeline_step_executions(tweet_id);

-- =====================================================
-- RUN METRICS
-- =====================================================

CREATE TABLE IF NOT EXISTS run_metrics (
    run_id         UUID PRIMARY KEY REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    total_tweets   INTEGER NOT NULL DEFAULT 0,
    labeled_tweets INTEGER NOT NULL DEFAULT 0,
    tp             INTEGER NOT NULL DEFAULT 0,
    fp             INTEGER NOT NULL DEFAULT 0,
    fn             INTEGER NOT NULL DEFAULT 0,
    tn             INTEGER NOT NULL DEFAULT 0,
    precision      DOUBLE PRECISION NOT NULL DEFAULT 0,
    recall         DOUBLE PRECISION NOT NULL DEFAULT 0,
    f1             DOUBLE PRECISION NOT NULL DEFAULT 0,
    accuracy       DOUBLE PRECISION NOT NULL DEFAULT 0,
    computed_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- RUN LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS run_logs (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id     UUID NULL,
    level      TEXT NOT NULL DEFAULT 'info',
    context    TEXT NOT NULL DEFAULT '',
    message    TEXT NOT NULL,
    details    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_run_logs_run_id ON run_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_run_logs_level  ON run_logs(level);
