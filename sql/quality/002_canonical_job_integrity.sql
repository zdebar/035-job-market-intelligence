-- Informational report for cross-source canonical matching.
WITH issues AS (
    SELECT
        'missing_canonical_link' AS issue,
        COUNT(*)::BIGINT AS issue_count
    FROM job_postings postings
    LEFT JOIN job_posting_sources links ON links.job_posting_id = postings.id
    WHERE links.job_posting_id IS NULL

    UNION ALL

    SELECT
        'canonical_without_posting' AS issue,
        COUNT(*)::BIGINT AS issue_count
    FROM canonical_jobs canonical
    LEFT JOIN job_posting_sources links
        ON links.canonical_job_id = canonical.id
    WHERE links.canonical_job_id IS NULL

    UNION ALL

    SELECT
        'duplicate_fingerprint_across_canonicals' AS issue,
        COUNT(*)::BIGINT AS issue_count
    FROM (
        SELECT postings.company_id, postings.content_fingerprint
        FROM job_postings postings
        JOIN job_posting_sources links ON links.job_posting_id = postings.id
        WHERE postings.content_fingerprint IS NOT NULL
        GROUP BY postings.company_id, postings.content_fingerprint
        HAVING COUNT(DISTINCT links.canonical_job_id) > 1
    ) duplicates

    UNION ALL

    SELECT
        'invalid_match_method' AS issue,
        COUNT(*)::BIGINT AS issue_count
    FROM job_posting_sources links
    WHERE links.match_method NOT IN (
        'new_canonical_job',
        'algorithmic_match',
        'llm_match',
        'manual_match'
    )
)
SELECT issue, issue_count
FROM issues
ORDER BY issue;
