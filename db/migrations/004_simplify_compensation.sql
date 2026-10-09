BEGIN;

-- Salary is currently modeled as one optional generic range per posting.
DROP INDEX IF EXISTS job_posting_compensations_relation_id_idx;

ALTER TABLE job_posting_compensations
    DROP COLUMN employment_relation_id,
    ADD CONSTRAINT job_posting_compensations_posting_unique
    UNIQUE (job_posting_id);

COMMIT;
