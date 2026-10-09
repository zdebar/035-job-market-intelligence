-- Active job postings grouped by offered location.

SELECT
    l.name AS location,
    COUNT(DISTINCT jpl.job_posting_id) AS active_postings
FROM job_posting_locations AS jpl
JOIN locations AS l ON l.id = jpl.location_id
JOIN job_postings AS jp ON jp.id = jpl.job_posting_id
WHERE jp.status = 'active'
GROUP BY l.id, l.name
ORDER BY active_postings DESC, location;
