{{ config(materialized='view') }}

select
    job_posting_id,
    skill_id,
    proficiency_level_id,
    requirement_type_id,
    priority
from {{ source('operational', 'job_skill_requirements') }}
