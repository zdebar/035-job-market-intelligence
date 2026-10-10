{{ config(materialized='view') }}

select
    postings.canonical_job_id,
    work_modes.work_mode_id
from {{ ref('stg_job_postings') }} as postings
join {{ ref('stg_job_posting_work_modes') }} as work_modes
    on work_modes.job_posting_id = postings.job_posting_id
where postings.selection_rank = 1
