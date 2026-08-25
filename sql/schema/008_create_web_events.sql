CREATE TABLE IF NOT EXISTS web.events (
    event_id TEXT PRIMARY KEY,

    -- Identidade anônima do navegador/device
    anonymous_id TEXT NOT NULL,

    -- Agrupa eventos da mesma sessão
    session_id TEXT NOT NULL,

    -- Ground truth interno do laboratório.
    -- O Data 360 não deverá depender deste campo
    -- diretamente para Identity Resolution.
    customer_unique_id TEXT,

    -- Pode existir apenas depois que o usuário
    -- se identifica, faz login ou checkout.
    email TEXT,

    event_type TEXT NOT NULL,

    product_id TEXT,

    page_path TEXT,

    device_type TEXT NOT NULL,

    event_at TIMESTAMPTZ NOT NULL,

    quality_profile TEXT NOT NULL,

    event_properties JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_web_events_customer
    ON web.events (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_web_events_email
    ON web.events (email);

CREATE INDEX IF NOT EXISTS idx_web_events_anonymous
    ON web.events (anonymous_id);

CREATE INDEX IF NOT EXISTS idx_web_events_session
    ON web.events (session_id);

CREATE INDEX IF NOT EXISTS idx_web_events_type
    ON web.events (event_type);

CREATE INDEX IF NOT EXISTS idx_web_events_product
    ON web.events (product_id);

CREATE INDEX IF NOT EXISTS idx_web_events_date
    ON web.events (event_at);

CREATE INDEX IF NOT EXISTS idx_web_events_quality
    ON web.events (quality_profile);
