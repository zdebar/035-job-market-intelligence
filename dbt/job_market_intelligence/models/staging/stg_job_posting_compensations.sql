{{ config(materialized='view') }}

select
    job_posting_id,
    salary_min,
    salary_max,
    salary_currency,
    salary_period
from {{ source('operational', 'job_posting_compensations') }}
