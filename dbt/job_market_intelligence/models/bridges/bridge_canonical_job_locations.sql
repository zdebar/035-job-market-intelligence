{{ config(materialized='view') }}

select
    postings.canonical_job_id,
    locations.location_id
from {{ ref('stg_job_postings') }} as postings
join {{ ref('stg_job_posting_locations') }} as locations
    on locations.job_posting_id = postings.job_posting_id
where postings.selection_rank = 1
