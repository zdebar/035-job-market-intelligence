-- One readable row per job posting.
-- Add a WHERE clause on jp.id when inspecting one posting.

WITH posting_locations AS (
    SELECT
        jpl.job_posting_id,
        string_agg(l.name, ', ' ORDER BY l.name) AS locations
    FROM job_posting_locations AS jpl
    JOIN locations AS l ON l.id = jpl.location_id
    GROUP BY jpl.job_posting_id
),
posting_work_modes AS (
    SELECT
        jpwm.job_posting_id,
        string_agg(wm.name, ', ' ORDER BY wm.name) AS work_modes
    FROM job_posting_work_modes AS jpwm
    JOIN work_modes AS wm ON wm.id = jpwm.work_mode_id
    GROUP BY jpwm.job_posting_id
),
posting_employment_options AS (
    SELECT
        jpeo.job_posting_id,
        jsonb_agg(
            jsonb_build_object(
                'employment_relation', er.name,
                'workload', w.name,
                'hours_min', jpeo.hours_min,
                'hours_max', jpeo.hours_max,
                'hours_period', jpeo.hours_period
            )
            ORDER BY jpeo.id
        ) AS employment_options
    FROM job_posting_employment_options AS jpeo
    LEFT JOIN employment_relations AS er
        ON er.id = jpeo.employment_relation_id
    LEFT JOIN workloads AS w ON w.id = jpeo.workload_id
    GROUP BY jpeo.job_posting_id
),
posting_skills AS (
    SELECT
        jsr.job_posting_id,
        jsonb_agg(
            jsonb_build_object(
                'skill', s.name,
                'proficiency', pl.name,
                'requirement_type', rt.name,
                'priority', jsr.priority
            )
            ORDER BY s.name
        ) AS skills
    FROM job_skill_requirements AS jsr
    JOIN skills AS s ON s.id = jsr.skill_id
    LEFT JOIN proficiency_levels AS pl
        ON pl.id = jsr.proficiency_level_id
    LEFT JOIN requirement_types AS rt
        ON rt.id = jsr.requirement_type_id
    GROUP BY jsr.job_posting_id
)
SELECT
    jp.id AS job_posting_id,
    jp.status,
    source.name AS source,
    jp.source_job_id,
    c.name AS company,
    r.name AS role,
    sl.name AS seniority_level,
    pl.locations,
    pwm.work_modes,
    peo.employment_options,
    ps.skills,
    jpc.salary_min,
    jpc.salary_max,
    jpc.salary_currency,
    jpc.salary_period,
    jp.source_url,
    jp.source_published_at,
    jp.source_updated_at,
    jp.retrieved_at,
    jp.last_seen_at
FROM job_postings AS jp
JOIN sources AS source ON source.id = jp.source_id
LEFT JOIN companies AS c ON c.id = jp.company_id
LEFT JOIN roles AS r ON r.id = jp.role_id
LEFT JOIN seniority_levels AS sl ON sl.id = jp.seniority_level_id
LEFT JOIN posting_locations AS pl ON pl.job_posting_id = jp.id
LEFT JOIN posting_work_modes AS pwm ON pwm.job_posting_id = jp.id
LEFT JOIN posting_employment_options AS peo
    ON peo.job_posting_id = jp.id
LEFT JOIN posting_skills AS ps ON ps.job_posting_id = jp.id
LEFT JOIN job_posting_compensations AS jpc ON jpc.job_posting_id = jp.id
ORDER BY jp.last_seen_at DESC, jp.id;
