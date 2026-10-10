{{ config(materialized='view') }}

select
    posting.job_posting_id,
    posting.canonical_job_id,
    posting.company_id,
    posting.role_id,
    posting.source_id,
    posting.seniority_id,
    posting.status,
    posting.source_published_at,
    posting.retrieved_at,
    posting.last_seen_at,
    posting.source_url,
    compensation.salary_min,
    compensation.salary_max,
    compensation.salary_currency,
    compensation.salary_period
from {{ ref('stg_job_postings') }} as posting
left join {{ ref('stg_job_posting_compensations') }} as compensation
    on compensation.job_posting_id = posting.job_posting_id
