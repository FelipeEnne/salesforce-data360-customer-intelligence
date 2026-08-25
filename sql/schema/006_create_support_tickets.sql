CREATE TABLE IF NOT EXISTS support.tickets (
    ticket_id TEXT PRIMARY KEY,

    -- Ground truth interno do laboratório.
    -- Depois o Data 360 não deverá depender deste campo
    -- para fazer Identity Resolution.
    customer_unique_id TEXT,

    requester_name TEXT,
    requester_email TEXT,
    requester_phone TEXT,

    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    channel TEXT NOT NULL,

    sentiment TEXT,

    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,

    resolution_hours NUMERIC(10,2),

    quality_profile TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_support_tickets_customer
    ON support.tickets (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_support_tickets_email
    ON support.tickets (requester_email);

CREATE INDEX IF NOT EXISTS idx_support_tickets_phone
    ON support.tickets (requester_phone);

CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at
    ON support.tickets (created_at);

CREATE INDEX IF NOT EXISTS idx_support_tickets_quality_profile
    ON support.tickets (quality_profile);
