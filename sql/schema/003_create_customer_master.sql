CREATE TABLE IF NOT EXISTS crm.customer_master (
    customer_unique_id TEXT PRIMARY KEY,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,

    email TEXT NOT NULL UNIQUE,
    phone_e164 TEXT NOT NULL,

    birth_date DATE,

    source_system TEXT NOT NULL DEFAULT 'olist_enriched',
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customer_master_email
    ON crm.customer_master (email);

CREATE INDEX IF NOT EXISTS idx_customer_master_phone
    ON crm.customer_master (phone_e164);

CREATE INDEX IF NOT EXISTS idx_customer_master_name
    ON crm.customer_master (full_name);
