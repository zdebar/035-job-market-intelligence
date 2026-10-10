{{ config(materialized='view') }}

select
    id as seniority_id,
    name as seniority_name,
    sort_order
from {{ source('operational', 'seniority_levels') }}
