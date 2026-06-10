CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- EVENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    center_lat DOUBLE PRECISION NOT NULL,
    center_lon DOUBLE PRECISION NOT NULL,
    radius_km DOUBLE PRECISION NOT NULL DEFAULT 20.0,

    status TEXT NOT NULL DEFAULT 'active',
    is_finished BOOLEAN NOT NULL DEFAULT FALSE,
    finished_at TIMESTAMP NULL,

    tweet_count INTEGER NOT NULL DEFAULT 0,
    latest_tweet_text TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- TWEETS
-- =====================================================

CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,

    event_id UUID REFERENCES events(id) ON DELETE SET NULL,

    text TEXT NOT NULL,
    source TEXT DEFAULT 'twitter',

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- PIPELINE RUNS
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tweet_id TEXT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,

    pipeline_config TEXT NOT NULL DEFAULT 'fire_pipeline_v1',

    status TEXT NOT NULL DEFAULT 'passed',
    stopped_at TEXT,

    final_lat DOUBLE PRECISION,
    final_lon DOUBLE PRECISION,

    raw_json JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- PIPELINE STEPS
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    run_id UUID NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,

    step_id TEXT NOT NULL,
    step_name TEXT NOT NULL,

    status TEXT NOT NULL,
    description TEXT,

    duration_ms INTEGER,

    output JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    step_order INTEGER NOT NULL,

    UNIQUE(run_id, step_id)
);

-- =====================================================
-- STEP ANNOTATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS step_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    pipeline_step_id UUID NOT NULL REFERENCES pipeline_steps(id) ON DELETE CASCADE,

    label TEXT NOT NULL CHECK (
        label IN ('correct', 'incorrect', 'uncertain')
    ),

    annotated_by TEXT DEFAULT 'mathias',

    notes TEXT,

    annotated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(pipeline_step_id, annotated_by)
);

-- =====================================================
-- DEMO DATA
-- =====================================================

WITH inserted_event AS (

    INSERT INTO events (
        center_lat,
        center_lon,
        radius_km,
        status,
        tweet_count,
        latest_tweet_text
    )
    VALUES (
        43.5081,
        16.4402,
        20.0,
        'active',
        1,
        'Smoke visible near Marjan hill in Split'
    )
    RETURNING id

),

inserted_tweet AS (

    INSERT INTO tweets (
        id,
        event_id,
        text,
        source
    )
    SELECT
        'tweet_001',
        inserted_event.id,
        'Smoke visible near Marjan hill in Split',
        'twitter'
    FROM inserted_event
    RETURNING id

),

inserted_run AS (

    INSERT INTO pipeline_runs (
        tweet_id,
        pipeline_config,
        status,
        final_lat,
        final_lon
    )
    SELECT
        inserted_tweet.id,
        'fire_pipeline_v1',
        'passed',
        43.508,
        16.408
    FROM inserted_tweet
    RETURNING id

),

inserted_relevance_step AS (

    INSERT INTO pipeline_steps (
        run_id,
        step_id,
        step_name,
        status,
        description,
        duration_ms,
        output
    )
    SELECT
        inserted_run.id,
        'relevance',
        'Relevance',
        'success',
        'Tweet classified as relevant wildfire signal.',
        42,
        '{
            "label": "low_signal",
            "confidence": 0.91
        }'::jsonb
    FROM inserted_run
    RETURNING id

),

inserted_geocoding_step AS (

    INSERT INTO pipeline_steps (
        run_id,
        step_id,
        step_name,
        status,
        description,
        duration_ms,
        output
    )
    SELECT
        inserted_run.id,
        'geocoding',
        'Geocoding',
        'success',
        'Location resolved with Photon.',
        121,
        '{
            "best_location": "Marjan hill",
            "lat": 43.508,
            "lon": 16.408
        }'::jsonb
    FROM inserted_run
    RETURNING id

)

INSERT INTO step_annotations (
    pipeline_step_id,
    label,
    annotated_by,
    notes
)

SELECT
    inserted_geocoding_step.id,
    'correct',
    'mathias',
    'Correct geocoding resolution'
FROM inserted_geocoding_step

ON CONFLICT DO NOTHING;