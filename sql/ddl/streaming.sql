-- =====================================================================
-- Streaming ingestion layer (additive; does NOT touch the batch star schema)
-- Landing -> AI-clean audit -> quarantine -> promoted stream fact.
-- Every landed event is ACCOUNTED FOR: promoted OR quarantined, never dropped.
-- =====================================================================

-- Append-only raw landing table. Payload stored as-received (messy, untyped).
CREATE TABLE IF NOT EXISTS raw_orders_events (
    event_id     BIGSERIAL PRIMARY KEY,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    source       VARCHAR(50),
    kafka_topic  VARCHAR(100),
    kafka_offset BIGINT,
    payload      JSONB NOT NULL
);

-- One row per field the AI-clean gate touched. Full lineage of every decision:
-- rule-based, LLM-assisted, or passthrough, with confidence + model.
CREATE TABLE IF NOT EXISTS orders_clean_audit (
    audit_id    BIGSERIAL PRIMARY KEY,
    event_id    BIGINT REFERENCES raw_orders_events(event_id),
    cleaned_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    field       VARCHAR(50)  NOT NULL,
    raw_value   TEXT,
    clean_value TEXT,
    method      VARCHAR(20)  NOT NULL,   -- 'rule' | 'llm' | 'passthrough'
    confidence  NUMERIC(4, 3),
    model       VARCHAR(50)
);

-- Abstention target. When the pipeline is NOT confident it quarantines
-- instead of guessing. This is the trustworthy-analytics behaviour.
CREATE TABLE IF NOT EXISTS orders_quarantine (
    quarantine_id  BIGSERIAL PRIMARY KEY,
    event_id       BIGINT REFERENCES raw_orders_events(event_id),
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason         TEXT NOT NULL,
    field          VARCHAR(50),
    raw_value      TEXT,
    payload        JSONB
);

-- Promoted, governed, typed stream fact. Kept SEPARATE from batch fact_sales
-- so the streaming boundary stays legible and the batch pipeline is untouched.
CREATE TABLE IF NOT EXISTS fact_orders_stream (
    order_event_id BIGSERIAL PRIMARY KEY,
    event_id       BIGINT REFERENCES raw_orders_events(event_id),
    order_id       VARCHAR(40),
    customer_id    BIGINT,
    country        VARCHAR(100),
    stock_code     VARCHAR(40),
    quantity       INTEGER,
    unit_price     NUMERIC(12, 2),
    order_status   VARCHAR(20),          -- canonical: completed|shipped|cancelled
    order_ts       TIMESTAMPTZ,
    line_revenue   NUMERIC(14, 2),
    promoted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_orders_ingested   ON raw_orders_events (ingested_at);
CREATE INDEX IF NOT EXISTS idx_stream_fact_status    ON fact_orders_stream (order_status);
CREATE INDEX IF NOT EXISTS idx_clean_audit_method    ON orders_clean_audit (method);
