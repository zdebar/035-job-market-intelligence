-- Active job postings grouped by offered work mode.

SELECT
    wm.name AS work_mode,
    COUNT(DISTINCT jpwm.job_posting_id) AS active_postings
FROM job_posting_work_modes AS jpwm
JOIN work_modes AS wm ON wm.id = jpwm.work_mode_id
JOIN job_postings AS jp ON jp.id = jpwm.job_posting_id
WHERE jp.status = 'active'
GROUP BY wm.id, wm.name
ORDER BY active_postings DESC, work_mode;
