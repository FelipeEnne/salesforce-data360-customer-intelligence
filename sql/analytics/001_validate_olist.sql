-- 1. Clientes duplicados por customer_id
SELECT
    'duplicate_customer_id' AS check_name,
    COUNT(*) AS issues
FROM (
    SELECT customer_id
    FROM olist.customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) t;

-- 2. Pedidos sem cliente correspondente
SELECT
    'orders_without_customer' AS check_name,
    COUNT(*) AS issues
FROM olist.orders o
LEFT JOIN olist.customers c
    ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;

-- 3. Itens sem pedido correspondente
SELECT
    'items_without_order' AS check_name,
    COUNT(*) AS issues
FROM olist.order_items oi
LEFT JOIN olist.orders o
    ON o.order_id = oi.order_id
WHERE o.order_id IS NULL;

-- 4. Pagamentos sem pedido
SELECT
    'payments_without_order' AS check_name,
    COUNT(*) AS issues
FROM olist.order_payments p
LEFT JOIN olist.orders o
    ON o.order_id = p.order_id
WHERE o.order_id IS NULL;

-- 5. Reviews sem pedido
SELECT
    'reviews_without_order' AS check_name,
    COUNT(*) AS issues
FROM olist.order_reviews r
LEFT JOIN olist.orders o
    ON o.order_id = r.order_id
WHERE o.order_id IS NULL;

-- 6. Itens sem produto
SELECT
    'items_without_product' AS check_name,
    COUNT(*) AS issues
FROM olist.order_items oi
LEFT JOIN olist.products p
    ON p.product_id = oi.product_id
WHERE p.product_id IS NULL;

-- 7. Valores de preço inválidos
SELECT
    'invalid_item_prices' AS check_name,
    COUNT(*) AS issues
FROM olist.order_items
WHERE price < 0
   OR freight_value < 0;

-- 8. Review score fora da faixa esperada
SELECT
    'invalid_review_score' AS check_name,
    COUNT(*) AS issues
FROM olist.order_reviews
WHERE review_score NOT BETWEEN 1 AND 5;
