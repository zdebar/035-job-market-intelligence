BEGIN;

-- Source boards used for ingestion. Example: Mews or Second Foundation Tech.
CREATE TABLE sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Companies used by normalized job postings. Example: Mews.
CREATE TABLE companies (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Canonical job roles. Example: Data Engineer.
CREATE TABLE roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Canonical skills. Example: Python.
CREATE TABLE skills (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Job seniority levels. Example: Senior.
CREATE TABLE seniority_levels (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

-- Skill proficiency levels. Example: Advanced.
CREATE TABLE proficiency_levels (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

-- Requirement types for skills. Example: Required.
CREATE TABLE requirement_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

-- Legal or contractual engagement relations. Example: Employee or Self-employed.
CREATE TABLE employment_relations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Workload categories. Example: Full-time or Part-time.
CREATE TABLE workloads (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Work modes. Example: Remote.
CREATE TABLE work_modes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Canonical locations. Example: Prague, Czechia.
CREATE TABLE locations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- One normalized record for one posting from one source board.
-- The complete original advertisement is stored in raw_advertisement.
CREATE TABLE job_postings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id),
    source_job_id TEXT NOT NULL,
    company_id BIGINT REFERENCES companies(id),
    role_id BIGINT REFERENCES roles(id),
    seniority_level_id BIGINT REFERENCES seniority_levels(id),
    raw_advertisement JSONB NOT NULL,
    source_url TEXT,
    source_published_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    normalization_version TEXT NOT NULL DEFAULT 'v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, source_job_id),
    CHECK (status IN ('active', 'inactive', 'unknown'))
);

-- Locations offered by a posting. Example: Prague and Brno.
CREATE TABLE job_posting_locations (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    location_id BIGINT NOT NULL REFERENCES locations(id),
    PRIMARY KEY (job_posting_id, location_id)
);

-- Work modes offered by a posting. Example: Remote and Hybrid.
CREATE TABLE job_posting_work_modes (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    work_mode_id BIGINT NOT NULL REFERENCES work_modes(id),
    PRIMARY KEY (job_posting_id, work_mode_id)
);

-- Employment alternatives offered by a posting.
-- Example: Employee full-time or Self-employed full-time.
CREATE TABLE job_posting_employment_options (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    employment_relation_id BIGINT REFERENCES employment_relations(id),
    workload_id BIGINT REFERENCES workloads(id),
    hours_min NUMERIC(7, 2),
    hours_max NUMERIC(7, 2),
    hours_period TEXT,
    CHECK (hours_min IS NULL OR hours_min >= 0),
    CHECK (hours_max IS NULL OR hours_max >= 0),
    CHECK (hours_min IS NULL OR hours_max IS NULL OR hours_max >= hours_min),
    CHECK (hours_period IS NULL OR hours_period IN ('day', 'week', 'month', 'year'))
);

-- Skills assigned to a posting. Example: Python is required at an advanced level.
CREATE TABLE job_skill_requirements (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(id),
    proficiency_level_id BIGINT REFERENCES proficiency_levels(id),
    requirement_type_id BIGINT REFERENCES requirement_types(id),
    priority SMALLINT,
    PRIMARY KEY (job_posting_id, skill_id),
    CHECK (priority IS NULL OR priority BETWEEN 1 AND 5)
);

-- Logical job shared by one or more source postings. Example: one Data Engineer vacancy.
CREATE TABLE canonical_jobs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Links source postings to their logical canonical job.
CREATE TABLE job_posting_sources (
    canonical_job_id BIGINT NOT NULL REFERENCES canonical_jobs(id) ON DELETE CASCADE,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    PRIMARY KEY (canonical_job_id, job_posting_id),
    UNIQUE (job_posting_id)
);

CREATE INDEX job_postings_source_id_idx ON job_postings (source_id);
CREATE INDEX job_postings_company_id_idx ON job_postings (company_id);
CREATE INDEX job_postings_role_id_idx ON job_postings (role_id);
CREATE INDEX job_postings_last_seen_at_idx ON job_postings (last_seen_at);
CREATE INDEX job_posting_locations_location_id_idx
    ON job_posting_locations (location_id);
CREATE INDEX job_posting_work_modes_work_mode_id_idx
    ON job_posting_work_modes (work_mode_id);
CREATE INDEX job_posting_employment_options_relation_id_idx
    ON job_posting_employment_options (employment_relation_id);
CREATE INDEX job_skill_requirements_skill_id_idx
    ON job_skill_requirements (skill_id);
CREATE INDEX job_posting_sources_canonical_job_id_idx
    ON job_posting_sources (canonical_job_id);

COMMIT;
