# Customer Intelligence Data Warehouse

A reproducible analytics engineering and BI-ready warehouse project built around Online Retail II-style e-commerce transaction data. The repository combines Python ETL, PostgreSQL, dbt staging/intermediate/mart models, and Power BI-ready documentation to convert raw retail transactions into trusted reporting tables and business metrics.

---

## Project Overview

Customer Intelligence Data Warehouse ingests raw retail transaction data, cleans and structures it in PostgreSQL, and transforms it through dbt into a layered analytics model. The final marts support executive KPI reporting, customer lifetime value analysis, cohort retention analysis, repeat purchase analysis, country revenue analysis, and monthly sales trend reporting.

The main delivery is the warehouse and analytics engineering stack: Python ETL, PostgreSQL, dbt, validated marts, and BI-ready exports. Plotly Dash and reporting assets are included as secondary visualization artifacts. An additive **streaming + AI-clean layer** (Redpanda → AI-clean gate → governed warehouse) extends the batch pipeline toward real-time, trustworthy analytics — see the section below.

---

## Why This Project Matters

Retail transaction data is rarely dashboard-ready. It often includes inconsistent fields, returns, missing customer identifiers, mixed grains, and source noise that make direct analysis unreliable.

This project addresses that problem by separating ingestion, cleaning, modeling, and reporting logic. The result is a documented warehouse workflow that produces stable marts for analysis and export, with clear validation and a transparent modeling layer.

---

## Architecture

```mermaid
flowchart LR
    A[Raw Retail Excel / CSV] --> B[Python ETL]
    B --> C[PostgreSQL Warehouse]
    C --> D[dbt Staging Models]
    D --> E[dbt Intermediate Models]
    E --> F[dbt Mart Models]
    F --> G[BI-Ready CSV Exports]
    F --> H[Documentation Layer]
    G --> I[Reporting Consumption]
    H --> I
```

The pipeline starts with raw retail files, processes them through Python ETL, loads the warehouse into PostgreSQL, and then applies dbt to create reusable analytical layers. The mart layer is the main consumption layer for KPI reporting and export workflows.

---

## Streaming + AI-Clean Layer

An additive layer that extends the batch warehouse toward real-time, trustworthy analytics. It ingests a live operational order-event stream and only promotes data it is confident in — the rest is quarantined, never silently guessed. The batch star-schema ETL is untouched; streamed data lands in its own tables.

```mermaid
flowchart LR
    A[Order-event stream] --> B[Redpanda / Kafka API]
    B --> C[AI-clean gate]
    C -->|rule or high-confidence LLM| D[fact_orders_stream]
    C -->|low confidence / ambiguous| E[orders_quarantine]
    C --> F[orders_clean_audit]
    D --> G[dbt trust models]
    E --> G
    F --> G
    G --> H[mart_bi_readiness scorecard]
```

**AI-clean gate** — deterministic rules first; Gemini (called over REST, no SDK) only on genuine ambiguity; and it **abstains** to a quarantine table when confidence is below threshold instead of guessing. Every field decision is audited with method (`rule`/`llm`), confidence, and model.

**Trust by construction:**
- No event is ever dropped — `landed == promoted + quarantined`, enforced by a dbt test.
- A governed semantic catalog (`semantic/metrics.yml`) is the single source of truth for what each metric means.
- `mart_bi_readiness` publishes a 0–100 readiness score with a hard reconciliation gate.

**Verified locally (same 81 landed events, A/B):** rules-only promotes 45 (55.6%); with Gemini-assisted resolution 69 (85.2%) — the LLM rescues 24 typo/variant statuses (`complete!!` → completed, `shipd` → shipped) while correctly abstaining on ambiguous dates and unmappable statuses. dbt build green; reconciliation test passes.

Runs **free** end-to-end: offline (deterministic rules + abstention) with no API key, or Gemini-assisted with a free-tier key. A live trust dashboard runs on `:8051`, and a GitHub Actions workflow runs the whole path as CI plus a near-live scheduled batch. Full setup and run commands: [`streaming/README.md`](streaming/README.md).

---

## Dataset and Scope

The project is built around Online Retail II-style transaction data and modeled for customer and revenue analysis.

### Implemented warehouse concepts
- Invoices and invoice numbers for order-level analysis.
- Customers for customer-level KPIs and repeat purchase metrics.
- Products identified by stock code and product description.
- Countries for geographic reporting.
- Transaction line facts with quantity, invoice date, unit price, and return flag.

### Known reporting metrics
- Average order value.
- Repeat purchase rate.
- Cohort retention rate.
- Cohort revenue over time.
- Customer lifetime value.
- Country revenue.
- Monthly revenue trends.
- Quantity sold.
- Total revenue.
- Total customers.
- Total invoices.

---

## Data Pipeline

```mermaid
flowchart TD
    A[Raw Retail Workbook / CSV] --> B[Python ETL Extraction]
    B --> C[Normalize Headers and Types]
    C --> D[Handle Returns and Guest Checkouts]
    D --> E[Create Warehouse Tables]
    E --> F[Load PostgreSQL Fact and Dimensions]
    F --> G[dbt Build and Test]
    G --> H[Validated Mart Tables]
```

The Python ETL pipeline extracts raw transaction data, normalizes fields, converts types, flags returns, and loads warehouse tables. dbt then validates and transforms the warehouse into staging, intermediate, and mart outputs.

---

## dbt Model Lineage

```mermaid
flowchart LR
    A[Sources] --> B[stg_sales]
    A --> C[stg_customers]
    A --> D[stg_products]
    A --> E[stg_countries]
    B --> F[int_sales_enriched]
    B --> G[int_order_metrics]
    B --> H[int_customer_orders]
    B --> I[int_customer_lifetime_value]
    B --> J[int_country_metrics]
    H --> P[int_customer_cohort_activity]
    F --> K[mart_executive_kpis]
    I --> L[mart_customer_lifetime_value]
    H --> M[mart_repeat_purchase_metrics]
    P --> Q[mart_customer_cohort_retention]
    J --> N[mart_country_revenue]
    G --> O[mart_sales_monthly]
```

Staging models standardize the source data. Intermediate models encode reusable business logic. Mart models expose stable BI-ready tables that can be consumed directly or exported to CSV for reporting workflows.

---

## Key Marts

### `mart_executive_kpis`
Executive summary table for total revenue, total customers, total invoices, average order value, repeat purchase rate, and quantity sold.

### `mart_customer_lifetime_value`
Customer-level revenue ranking for value analysis and prioritization.

### `mart_repeat_purchase_metrics`
Repeat purchase behavior and loyalty-oriented metrics.

### `mart_customer_cohort_retention`
Monthly retention, repeat purchase rate, cohort revenue, and cumulative cohort lifetime value by first purchase month.

### `mart_country_revenue`
Country-level revenue, order count, customer count, and average order value.

### `mart_sales_monthly`
Monthly revenue trend table for time-series reporting.

---

## Validation Results

The dbt implementation is validated and documented.

- 14 dbt models built successfully.
- 41 dbt tests passed.
- dbt documentation generated successfully.
- dbt artifacts available under `target/`.

### Test coverage includes
- `not_null`
- `unique`
- `relationships`
- `accepted_values`

This gives the warehouse a documented, tested analytics layer rather than a collection of standalone SQL files.

---

## BI / Export Flow

```mermaid
flowchart TD
    A[Validated dbt Mart Tables] --> B[Python Export Script]
    B --> C[CSV Files in powerbi/exports]
    C --> D[Power BI Desktop Import]
    D --> E[Power Query Type Cleanup]
    E --> F[Date Table and Reporting Model]
    F --> G[Dashboard / Report Consumption]
```

The repository includes Power BI-ready documentation and a CSV export workflow for the mart layer. The project should be described as Power BI-ready and PL-300-aligned, not as a completed Power BI workbook.

### BI documentation included
- DAX measure definitions.
- Power Query import steps.
- Export workflow documentation.
- Data model guidance for mart consumption.

### Scope note
A `.pbix` file, Power BI screenshots, and Power BI publishing artifacts are not included yet.

---

## Dashboarding / Visualization Artifacts

Plotly Dash and report assets are included as secondary visualization artifacts. They support the portfolio narrative, but they are not the core product.

### Dashboard / report visuals
The Plotly Dash app includes a "Customer Cohort & Retention" report page with KPI cards, a retention heatmap, repeat purchase rate by cohort, and cohort revenue over time.

![Executive Overview Portfolio](reports/executive_overview_portfolio.png)

![Customer Value Portfolio](reports/customer_value_portfolio.png)

![Product Return Risk Portfolio](reports/product_return_risk_portfolio.png)

---

## Repository Structure

```text
Customer Intelligence Data Warehouse/
├── config/
│   └── config.yaml
├── data/
│   ├── processed/
│   └── raw/
│       ├── zips/
│       └── processed/
├── dashboard/
├── dashboards/
│   └── powerbi_requirements.md
├── dbt_project.yml
├── docker-compose.yml
├── models/
├── powerbi/
├── reports/
│   └── model_rebuild_report.md
├── src/
│   ├── etl/
│   ├── export_dbt_marts_for_powerbi.py
│   └── pipeline.py
├── target/
└── README.md
```

---

## How to Run

```bash
docker compose up -d
python src/etl/pipeline.py
export DBT_POSTGRES_PASSWORD='your-local-postgres-password'
dbt run
dbt test
dbt docs generate
python src/export_dbt_marts_for_powerbi.py
```

After running the pipeline, the warehouse is available in PostgreSQL, dbt artifacts are generated in `target/`, and the mart CSV exports are written to `powerbi/exports/`.

---

## Technical Skills Demonstrated

- Python ETL for structured warehouse loading.
- PostgreSQL dimensional modeling.
- dbt staging, intermediate, and mart layer design.
- Data quality testing and documentation.
- BI-ready semantic modeling.
- Export workflows for reporting consumption.
- Warehouse-to-reporting separation of logic.
- Streaming ingestion via Redpanda (Kafka API).
- LLM-assisted data cleaning with confidence-based abstention and full decision lineage.
- Data governance: reconciliation invariants, a semantic metric catalog, and a BI-readiness score.

---

## Tech Stack

- Python
- pandas
- SQLAlchemy
- psycopg2
- PostgreSQL
- dbt
- Docker
- Redpanda (Kafka API)
- Gemini (LLM data cleaning)
- SQL
- Power BI-ready documentation
- Plotly Dash
