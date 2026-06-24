# Power Query Steps

This file documents planned Power Query transformation steps for importing dbt mart CSV exports into Power BI Desktop. It does not include fake `.pq` files or Power Query M scripts.

## 1. Import CSVs

Use **Get Data > Text/CSV** and import files from `powerbi/exports/`:

- `mart_executive_kpis.csv`
- `mart_customer_lifetime_value.csv`
- `mart_repeat_purchase_metrics.csv`
- `mart_country_revenue.csv`
- `mart_sales_monthly.csv`

## 2. Set Data Types

Recommended types:

| Table | Column | Power Query Type |
|---|---|---|
| `mart_executive_kpis` | `total_revenue` | Decimal number |
| `mart_executive_kpis` | `total_invoices` | Whole number |
| `mart_executive_kpis` | `total_customers` | Whole number |
| `mart_executive_kpis` | `aov` | Decimal number |
| `mart_executive_kpis` | `repeat_purchase_rate` | Decimal number |
| `mart_executive_kpis` | `total_quantity_sold` | Whole number |
| `mart_customer_lifetime_value` | `customer_id` | Text or whole number |
| `mart_customer_lifetime_value` | `total_revenue` | Decimal number |
| `mart_customer_lifetime_value` | `order_count` | Whole number |
| `mart_customer_lifetime_value` | `first_order_date` | Date/time |
| `mart_customer_lifetime_value` | `last_order_date` | Date/time |
| `mart_customer_lifetime_value` | `customer_lifetime_value` | Decimal number |
| `mart_repeat_purchase_metrics` | `repeat_customers` | Whole number |
| `mart_repeat_purchase_metrics` | `total_customers` | Whole number |
| `mart_repeat_purchase_metrics` | `repeat_purchase_rate` | Decimal number |
| `mart_country_revenue` | `country_name` | Text |
| `mart_country_revenue` | `total_revenue` | Decimal number |
| `mart_country_revenue` | `invoice_count` | Whole number |
| `mart_country_revenue` | `customer_count` | Whole number |
| `mart_country_revenue` | `aov` | Decimal number |
| `mart_sales_monthly` | `month` | Date |
| `mart_sales_monthly` | `revenue` | Decimal number |
| `mart_sales_monthly` | `invoice_count` | Whole number |
| `mart_sales_monthly` | `quantity_sold` | Whole number |

## 3. Rename Columns for Readability

Examples:

- `total_revenue` -> `Total Revenue`
- `total_invoices` -> `Total Invoices`
- `customer_lifetime_value` -> `Customer Lifetime Value`
- `repeat_purchase_rate` -> `Repeat Purchase Rate`
- `country_name` -> `Country`
- `quantity_sold` -> `Quantity Sold`

## 4. Remove Duplicate Rows Where Valid

- `mart_customer_lifetime_value`: remove duplicates by `customer_id` only if duplicates appear.
- `mart_country_revenue`: remove duplicates by `country_name` only if duplicates appear.
- `mart_sales_monthly`: remove duplicates by `month` only if duplicates appear.
- Do not deduplicate summary KPI tables unless an import issue creates accidental repeated rows.

## 5. Ensure Date Handling

- Convert `mart_sales_monthly[month]` to Date.
- Convert customer first and last order fields to Date/time or Date.
- Create or import a Date table for trend visuals.

## 6. Create or Import Date Table

Recommended Date table fields:

- Date
- Year
- Quarter
- Month Number
- Month Name
- Year-Month

Relate `Date[Date]` to `mart_sales_monthly[month]`.

## 7. Disable Load for Helper Queries

If helper queries are created for file paths, parameters, or Date table generation, disable load where appropriate so only final reporting tables appear in the model.

## 8. Load Final Reporting Tables

Load these tables:

- `mart_executive_kpis`
- `mart_customer_lifetime_value`
- `mart_repeat_purchase_metrics`
- `mart_country_revenue`
- `mart_sales_monthly`
- `Date`

## Current Scope

These are documented Power Query steps. Actual Power Query M files are not included in this phase.
