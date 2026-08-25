-- Total de contatos
SELECT
    'salesforce_contact_count' AS check_name,
    COUNT(*) AS value
FROM crm.salesforce_contacts;


-- Contatos sem Customer Master correspondente
SELECT
    'contacts_without_master' AS check_name,
    COUNT(*) AS value
FROM crm.salesforce_contacts sf
LEFT JOIN crm.customer_master cm
    ON cm.customer_unique_id = sf.customer_unique_id
WHERE cm.customer_unique_id IS NULL;


-- Nomes diferentes
SELECT
    'different_name' AS check_name,
    COUNT(*) AS value
FROM crm.salesforce_contacts sf
JOIN crm.customer_master cm
    USING (customer_unique_id)
WHERE sf.full_name IS DISTINCT FROM cm.full_name;


-- Emails diferentes
SELECT
    'different_email' AS check_name,
    COUNT(*) AS value
FROM crm.salesforce_contacts sf
JOIN crm.customer_master cm
    USING (customer_unique_id)
WHERE sf.email IS DISTINCT FROM cm.email;


-- Telefones diferentes
SELECT
    'different_phone' AS check_name,
    COUNT(*) AS value
FROM crm.salesforce_contacts sf
JOIN crm.customer_master cm
    USING (customer_unique_id)
WHERE sf.phone IS DISTINCT FROM cm.phone_e164;


-- Distribuição dos perfis
SELECT
    quality_profile,
    COUNT(*) AS contacts,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM crm.salesforce_contacts
GROUP BY quality_profile
ORDER BY contacts DESC;
