-- Resumo geral
SELECT
    'web_summary' AS check_name,
    COUNT(*) AS events,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT anonymous_id) AS anonymous_ids
FROM web.events;


-- Tipos de evento inválidos
SELECT
    'invalid_event_type' AS check_name,
    COUNT(*) AS issues
FROM web.events
WHERE event_type NOT IN (
    'page_view',
    'product_view',
    'add_to_cart',
    'checkout_started',
    'purchase'
);


-- Eventos sem anonymous_id
SELECT
    'events_without_anonymous_id' AS check_name,
    COUNT(*) AS issues
FROM web.events
WHERE anonymous_id IS NULL;


-- Eventos sem session_id
SELECT
    'events_without_session_id' AS check_name,
    COUNT(*) AS issues
FROM web.events
WHERE session_id IS NULL;


-- Eventos conhecidos sem customer_unique_id
SELECT
    'known_without_customer_id' AS check_name,
    COUNT(*) AS issues
FROM web.events
WHERE quality_profile <> 'anonymous_only'
  AND customer_unique_id IS NULL;


-- Eventos anônimos que carregam customer_unique_id
SELECT
    'anonymous_with_customer_id' AS check_name,
    COUNT(*) AS issues
FROM web.events
WHERE quality_profile = 'anonymous_only'
  AND customer_unique_id IS NOT NULL;


-- Clientes conhecidos sem correspondência no Customer Master
SELECT
    'known_without_master' AS check_name,
    COUNT(*) AS issues
FROM web.events e
LEFT JOIN crm.customer_master cm
    ON cm.customer_unique_id = e.customer_unique_id
WHERE e.customer_unique_id IS NOT NULL
  AND cm.customer_unique_id IS NULL;


-- Purchase sem checkout na mesma sessão
SELECT
    'purchase_without_checkout' AS check_name,
    COUNT(*) AS issues
FROM web.events purchase
WHERE purchase.event_type = 'purchase'
AND NOT EXISTS (
    SELECT 1
    FROM web.events checkout
    WHERE checkout.session_id = purchase.session_id
      AND checkout.event_type = 'checkout_started'
);


-- Checkout sem add_to_cart
SELECT
    'checkout_without_cart' AS check_name,
    COUNT(*) AS issues
FROM web.events checkout
WHERE checkout.event_type = 'checkout_started'
AND NOT EXISTS (
    SELECT 1
    FROM web.events cart
    WHERE cart.session_id = checkout.session_id
      AND cart.event_type = 'add_to_cart'
);


-- Ordem temporal inválida dentro da sessão
SELECT
    'invalid_session_order' AS check_name,
    COUNT(*) AS issues
FROM web.events later
JOIN web.events earlier
    ON earlier.session_id = later.session_id
WHERE
    (
        later.event_type = 'product_view'
        AND earlier.event_type = 'page_view'
        AND later.event_at < earlier.event_at
    )
    OR
    (
        later.event_type = 'add_to_cart'
        AND earlier.event_type = 'product_view'
        AND later.event_at < earlier.event_at
    )
    OR
    (
        later.event_type = 'checkout_started'
        AND earlier.event_type = 'add_to_cart'
        AND later.event_at < earlier.event_at
    )
    OR
    (
        later.event_type = 'purchase'
        AND earlier.event_type = 'checkout_started'
        AND later.event_at < earlier.event_at
    );


-- Distribuição por tipo
SELECT
    event_type,
    COUNT(*) AS events
FROM web.events
GROUP BY event_type
ORDER BY events DESC;


-- Distribuição identity state
SELECT
    CASE
        WHEN customer_unique_id IS NULL
            THEN 'anonymous'
        ELSE 'known'
    END AS identity_state,
    COUNT(*) AS events
FROM web.events
GROUP BY identity_state
ORDER BY events DESC;


-- Perfis de qualidade
SELECT
    quality_profile,
    COUNT(*) AS events,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM web.events
GROUP BY quality_profile
ORDER BY events DESC;
