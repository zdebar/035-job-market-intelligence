BEGIN;

ALTER TABLE job_posting_sources
    ADD COLUMN selection_rank INTEGER;

ALTER TABLE job_posting_sources
    ADD CONSTRAINT job_posting_sources_selection_rank_check
    CHECK (selection_rank IS NULL OR selection_rank >= 1);

CREATE UNIQUE INDEX job_posting_sources_canonical_rank_idx
    ON job_posting_sources (canonical_job_id, selection_rank)
    WHERE selection_rank IS NOT NULL;

WITH ranked AS (
    SELECT
        links.job_posting_id,
        CASE
                        WHEN postings.status = 'active' THEN ROW_NUMBER() OVER (
                            PARTITION BY links.canonical_job_id
                ORDER BY
                    (postings.status = 'active') DESC,
                    COALESCE(postings.source_updated_at, postings.retrieved_at)
                        DESC NULLS LAST,
                    (
                        CASE WHEN postings.role_id IS NOT NULL THEN 1 ELSE 0 END
                        + CASE WHEN postings.seniority_level_id IS NOT NULL THEN 1 ELSE 0 END
                        + CASE WHEN postings.source_url IS NOT NULL THEN 1 ELSE 0 END
                        + CASE WHEN EXISTS (
                            SELECT 1
                            FROM job_posting_locations locations
                            WHERE locations.job_posting_id = postings.id
                        ) THEN 1 ELSE 0 END
                        + CASE WHEN EXISTS (
                            SELECT 1
                            FROM job_posting_work_modes work_modes
                            WHERE work_modes.job_posting_id = postings.id
                        ) THEN 1 ELSE 0 END
                        + CASE WHEN EXISTS (
                            SELECT 1
                            FROM job_skill_requirements skills
                            WHERE skills.job_posting_id = postings.id
                        ) THEN 1 ELSE 0 END
                        + CASE WHEN EXISTS (
                            SELECT 1
                            FROM job_posting_compensations compensation
                            WHERE compensation.job_posting_id = postings.id
                        ) THEN 1 ELSE 0 END
                        + CASE WHEN EXISTS (
                            SELECT 1
                            FROM job_posting_employment_options employment
                            WHERE employment.job_posting_id = postings.id
                        ) THEN 1 ELSE 0 END
                    ) DESC,
                    postings.id ASC
            )::INTEGER
            ELSE NULL
        END AS selection_rank
    FROM job_posting_sources links
    JOIN job_postings postings ON postings.id = links.job_posting_id
)
UPDATE job_posting_sources links
SET selection_rank = ranked.selection_rank
FROM ranked
WHERE links.job_posting_id = ranked.job_posting_id;

COMMIT;
