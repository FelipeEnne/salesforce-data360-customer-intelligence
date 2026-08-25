CREATE TABLE IF NOT EXISTS crm.salesforce_contacts (
    salesforce_contact_id TEXT PRIMARY KEY,

    customer_unique_id TEXT,

    first_name TEXT,
    last_name TEXT,
    full_name TEXT,

    email TEXT,
    phone TEXT,

    lead_source TEXT,
    contact_status TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_salesforce_contacts_email
    ON crm.salesforce_contacts (email);

CREATE INDEX IF NOT EXISTS idx_salesforce_contacts_phone
    ON crm.salesforce_contacts (phone);

CREATE INDEX IF NOT EXISTS idx_salesforce_contacts_customer
    ON crm.salesforce_contacts (customer_unique_id);
