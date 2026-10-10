{{ config(materialized='view') }}

select
    job_posting_id,
    location_id
from {{ source('operational', 'job_posting_locations') }}
