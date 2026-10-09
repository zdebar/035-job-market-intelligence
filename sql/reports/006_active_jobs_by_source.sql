-- Active job postings grouped by source.

SELECT
    s.name AS source,
    COUNT(*) AS active_postings
FROM job_postings AS jp
JOIN sources AS s ON s.id = jp.source_id
WHERE jp.status = 'active'
GROUP BY s.id, s.name
ORDER BY active_postings DESC, source;
