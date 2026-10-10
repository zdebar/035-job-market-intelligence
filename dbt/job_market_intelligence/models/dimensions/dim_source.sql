{{ config(materialized='view') }}

select
    id as source_id,
    source_key,
    name as source_name
from {{ source('operational', 'sources') }}
