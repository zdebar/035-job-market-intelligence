BEGIN;

-- Salary may have multiple ranges per posting and may differ by employment relation.
CREATE TABLE job_posting_compensations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    employment_relation_id BIGINT REFERENCES employment_relations(id),
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_currency TEXT,
    salary_period TEXT,
    CHECK (salary_min IS NOT NULL OR salary_max IS NOT NULL),
    CHECK (salary_min IS NULL OR salary_min >= 0),
    CHECK (salary_max IS NULL OR salary_max >= 0),
    CHECK (
        salary_min IS NULL
        OR salary_max IS NULL
        OR salary_max >= salary_min
    ),
    CHECK (
        salary_currency IS NULL
        OR salary_currency ~ '^[A-Z]{3}$'
    ),
    CHECK (
        salary_period IS NULL
        OR salary_period IN ('hour', 'day', 'week', 'month', 'year', 'project')
    )
);

CREATE INDEX job_posting_compensations_posting_id_idx
    ON job_posting_compensations (job_posting_id);

CREATE INDEX job_posting_compensations_relation_id_idx
    ON job_posting_compensations (employment_relation_id);

-- Keep database limits aligned with config/validation.toml.
ALTER TABLE job_posting_employment_options
    ADD CONSTRAINT job_posting_employment_options_hours_minimum_check
    CHECK (
        hours_min IS NULL
        OR hours_min <= CASE hours_period
            WHEN 'day' THEN 24
            WHEN 'week' THEN 168
            WHEN 'month' THEN 744
            WHEN 'year' THEN 8784
            ELSE 8784
        END
    ),
    ADD CONSTRAINT job_posting_employment_options_hours_maximum_check
    CHECK (
        hours_max IS NULL
        OR hours_max <= CASE hours_period
            WHEN 'day' THEN 24
            WHEN 'week' THEN 168
            WHEN 'month' THEN 744
            WHEN 'year' THEN 8784
            ELSE 8784
        END
    );

COMMIT;
