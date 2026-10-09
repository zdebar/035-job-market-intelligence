-- Most common normalized skills in active job postings.

SELECT
    s.name AS skill,
    COUNT(DISTINCT jsr.job_posting_id) AS active_postings
FROM job_skill_requirements AS jsr
JOIN skills AS s ON s.id = jsr.skill_id
JOIN job_postings AS jp ON jp.id = jsr.job_posting_id
WHERE jp.status = 'active'
GROUP BY s.id, s.name
ORDER BY active_postings DESC, skill;
