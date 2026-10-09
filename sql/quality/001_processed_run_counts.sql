-- Quality check: every processed raw run must persist all records it parsed.
-- The first query is the report. The DO block makes the check fail on mismatch.

SELECT
    status,
    COUNT(*) AS runs,
    COALESCE(SUM(record_count), 0) AS downloaded_records,
    COALESCE(SUM(processed_records), 0) AS processed_records
FROM raw_ingestion_runs
GROUP BY status
ORDER BY status;

SELECT
    source_id,
    run_id,
    record_count,
    processed_records
FROM raw_ingestion_runs
WHERE status = 'processed'
  AND record_count IS NOT NULL
  AND record_count <> processed_records
ORDER BY source_id, run_id;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM raw_ingestion_runs
        WHERE status = 'processed'
          AND record_count IS NOT NULL
          AND record_count <> processed_records
    ) THEN
        RAISE EXCEPTION 'Processed record count does not match raw record count';
    END IF;
END;
$$;
