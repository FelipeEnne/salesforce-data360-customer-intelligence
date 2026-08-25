SELECT
    'duplicate_email' AS check_name,
    COUNT(*) AS issues
FROM (
    SELECT email
    FROM crm.customer_master
    GROUP BY email
    HAVING COUNT(*) > 1
) t;

SELECT
    'duplicate_phone' AS check_name,
    COUNT(*) AS issues
FROM (
    SELECT phone_e164
    FROM crm.customer_master
    GROUP BY phone_e164
    HAVING COUNT(*) > 1
) t;

SELECT
    'missing_identity_fields' AS check_name,
    COUNT(*) AS issues
FROM crm.customer_master
WHERE full_name IS NULL
   OR email IS NULL
   OR phone_e164 IS NULL;

SELECT
    'customer_master_count' AS check_name,
    COUNT(*) AS issues
FROM crm.customer_master;
