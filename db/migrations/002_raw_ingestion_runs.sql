BEGIN;

-- Processing state for a raw download. The source_id identifies an adapter,
-- for example greenhouse; it is intentionally not a foreign key to sources.
CREATE TABLE raw_ingestion_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ,
    record_count INTEGER,
    payload_sha256 TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    processed_records INTEGER NOT NULL DEFAULT 0,
    parser_version TEXT,
    error_message TEXT,
    processing_started_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, run_id),
    CHECK (status IN ('pending', 'processing', 'processed', 'failed')),
    CHECK (record_count IS NULL OR record_count >= 0),
    CHECK (processed_records >= 0)
);

CREATE INDEX raw_ingestion_runs_status_idx
    ON raw_ingestion_runs (status);

CREATE INDEX raw_ingestion_runs_source_id_idx
    ON raw_ingestion_runs (source_id);

COMMIT;
