# Streaming + AI-clean layer

Live order-event stream → **Redpanda (Kafka API)** → **AI-clean gate** → **PostgreSQL** → **dbt trust models**.

Additive layer. The batch star-schema ETL (`src/etl/pipeline.py`) is untouched; streamed data lands in its own tables (`raw_orders_events`, `fact_orders_stream`) so the boundary stays legible.

## What makes it "AI-ready", not just "AI-cleaned"

| Stage | Component | Trust property |
|---|---|---|
| Ingest | `producer.py` → Redpanda → `consumer.py` | append-only landing; nothing dropped |
| Clean | `ai_clean.py` | **rules first, LLM only on ambiguity, abstain when unsure** |
| Govern | `orders_quarantine`, `orders_clean_audit` | every decision has lineage; low-confidence → quarantine |
| Model | `models/streaming/*` | typed, tested, closed status vocabulary |
| Score | `mart_bi_readiness` | 0–100 readiness + hard reconciliation gate |
| Define | `../semantic/metrics.yml` | one meaning per metric for BI + agents |

The AI-clean gate **abstains** instead of guessing: `01/08/26` (Jan 8 vs Aug 1) with no confident resolution goes to quarantine, not into revenue.

## Run it locally (free)

```bash
# 1. start Postgres + Redpanda (+ console at http://localhost:8080)
docker compose up -d postgres_warehouse redpanda redpanda_console

# 2. create tables
psql -h localhost -p 5433 -U analytics_engineer -d customer_intelligence_db -f sql/ddl/schema.sql
psql -h localhost -p 5433 -U analytics_engineer -d customer_intelligence_db -f sql/ddl/streaming.sql

# 3. stream events (terminal A)
python -m streaming.producer --rate 5

# 4. clean + load (terminal B)
python -m streaming.consumer            # Ctrl-C to stop

# 5. build trust models + scorecard
dbt build --select streaming source:stream
psql -h localhost -p 5433 -U analytics_engineer -d customer_intelligence_db \
  -c "SELECT * FROM streaming.mart_bi_readiness;"
```

## AI provider

Set `GEMINI_API_KEY` in the environment (or a `.env`) to enable Gemini-assisted
resolution of ambiguous fields. **With no key the gate runs offline** — deterministic
rules plus abstention — so everything works free and in CI. Model + confidence
threshold are in `config/config.yaml → ai_clean`.

## Always-on, free

`.github/workflows/streaming-pipeline.yml` runs the full path on every push (CI)
and on a 30-min schedule — the free, always-on substitute for a 24/7 server.
