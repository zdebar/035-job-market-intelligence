-- Quality check: active postings must have a unique deterministic rank.

SELECT
    'active_posting_without_rank' AS issue,
    COUNT(*)::BIGINT AS issue_count
FROM job_postings postings
JOIN job_posting_sources links ON links.job_posting_id = postings.id
WHERE postings.status = 'active'
  AND links.selection_rank IS NULL

UNION ALL

SELECT
    'canonical_with_multiple_primary_postings' AS issue,
    COUNT(*)::BIGINT AS issue_count
FROM job_posting_sources links
WHERE links.selection_rank = 1
GROUP BY links.canonical_job_id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'inactive_posting_with_rank' AS issue,
    COUNT(*)::BIGINT AS issue_count
FROM job_postings postings
JOIN job_posting_sources links ON links.job_posting_id = postings.id
WHERE postings.status <> 'active'
  AND links.selection_rank IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM job_postings postings
        JOIN job_posting_sources links ON links.job_posting_id = postings.id
        WHERE postings.status = 'active'
          AND links.selection_rank IS NULL
    ) THEN
        RAISE EXCEPTION 'Active posting is missing a canonical selection rank';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM job_posting_sources links
        WHERE links.selection_rank = 1
        GROUP BY links.canonical_job_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Canonical job has multiple primary postings';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM job_postings postings
        JOIN job_posting_sources links ON links.job_posting_id = postings.id
        WHERE postings.status <> 'active'
          AND links.selection_rank IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'Inactive posting has a selection rank';
    END IF;
END;
$$;
