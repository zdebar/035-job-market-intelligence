{{ config(materialized='view') }}

select
    job_posting_id,
    location_id
from {{ ref('stg_job_posting_locations') }}
