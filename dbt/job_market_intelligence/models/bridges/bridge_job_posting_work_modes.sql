{{ config(materialized='view') }}

select
    job_posting_id,
    work_mode_id
from {{ ref('stg_job_posting_work_modes') }}
