CREATE TABLE IF NOT EXISTS marketing.interactions (
    interaction_id TEXT PRIMARY KEY,

    customer_unique_id TEXT,

    email TEXT,

    campaign_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'Email',

    event_at TIMESTAMPTZ NOT NULL,

    quality_profile TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_marketing_interactions_customer
    ON marketing.interactions (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_marketing_interactions_email
    ON marketing.interactions (email);

CREATE INDEX IF NOT EXISTS idx_marketing_interactions_event
    ON marketing.interactions (event_type);

CREATE INDEX IF NOT EXISTS idx_marketing_interactions_date
    ON marketing.interactions (event_at);

CREATE INDEX IF NOT EXISTS idx_marketing_interactions_quality
    ON marketing.interactions (quality_profile);
