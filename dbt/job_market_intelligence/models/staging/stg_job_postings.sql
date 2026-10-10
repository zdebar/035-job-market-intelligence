{{ config(materialized='view') }}

select
    posting.id as job_posting_id,
    posting.source_id,
    posting.source_job_id,
    posting.company_id,
    posting.role_id,
    posting.seniority_level_id as seniority_id,
    posting.source_url,
    posting.source_published_at,
    posting.source_updated_at,
    posting.retrieved_at,
    posting.last_seen_at,
    posting.status,
    posting.normalization_version,
    posting.content_fingerprint,
    posting.created_at,
    posting.updated_at,
    posting_source.canonical_job_id,
    posting_source.match_method,
    posting_source.matched_at,
    posting_source.selection_rank
from {{ source('operational', 'job_postings') }} as posting
left join {{ ref('stg_job_posting_sources') }} as posting_source
    on posting_source.job_posting_id = posting.id
