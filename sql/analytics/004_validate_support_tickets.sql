-- Total de tickets e clientes atendidos
SELECT
    'support_summary' AS check_name,
    COUNT(*) AS tickets,
    COUNT(DISTINCT customer_unique_id) AS customers
FROM support.tickets;


-- Tickets sem Customer Master
SELECT
    'tickets_without_master' AS check_name,
    COUNT(*) AS issues
FROM support.tickets t
LEFT JOIN crm.customer_master cm
    ON cm.customer_unique_id = t.customer_unique_id
WHERE cm.customer_unique_id IS NULL;


-- Tickets com identidade totalmente ausente
SELECT
    'tickets_without_identity' AS check_name,
    COUNT(*) AS issues
FROM support.tickets
WHERE requester_name IS NULL
  AND requester_email IS NULL
  AND requester_phone IS NULL;


-- Tickets resolvidos sem data de resolução
SELECT
    'resolved_without_date' AS check_name,
    COUNT(*) AS issues
FROM support.tickets
WHERE status IN ('Resolved', 'Closed')
  AND resolved_at IS NULL;


-- Tickets abertos que possuem data de resolução
SELECT
    'open_with_resolution_date' AS check_name,
    COUNT(*) AS issues
FROM support.tickets
WHERE status = 'Open'
  AND resolved_at IS NOT NULL;


-- Datas inconsistentes
SELECT
    'resolution_before_creation' AS check_name,
    COUNT(*) AS issues
FROM support.tickets
WHERE resolved_at < created_at;


-- Perfis de qualidade
SELECT
    quality_profile,
    COUNT(*) AS tickets,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM support.tickets
GROUP BY quality_profile
ORDER BY tickets DESC;


-- Distribuição de status
SELECT
    status,
    COUNT(*) AS tickets
FROM support.tickets
GROUP BY status
ORDER BY tickets DESC;


-- Distribuição de sentimento
SELECT
    sentiment,
    COUNT(*) AS tickets
FROM support.tickets
GROUP BY sentiment
ORDER BY tickets DESC;
