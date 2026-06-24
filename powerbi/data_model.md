# Power BI Data Model

This model is designed around dbt mart exports. The exported CSVs are reporting-ready summary tables, not a fully normalized star schema. In Power BI, they can be loaded as a compact semantic layer for dashboarding and PL-300-style modeling practice.

## Exported Tables and Grain

| Table | Grain | Notes |
|---|---|---|
| `mart_executive_kpis` | One row for overall business KPIs | Summary table for KPI cards. |
| `mart_customer_lifetime_value` | One row per known customer | Customer-level table for LTV, order count, first order date, and last order date. |
| `mart_repeat_purchase_metrics` | One row for overall repeat purchase summary | Summary table for repeat purchase KPI cards. |
| `mart_country_revenue` | One row per country | Country-level reporting table for revenue, invoices, customers, and AOV. |
| `mart_sales_monthly` | One row per month | Monthly trend table for revenue, invoice count, and quantity sold. |

## Fact-Like Tables

- `mart_sales_monthly`: trend fact by month.
- `mart_customer_lifetime_value`: customer-level fact-like table.
- `mart_country_revenue`: country-level fact-like table.

These tables are pre-aggregated marts. They should not be summed together unless the dashboard page is intentionally using their own grain.

## Dimension-Like Tables

No dedicated exported dimension tables are included in this MVP export. Recommended helper dimensions in Power BI:

- `Date`: generated in Power BI or Power Query and related to `mart_sales_monthly[month]`.
- Optional disconnected metric selector table for KPI switching.

## Recommended Relationships

- `Date[Date]` one-to-many to `mart_sales_monthly[month]`.

The customer and country marts are independent summary tables in this phase. Do not force relationships between customer, country, and monthly summary tables unless lower-grain fact tables are exported later.

## Recommended Reporting Model

Use a report-page model:

- Executive Overview: `mart_executive_kpis`, `mart_sales_monthly`, `mart_country_revenue`
- Customer LTV: `mart_customer_lifetime_value`
- Repeat Purchase & Retention: `mart_repeat_purchase_metrics`, `mart_customer_lifetime_value`
- Country Revenue: `mart_country_revenue`
- Monthly Sales Trends: `mart_sales_monthly`, `Date`

## Date Table Recommendation

Create a Date table in Power BI with:

- Date
- Year
- Quarter
- Month Number
- Month Name
- Year-Month

Relate `Date[Date]` to `mart_sales_monthly[month]`. Mark the Date table as the official date table.

## Honest Scope

This Power BI model is a documented semantic-layer plan plus CSV export workflow. A `.pbix` model file is pending and should only be claimed after it is created.
