-- Resumo geral
SELECT
    'marketing_summary' AS check_name,
    COUNT(*) AS interactions,
    COUNT(DISTINCT customer_unique_id) AS customers
FROM marketing.interactions;


-- Interações sem Customer Master correspondente
SELECT
    'interactions_without_master' AS check_name,
    COUNT(*) AS issues
FROM marketing.interactions m
LEFT JOIN crm.customer_master cm
    ON cm.customer_unique_id = m.customer_unique_id
WHERE cm.customer_unique_id IS NULL;


-- Eventos sem identificação suficiente
SELECT
    'interactions_without_identity' AS check_name,
    COUNT(*) AS issues
FROM marketing.interactions
WHERE customer_unique_id IS NULL
  AND email IS NULL;


-- Tipos de evento inválidos
SELECT
    'invalid_event_type' AS check_name,
    COUNT(*) AS issues
FROM marketing.interactions
WHERE event_type NOT IN (
    'email_sent',
    'email_open',
    'email_click',
    'campaign_conversion',
    'unsubscribe'
);


-- Emails sem evento de envio correspondente
SELECT
    'engagement_without_sent' AS check_name,
    COUNT(*) AS issues
FROM marketing.interactions m
WHERE m.event_type <> 'email_sent'
AND NOT EXISTS (
    SELECT 1
    FROM marketing.interactions sent
    WHERE sent.customer_unique_id = m.customer_unique_id
      AND sent.campaign_name = m.campaign_name
      AND sent.event_type = 'email_sent'
);


-- Distribuição por evento
SELECT
    event_type,
    COUNT(*) AS interactions,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM marketing.interactions
GROUP BY event_type
ORDER BY interactions DESC;


-- Distribuição dos perfis de qualidade
SELECT
    quality_profile,
    COUNT(*) AS interactions,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM marketing.interactions
GROUP BY quality_profile
ORDER BY interactions DESC;


-- Distribuição por campanha
SELECT
    campaign_name,
    COUNT(*) AS interactions
FROM marketing.interactions
GROUP BY campaign_name
ORDER BY interactions DESC;
