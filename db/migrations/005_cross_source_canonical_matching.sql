BEGIN;

ALTER TABLE sources ADD COLUMN source_key TEXT;

UPDATE sources
SET source_key = CASE name
    WHEN 'Mews' THEN 'greenhouse_mews'
    WHEN 'Second Foundation Tech' THEN 'greenhouse_second_foundation_tech'
    ELSE lower(regexp_replace(name, '[^a-zA-Z0-9]+', '_', 'g'))
END
WHERE source_key IS NULL;

ALTER TABLE sources
    ALTER COLUMN source_key SET NOT NULL,
    ADD CONSTRAINT sources_source_key_key UNIQUE (source_key);

INSERT INTO sources (name, source_key)
VALUES
    ('Ataccama', 'lever_ataccama'),
    ('Apify', 'ashby_apify')
ON CONFLICT (source_key) DO NOTHING;

ALTER TABLE job_postings ADD COLUMN content_fingerprint TEXT;

ALTER TABLE job_postings
    ADD CONSTRAINT job_postings_content_fingerprint_check
    CHECK (content_fingerprint IS NULL OR content_fingerprint ~ '^[0-9a-f]{64}$');

CREATE INDEX job_postings_content_fingerprint_idx
    ON job_postings (content_fingerprint);

ALTER TABLE job_posting_sources
    ADD COLUMN match_method TEXT NOT NULL DEFAULT 'new_canonical_job',
    ADD COLUMN matched_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE job_posting_sources
    ADD CONSTRAINT job_posting_sources_match_method_check
    CHECK (match_method IN ('new_canonical_job', 'algorithmic_match', 'llm_match', 'manual_match'));

ALTER TABLE raw_ingestion_runs
    DROP CONSTRAINT raw_ingestion_runs_status_check,
    ADD CONSTRAINT raw_ingestion_runs_status_check
    CHECK (status IN ('pending', 'processing', 'processed', 'partial', 'failed'));

CREATE TABLE raw_ingestion_record_errors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    raw_ingestion_run_id BIGINT NOT NULL REFERENCES raw_ingestion_runs(id) ON DELETE CASCADE,
    source_job_id TEXT,
    stage TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX raw_ingestion_record_errors_run_id_idx
    ON raw_ingestion_record_errors (raw_ingestion_run_id);

COMMIT;
