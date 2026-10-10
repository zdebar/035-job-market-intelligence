{{ config(materialized='view') }}

select
    postings.canonical_job_id,
    requirements.skill_id,
    requirements.proficiency_level_id,
    requirements.requirement_type_id,
    requirements.priority
from {{ ref('stg_job_postings') }} as postings
join {{ ref('stg_job_skill_requirements') }} as requirements
    on requirements.job_posting_id = postings.job_posting_id
where postings.selection_rank = 1
