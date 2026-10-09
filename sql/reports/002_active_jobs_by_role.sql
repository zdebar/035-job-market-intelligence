-- Active job postings grouped by normalized role.

SELECT
    COALESCE(r.name, '[unknown role]') AS role,
    COUNT(*) AS active_postings
FROM job_postings AS jp
LEFT JOIN roles AS r ON r.id = jp.role_id
WHERE jp.status = 'active'
GROUP BY r.id, r.name
ORDER BY active_postings DESC, role;
