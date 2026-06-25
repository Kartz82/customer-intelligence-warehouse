# Customer Intelligence Data Warehouse README Context Report

This report summarizes implemented evidence in the Customer Intelligence Data Warehouse repository for use as context in Perplexity or another AI writing assistant. It is intended to support a README rewrite, recruiter-facing project narrative, architecture explanation, and analytics engineering case study without introducing unsupported claims.

## 1. Executive Summary

The Customer Intelligence Data Warehouse is an end-to-end analytics engineering and BI-ready warehouse project built around Online Retail II-style e-commerce transaction data. The project uses Python ETL to clean and load raw retail transactions into a PostgreSQL warehouse, then uses dbt to transform the warehouse tables into staging, intermediate, and mart models. The dbt MVP is implemented and validated, with 14 models built successfully, 41 dbt tests passing, and dbt documentation generated. The resulting marts support executive KPI reporting, customer lifetime value analysis, repeat purchase analysis, country revenue reporting, and monthly sales trend analysis. The repository also includes Power BI-ready documentation, DAX measure definitions, Power Query import guidance, and a Python export workflow that writes dbt marts to CSV files for BI import. This makes the project strongest as an analytics engineering portfolio project with clear business metrics and a documented path from raw data to trusted BI-ready reporting tables. The project currently has BI documentation and exports, but it does not yet include a completed Power BI `.pbix` file, `.pbit` template, standalone `.pq` files, or Power BI screenshots.

## 2. Business Problem

Online retailers need reliable customer and revenue reporting, but raw transaction exports are not directly ready for executive dashboards or repeatable analysis. Transaction-level retail data often includes returns, missing customer identifiers, inconsistent product descriptions, country-level dimensions, invoice-level order grain, and line-item-level sales records. Analysts need trusted KPI marts that separate raw ingestion from business-ready reporting logic.

This project addresses that problem by building a PostgreSQL warehouse and dbt transformation layer that convert raw e-commerce transactions into validated analytical marts. The marts are designed to answer recurring questions about revenue, customer value, repeat purchase behavior, geographic performance, and monthly sales trends. The repository also documents how those marts can be exported and modeled for Power BI-style reporting without claiming that a finished Power BI report already exists.

## 3. Dataset Context

The project uses Online Retail II-style e-commerce transaction data loaded through a Python ETL pipeline. The raw source is configured as an Excel or CSV input and is transformed into a relational warehouse. Key entities represented in the implementation include invoices, customers, products, countries, and sales transactions.

Implemented data concepts include:

- Invoices and invoice numbers for order-level analysis.
- Customers for known customer-level metrics and repeat purchase analysis.
- Products identified by stock code and product description.
- Countries for geographic revenue reporting.
- Sales transaction lines with quantity, invoice date, unit price, and return/cancellation flag.

Known implemented metrics include:

- Average order value.
- Repeat purchase rate.
- Customer lifetime value.
- Country revenue.
- Monthly revenue trends.
- Quantity sold.
- Total revenue.
- Total customers.
- Total invoices.

## 4. Architecture Overview

The implemented architecture moves data from a raw retail file into PostgreSQL, transforms it through dbt, and exports validated marts for BI use.

```text
Raw Excel/CSV
    |
    v
Python ETL
    |
    v
PostgreSQL Warehouse
    |
    v
dbt Staging Models
    |
    v
dbt Intermediate Models
    |
    v
dbt Mart Models
    |
    v
BI-Ready CSV Exports + Documentation
    |
    v
Plotly / Looker Studio / Power BI-ready Reporting Context
```

Text architecture:

Raw Excel/CSV -> Python ETL -> PostgreSQL warehouse -> dbt staging/intermediate/marts -> BI-ready exports -> Plotly/Looker Studio/Power BI-ready reporting.

The Python ETL handles extraction, cleaning, type normalization, return flagging, dimension creation, and fact table loading. PostgreSQL stores the dimensional warehouse tables. dbt provides the analytics engineering layer, including source definitions, staging models, intermediate models, mart models, and data tests. The BI layer is represented by Power BI documentation, DAX measures, Power Query import steps, dashboard requirements, existing dashboard/report assets, and exported mart CSVs.

## 5. Repository Evidence

Evidence supporting implemented claims:

- `src/etl/pipeline.py`: Python ETL pipeline that extracts raw Excel/CSV data, transforms transaction records, creates clean fields, flags returns, and loads warehouse tables.
- `sql/ddl/schema.sql`: PostgreSQL DDL for `dim_country`, `dim_customer`, `dim_product`, and `fact_sales`.
- `docker-compose.yml`: Docker Compose configuration for PostgreSQL.
- `dbt_project.yml`: dbt project configuration.
- `profiles.example.yml`: example dbt profile configuration.
- `models/sources.yml`: dbt source definitions.
- `models/staging/`: staging models for sales, customers, products, and countries.
- `models/intermediate/`: intermediate analytical models for enriched sales, order metrics, customer orders, customer lifetime value, and country metrics.
- `models/marts/`: BI-ready marts for executive KPIs, customer lifetime value, repeat purchase metrics, country revenue, and monthly sales.
- `powerbi/`: Power BI-ready documentation folder, including data model notes, DAX measures, Power Query steps, export README, and screenshot placeholder README.
- `src/export_dbt_marts_for_powerbi.py`: Python script that exports dbt mart tables from PostgreSQL to CSV files.
- `dashboard/`: Plotly Dash application folder is present.
- `dashboards/powerbi_requirements.md`: Power BI dashboard requirements and planned visual definitions.
- `reports/`: portfolio report image assets are present.
- `assets/`: dashboard image assets are present.
- `target/run_results.json`: dbt run/test artifact showing successful dbt execution results.
- `target/catalog.json` and `target/index.html`: dbt documentation artifacts generated by `dbt docs generate`.

## 6. Data Modeling Layer

The PostgreSQL source warehouse uses a simple dimensional structure:

- `dim_country`: country dimension.
- `dim_customer`: customer dimension.
- `dim_product`: product dimension with stock code, description, and reference unit price.
- `fact_sales`: transaction line fact table with invoice, product, customer, country, quantity, invoice date, unit price, and return flag.

The dbt layer is separated into staging, intermediate, and mart models.

Staging models:

- `stg_sales`
- `stg_customers`
- `stg_products`
- `stg_countries`

Intermediate models:

- `int_sales_enriched`
- `int_order_metrics`
- `int_customer_orders`
- `int_customer_lifetime_value`
- `int_country_metrics`

Mart models:

- `mart_executive_kpis`
- `mart_customer_lifetime_value`
- `mart_repeat_purchase_metrics`
- `mart_country_revenue`
- `mart_sales_monthly`

This separation matters because each layer has a distinct responsibility. Staging models standardize and document source tables while preserving source grain. Intermediate models encode reusable business logic such as invoice-level metrics, customer order history, enriched sales records, lifetime value, and country-level rollups. Mart models expose stable, BI-ready outputs that can be consumed by dashboards, CSV exports, or semantic-layer documentation without requiring dashboard authors to rebuild business logic.

## 7. dbt Implementation Summary

Implemented dbt model count:

- 4 staging models.
- 5 intermediate models.
- 5 mart models.
- 14 total dbt models.

Validation status:

- `dbt run` passed for 14/14 models.
- `dbt test` passed for 41/41 tests.
- `dbt docs generate` passed and generated dbt documentation artifacts.
- dbt artifacts exist under `target/`, including `run_results.json`, `manifest.json`, `catalog.json`, and `index.html`.

Test types present in schema files:

- `not_null`
- `unique`
- `relationships`
- `accepted_values`

Examples of tested fields include:

- Unique and non-null transaction identifiers in staging and intermediate models.
- Unique and non-null customer identifiers where appropriate.
- Unique product stock codes.
- Non-null invoice, stock code, quantity, invoice date, and unit price fields.
- Relationship tests from enriched sales to product, customer, and country staging models.
- Accepted boolean values for return flags.
- Unique and non-null monthly mart month values.

## 8. BI and Reporting Layer

The repository includes a Power BI-ready reporting documentation layer under `powerbi/`. This folder documents how the dbt marts can be exported and imported into Power BI Desktop as a compact semantic layer.

Implemented BI-related evidence:

- `powerbi/README.md`: explains the Power BI-ready semantic layer and export workflow, and explicitly states that a `.pbix` file is not included yet.
- `powerbi/data_model.md`: describes exported mart grains, recommended reporting model, Date table guidance, and honest scope.
- `powerbi/dax_measures.md`: documents DAX measures for executive KPIs, customer lifetime value, repeat purchase metrics, monthly sales, and country revenue.
- `powerbi/power_query_steps.md`: documents Power Query import and data type steps for CSV mart exports.
- `powerbi/exports/README.md`: documents the export workflow and notes the Excel workbook for Power BI Service browser import.
- `src/export_dbt_marts_for_powerbi.py`: exports the five dbt marts to CSV from PostgreSQL.
- `powerbi/exports/customer_intelligence_powerbi.xlsx`: workbook combining the mart exports for Power BI Service browser import.
- `dashboards/powerbi_requirements.md`: describes planned Power BI dashboard pages and visuals.
- `dashboard/app.py`: Plotly Dash application exists.
- `assets/` and `reports/`: dashboard/report image assets exist.

CSV export workflow generated five mart exports:

| Export | Rows |
|---|---:|
| `mart_executive_kpis.csv` | 1 |
| `mart_customer_lifetime_value.csv` | 5,047 |
| `mart_repeat_purchase_metrics.csv` | 1 |
| `mart_country_revenue.csv` | 42 |
| `mart_sales_monthly.csv` | 25 |

BI scope caveat:

Actual `.pbix`, `.pbit`, `.pq`, Power BI screenshots, and Power BI Service publishing artifacts are not included yet. The project should be described as Power BI-ready or PL-300-aligned documentation and export workflow, not as a completed Power BI report.

## 9. Key Metrics and Business Questions

| Metric | Source Mart | Business Question | Use Case |
|---|---|---|---|
| Total Revenue | `mart_executive_kpis` | How much positive-sale revenue did the business generate? | Executive KPI reporting |
| Total Customers | `mart_executive_kpis` | How many known customers are represented in the reporting layer? | Executive/customer base reporting |
| Total Invoices | `mart_executive_kpis` | How many distinct invoices/orders were processed? | Sales volume reporting |
| Average Order Value | `mart_executive_kpis`, `mart_country_revenue` | What is the average revenue per invoice overall or by country? | Revenue quality and basket-size analysis |
| Repeat Purchase Rate | `mart_executive_kpis`, `mart_repeat_purchase_metrics` | What share of known customers placed more than one invoice? | Retention and loyalty reporting |
| Customer Lifetime Value | `mart_customer_lifetime_value` | Which customers have generated the most total positive-sale revenue? | Customer value and prioritization analysis |
| Country Revenue | `mart_country_revenue` | Which countries contribute the most revenue, invoices, customers, and AOV? | Geographic performance reporting |
| Monthly Sales | `mart_sales_monthly` | How does revenue trend by month? | Time-series sales reporting |
| Quantity Sold | `mart_executive_kpis`, `mart_sales_monthly` | How many units were sold overall or by month? | Sales volume and demand trend analysis |

## 10. Technical Skills Demonstrated

### SQL & Data Modeling

- Dimensional warehouse design with fact and dimension tables.
- SQL DDL for PostgreSQL warehouse tables.
- dbt model design across staging, intermediate, and mart layers.
- KPI mart design for executive reporting, customer value, repeat purchase, country revenue, and monthly sales.

### Python ETL

- Raw Excel/CSV extraction.
- Multi-sheet Excel ingestion.
- Transaction cleaning and column standardization.
- Type conversion for customer IDs, quantities, prices, and invoice dates.
- Return/cancellation flagging.
- Warehouse loading with SQLAlchemy and pandas.

### PostgreSQL

- Dockerized PostgreSQL setup.
- Relational warehouse tables.
- Primary keys and foreign key relationships in the warehouse schema.
- dbt transformations running against PostgreSQL.

### dbt Analytics Engineering

- dbt project configuration.
- Source definitions.
- Staging, intermediate, and mart models.
- dbt run/test/docs workflow.
- Documentation artifacts generated by dbt.

### Data Quality Testing

- 41 dbt tests passing.
- `not_null`, `unique`, `relationships`, and `accepted_values` tests.
- Model-level and column-level documentation in schema YAML files.

### BI Modeling

- BI-ready marts with clear grains.
- Power BI data model guidance.
- Date table recommendation for monthly trends.
- Guidance on not forcing relationships between independent summary marts.

### Power BI-ready Reporting

- DAX measure documentation.
- Power Query transformation-step documentation.
- CSV export workflow for mart imports.
- Excel workbook combining mart exports for Power BI Service browser import.
- PL-300-aligned modeling documentation without claiming a completed `.pbix`.

### Dashboarding / Visualization

- Plotly Dash application folder is present.
- Dashboard/report image assets exist under `assets/` and `reports/`.
- Power BI dashboard requirements document exists.

### Documentation

- Main README exists.
- Power BI documentation exists.
- dbt model and column documentation exists.
- Export documentation exists under `powerbi/exports/`.

## 11. Resume-Safe Claims

The following claims are currently safe based on implemented repository evidence:

- Built a PostgreSQL customer analytics warehouse for Online Retail II-style e-commerce transaction data.
- Developed a Python ETL pipeline to extract, clean, transform, and load retail transaction data into PostgreSQL.
- Implemented a dbt MVP with staging, intermediate, and mart models.
- Built 14 dbt models across 4 staging models, 5 intermediate models, and 5 mart models.
- Validated the dbt project with 41 passing dbt tests.
- Generated dbt documentation artifacts.
- Created BI-ready marts for executive KPIs, customer lifetime value, repeat purchase metrics, country revenue, and monthly sales.
- Documented a Power BI-ready semantic layer and reporting workflow.
- Documented DAX measures for executive, customer, repeat purchase, monthly sales, and country revenue reporting.
- Documented Power Query transformation steps for importing dbt mart CSV exports.
- Built a CSV export workflow for Power BI-ready mart exports.
- Generated five mart CSV exports for BI import.
- Created a combined Excel workbook for Power BI Service browser import.
- Included Plotly/dashboard assets only to the extent represented by `dashboard/`, `assets/`, and `reports/` files.

## 12. Claims Not Yet Safe

The following claims should not be made yet:

- Completed Power BI `.pbix` report.
- Power BI `.pbit` template.
- Standalone `.pq` Power Query files.
- Power BI screenshots.
- Power BI Service publishing.
- Airflow orchestration.
- Full RFM dbt marts.
- Churn-risk dbt marts.
- Product return-risk dbt marts.
- Finished Power BI production dashboard.
- Real business deployment for a company.
- Cloud deployment unless separate deployment evidence is added.

## 13. Recommended README Improvements

Recommended README structure:

1. Hero summary
   - One concise paragraph positioning the project as an analytics engineering and BI-ready customer intelligence warehouse.
   - Mention PostgreSQL, Python ETL, dbt, data quality tests, and BI-ready marts.

2. Architecture diagram
   - Include the pipeline from raw Online Retail II data to Python ETL, PostgreSQL, dbt models, mart exports, and BI-ready reporting.

3. Business problem
   - Explain why raw retail transactions need cleaning, modeling, validation, and trusted KPI marts.

4. Data pipeline
   - Describe extraction, cleaning, return flagging, dimension loading, and fact table loading.

5. dbt model lineage
   - Show staging, intermediate, and mart layers.
   - Explain why each layer exists.

6. Key marts
   - Summarize each mart, its grain, and its intended dashboard use.

7. Validation results
   - Highlight 14/14 dbt models built, 41/41 dbt tests passed, and dbt docs generated.

8. BI/reporting layer
   - Explain Power BI-ready documentation, DAX measures, Power Query steps, CSV exports, and the Excel workbook.
   - Explicitly state that `.pbix`, `.pbit`, `.pq`, and Power BI screenshots are not included yet.

9. Screenshots section
   - Use existing dashboard/report images where accurate.
   - Keep Power BI screenshots as a future addition only.

10. How to run locally
    - Docker Compose for PostgreSQL.
    - Python ETL.
    - dbt run/test/docs.
    - Power BI export script.

11. Resume bullets
    - Include safe bullets grounded in the implemented repo.

12. Future improvements
    - Completed Power BI `.pbix`.
    - Power BI screenshots.
    - dbt exposures or metrics layer.
    - RFM marts.
    - Churn-risk marts.
    - Product return-risk marts.
    - Orchestration only after implemented.

## 14. Perplexity Prompt

Using the project context above, rewrite my GitHub README into a recruiter-friendly analytics engineering case study. Keep it technically accurate, avoid unsupported claims, emphasize PostgreSQL, Python ETL, dbt, data quality tests, BI-ready marts, PL-300-aligned Power BI documentation, and business metrics. Do not claim .pbix, Airflow, Power BI screenshots, or Power BI publishing.
