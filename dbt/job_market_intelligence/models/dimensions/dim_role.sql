{{ config(materialized='view') }}

select
    id as role_id,
    name as role_name
from {{ source('operational', 'roles') }}
