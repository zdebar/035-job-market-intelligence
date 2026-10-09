-- Active job postings grouped by company.

SELECT
    COALESCE(c.name, '[unknown company]') AS company,
    COUNT(*) AS active_postings
FROM job_postings AS jp
LEFT JOIN companies AS c ON c.id = jp.company_id
WHERE jp.status = 'active'
GROUP BY c.id, c.name
ORDER BY active_postings DESC, company;
