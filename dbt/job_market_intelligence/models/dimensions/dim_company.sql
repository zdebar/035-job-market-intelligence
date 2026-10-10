{{ config(materialized='view') }}

select
    id as company_id,
    name as company_name
from {{ source('operational', 'companies') }}
