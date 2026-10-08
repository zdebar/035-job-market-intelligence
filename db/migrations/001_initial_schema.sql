BEGIN;

-- Registered ingestion sources. Example: Greenhouse.
CREATE TABLE sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Companies used by normalized job postings. Example: Microsoft.
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

-- Work modes. Example: Remote.
CREATE TABLE work_modes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Employment types. Example: Full-time.
CREATE TABLE employment_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Canonical locations. Example: Prague, Czechia.
CREATE TABLE locations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- One normalized record for one posting from one source.
-- The complete original advertisement is stored in raw_advertisement.
CREATE TABLE job_postings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id),
    source_job_id TEXT NOT NULL,
    company_id BIGINT REFERENCES companies(id),
    role_id BIGINT REFERENCES roles(id),
    seniority_level_id BIGINT REFERENCES seniority_levels(id),
    work_mode_id BIGINT REFERENCES work_modes(id),
    employment_type_id BIGINT REFERENCES employment_types(id),
    location_id BIGINT REFERENCES locations(id),
    raw_advertisement JSONB NOT NULL,
    source_url TEXT,
    source_published_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    normalization_version TEXT NOT NULL DEFAULT 'v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, source_job_id)
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
-- Example: Greenhouse and another source can point to one canonical job.
CREATE TABLE job_posting_sources (
    canonical_job_id BIGINT NOT NULL REFERENCES canonical_jobs(id) ON DELETE CASCADE,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    PRIMARY KEY (canonical_job_id, job_posting_id),
    UNIQUE (job_posting_id)
);

CREATE INDEX job_postings_source_id_idx ON job_postings (source_id);
CREATE INDEX job_postings_company_id_idx ON job_postings (company_id);
CREATE INDEX job_postings_role_id_idx ON job_postings (role_id);
CREATE INDEX job_postings_retrieved_at_idx ON job_postings (retrieved_at);
CREATE INDEX job_skill_requirements_skill_id_idx
    ON job_skill_requirements (skill_id);
CREATE INDEX job_posting_sources_canonical_job_id_idx
    ON job_posting_sources (canonical_job_id);

COMMIT;
