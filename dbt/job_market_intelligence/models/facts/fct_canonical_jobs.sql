{{ config(materialized='view') }}

with posting_counts as (
    select
        canonical_job_id,
        count(*) as posting_count,
        count(*) filter (where status = 'active') as active_posting_count,
        count(distinct source_id) as source_count,
        min(coalesce(source_published_at, retrieved_at)) as first_seen_at,
        max(last_seen_at) as last_seen_at
    from {{ ref('stg_job_postings') }}
    where canonical_job_id is not null
    group by canonical_job_id
),
primary_postings as (
    select *
    from {{ ref('fct_job_postings') }}
    where selection_rank = 1
)

select
    canonical.id as canonical_job_id,
    primary_posting.job_posting_id as primary_job_posting_id,
    case
        when coalesce(posting_counts.active_posting_count, 0) > 0 then 'active'
        else 'inactive'
    end as status,
    coalesce(posting_counts.posting_count, 0) as posting_count,
    coalesce(posting_counts.active_posting_count, 0) as active_posting_count,
    coalesce(posting_counts.source_count, 0) as source_count,
    posting_counts.first_seen_at,
    posting_counts.last_seen_at,
    primary_posting.company_id,
    primary_posting.role_id,
    primary_posting.source_id,
    primary_posting.seniority_id,
    primary_posting.source_published_at,
    primary_posting.source_url,
    primary_posting.salary_min,
    primary_posting.salary_max,
    primary_posting.salary_currency,
    primary_posting.salary_period
from {{ source('operational', 'canonical_jobs') }} as canonical
left join posting_counts
    on posting_counts.canonical_job_id = canonical.id
left join primary_postings as primary_posting
    on primary_posting.canonical_job_id = canonical.id
