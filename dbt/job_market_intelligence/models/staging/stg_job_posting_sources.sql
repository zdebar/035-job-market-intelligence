{{ config(materialized='view') }}

select
    canonical_job_id,
    job_posting_id,
    match_method,
    matched_at
from {{ source('operational', 'job_posting_sources') }}
