# Dashboard Rebuild Audit

Customer Intelligence Data Warehouse audit for a future Plotly Dash rebuild. This report is based only on local repository inspection; no dashboard code, SQL, ETL, data, reports, or images were modified.

## 1. Repo Structure Summary

| Path | Purpose |
| --- | --- |
| `data/raw/` | Raw source data. Contains `online_retail_II.xlsx`, the UCI Online Retail II workbook with two yearly sheets. |
| `data/processed/` | Local CSV exports intended for BI/dashboard consumption. Contains monthly revenue, top customers, country revenue, top products, and enriched fact sales. |
| `sql/ddl/` | Warehouse DDL. Defines `dim_country`, `dim_customer`, `dim_product`, and `fact_sales`. |
| `sql/analytics/` | Standalone SQL metric queries for monthly revenue, top customers, AOV, repeat purchase rate, and customer cohort size. |
| `src/etl/` | Python ETL pipeline that extracts the Excel workbook, cleans fields, and loads a PostgreSQL star schema. |
| `src/export_for_bi.py` | Python export script that queries PostgreSQL and writes dashboard-ready CSVs into `data/processed/`. |
| `dashboards/` | Reporting requirements. Contains `powerbi_requirements.md`, a semantic/dashboard spec that maps closely to the intended Dash rebuild. |
| `assets/` | Existing manually created Looker Studio PNG screenshots: executive overview, customer analysis, product performance, geographic view. |
| `config/` | Database and source-path configuration for the ETL pipeline. |
| `docker-compose.yml` | PostgreSQL 15 warehouse container on host port `5433`. |
| `README.md` | Project overview, architecture, dataset profile, warehouse design, ETL flow, and sample analytics outputs. |
| `customer-segmentation-rfm/` | Untracked nested repo/folder. Only a placeholder README was present, so it does not currently provide usable dashboard logic. |

## 2. Available Data Sources

### `data/raw/online_retail_II.xlsx`

Raw Excel workbook with two sheets and 1,067,371 total rows.

| Sheet | Rows | Columns | Inferred Types | Date Columns | Customer Columns | Product Columns | Geography Columns | Revenue/Sales Columns | Return/Cancellation Columns | Quantity/Unit Columns |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Year 2009-2010` | 525,461 | `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country` | invoice/object, stock/object, description/object, quantity/int, date/datetime, price/float, customer/float, country/object | `InvoiceDate`, 2009-12-01 to 2010-12-09 | `Customer ID` | `StockCode`, `Description` | `Country` | `Price`; line revenue can be inferred as `Quantity * Price` | Cancelled invoices start with `C`; 12,326 negative-quantity rows; 10,206 `C` invoice rows | `Quantity`, `Price` |
| `Year 2010-2011` | 541,910 | Same as above | Same as above | `InvoiceDate`, 2010-12-01 to 2011-12-09 | `Customer ID` | `StockCode`, `Description` | `Country` | `Price`; line revenue can be inferred as `Quantity * Price` | Cancelled invoices start with `C`; 10,624 negative-quantity rows; 9,288 `C` invoice rows | `Quantity`, `Price` |

Raw quality profile:

| Sheet | Missing Customers | Missing Descriptions | Zero Price Rows | Negative Price Rows | Unique Invoices | Unique Customers | Unique Stock Codes | Unique Countries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Year 2009-2010` | 107,927 | 2,928 | 3,687 | 3 | 28,816 | 4,383 | 4,632 | 40 |
| `Year 2010-2011` | 135,080 | 1,454 | 2,515 | 2 | 25,900 | 4,372 | 4,070 | 38 |

### `data/processed/fact_sales_enriched.csv`

Dashboard-ready fact export.

| Attribute | Value |
| --- | --- |
| Rows | 133,465 |
| Columns | `sale_id`, `invoice_number`, `stock_code`, `customer_id`, `quantity`, `invoice_date`, `unit_price`, `is_return`, `line_revenue`, `country_name`, `product_name` |
| Inferred Types | `sale_id` int, `invoice_number` object, `stock_code` object, `customer_id` float due to nulls, `quantity` int, `invoice_date` object/datetime, `unit_price` float, `is_return` bool, `line_revenue` float, `country_name` object, `product_name` object |
| Date Columns | `invoice_date`, 2009-12-01 07:45:00 to 2011-12-09 12:50:00 |
| Customer Columns | `customer_id`; 5,047 non-null unique customers; 38,914 guest/null rows |
| Product Columns | `stock_code`, `product_name`; 1,537 stock codes; 1,310 product names |
| Geography Columns | `country_name`; 42 countries |
| Revenue/Sales Columns | `unit_price`, `line_revenue`; line revenue equals `quantity * unit_price` |
| Return/Cancellation Columns | `is_return`; 3,650 return rows; 3,424 invoice numbers starting with `C` |
| Quantity/Unit Columns | `quantity`; positive units 1,243,730; net units 1,121,959; returned units by absolute negative quantity 121,771 |

Important lineage note: this processed fact export has 133,465 rows, far fewer than the 1,067,371 raw workbook rows and fewer than the 1,062,984 cleaned rows cited in `README.md`. Confirm whether the local PostgreSQL warehouse export was intentionally partial before treating the dashboard totals as final.

### `data/processed/monthly_revenue.csv`

| Attribute | Value |
| --- | --- |
| Rows | 25 |
| Columns | `month`, `revenue` |
| Inferred Types | `month` object/date, `revenue` float |
| Date Columns | `month`, 2009-12-01 to 2011-12-01 |
| Revenue/Sales Columns | `revenue`, sum 3,279,364.61 |
| Formula Source | `SUM(quantity * unit_price)` where `quantity > 0`, grouped by month |

### `data/processed/top_customers.csv`

| Attribute | Value |
| --- | --- |
| Rows | 50 |
| Columns | `customer_id`, `lifetime_value`, `total_orders` |
| Inferred Types | all numeric |
| Customer Columns | `customer_id` |
| Revenue/Sales Columns | `lifetime_value`, sum of top 50 = 851,183.44 |
| Quantity/Unit Columns | none |
| Formula Source | `SUM(quantity * unit_price)` where `quantity > 0 AND customer_id IS NOT NULL`; `COUNT(DISTINCT invoice_number)` |

### `data/processed/country_revenue.csv`

| Attribute | Value |
| --- | --- |
| Rows | 42 |
| Columns | `country_name`, `revenue`, `order_count` |
| Inferred Types | country object, revenue float, order count int |
| Geography Columns | `country_name` |
| Revenue/Sales Columns | `revenue`, sum 3,279,364.61 |
| Quantity/Unit Columns | none |
| Formula Source | positive-quantity revenue and distinct invoice count by country |

### `data/processed/top_products.csv`

| Attribute | Value |
| --- | --- |
| Rows | 50 |
| Columns | `product_name`, `stock_code`, `revenue`, `units_sold`, `avg_price`, `return_rate_percentage` |
| Inferred Types | product/object, stock/object, revenue/float, units/int, avg price/float, return rate/float |
| Product Columns | `product_name`, `stock_code` |
| Revenue/Sales Columns | `revenue`, `avg_price` |
| Return/Cancellation Columns | `return_rate_percentage` |
| Quantity/Unit Columns | `units_sold` |
| Formula Source | Product aggregation in `src/export_for_bi.py`; limited to top 50 by revenue |

## 3. Database/Schema Audit

The project contains a clear star-schema intent.

### Dimension Tables

| Table | Primary Key | Grain | Columns | Notes |
| --- | --- | --- | --- | --- |
| `dim_country` | `country_id` | One row per normalized country name | `country_id`, `country_name` | `country_name` is unique and not null. |
| `dim_customer` | `customer_id` | One row per known customer | `customer_id` | Guest/null customers are intentionally excluded from this dimension. |
| `dim_product` | `stock_code` | One row per stock code | `stock_code`, `description`, `unit_price_reference` | `stock_code` is the product key. Descriptions are last observed by invoice date in ETL. |

### Fact Table

| Table | Primary Key | Grain | Columns | Foreign Keys |
| --- | --- | --- | --- | --- |
| `fact_sales` | `sale_id` | One invoice line / stock-code transaction line | `sale_id`, `invoice_number`, `stock_code`, `customer_id`, `country_id`, `quantity`, `invoice_date`, `unit_price` | `stock_code -> dim_product.stock_code`, `customer_id -> dim_customer.customer_id`, `country_id -> dim_country.country_id` |

Available joins:

| Join | Type | Purpose |
| --- | --- | --- |
| `fact_sales.stock_code = dim_product.stock_code` | Many-to-one | Add product description/reference price. |
| `fact_sales.customer_id = dim_customer.customer_id` | Many-to-one, nullable fact key | Customer analytics, excluding guest checkouts if required. |
| `fact_sales.country_id = dim_country.country_id` | Many-to-one | Geography analytics. |

Schema concerns:

- Star schema exists and is appropriate for Dash.
- `schema.sql` does not define `fact_sales.is_return`, but `src/etl/pipeline.py`, `src/export_for_bi.py`, and `dashboards/powerbi_requirements.md` reference `is_return`.
- `src/export_for_bi.py` works around return status by recalculating `CASE WHEN f.quantity < 0 THEN true ELSE false END AS is_return`.
- `src/etl/pipeline.py` attempts to include `is_return` in `fact_sales.to_sql`; this would fail or silently depend on a database schema that differs from `sql/ddl/schema.sql`.
- The warehouse model is dimensional, but there is no date dimension, no customer geography dimension, no explicit order header fact, and no materialized dashboard query layer beyond CSV exports.

## 4. Existing ETL/Reporting Logic

| File | Function/Query | Output Columns | Metric Definition / Role |
| --- | --- | --- | --- |
| `src/etl/pipeline.py` | `CustomerIntelligenceETL.extract` | Raw dataframe columns from workbook | Reads all Excel sheets and concatenates them. |
| `src/etl/pipeline.py` | `CustomerIntelligenceETL.transform` | `invoice_number`, `stock_code`, `description`, `quantity`, `invoice_date`, `unit_price`, `customer_id`, `country`, `is_return` | Normalizes headers, drops missing stock/description, casts types, strips country text, removes negative prices, flags invoice numbers starting with `C`. |
| `src/etl/pipeline.py` | `CustomerIntelligenceETL.load_warehouse` | Loads `dim_country`, `dim_customer`, `dim_product`, `fact_sales` | Truncate-and-reload warehouse; builds dimensions and fact table. Product description/reference price are last observed by stock code. |
| `src/export_for_bi.py` | Enriched fact export | `sale_id`, `invoice_number`, `stock_code`, `customer_id`, `quantity`, `invoice_date`, `unit_price`, `is_return`, `line_revenue`, `country_name`, `product_name` | Joins fact to country/product; defines `is_return` as `quantity < 0`; defines `line_revenue = quantity * unit_price`. |
| `src/export_for_bi.py` | Monthly velocity export | `month`, `revenue` | `SUM(quantity * unit_price)` where `quantity > 0`, grouped by month. |
| `src/export_for_bi.py` | Top customers export | `customer_id`, `lifetime_value`, `total_orders` | Positive-quantity revenue and distinct invoice count per non-null customer; top 50 by LTV. |
| `src/export_for_bi.py` | Country revenue export | `country_name`, `revenue`, `order_count` | Positive-quantity revenue and distinct invoice count by country. |
| `src/export_for_bi.py` | Top products export | `product_name`, `stock_code`, `revenue`, `units_sold`, `avg_price`, `return_rate_percentage` | Product revenue from positive quantities only; units sold from positive quantities; average unit price; return rate as negative-line count divided by all product line rows. |
| `sql/analytics/monthly_revenue.sql` | Monthly revenue query | `month`, `revenue` | Positive-quantity revenue by month. |
| `sql/analytics/top_customers.sql` | Top customers query | `customer_id`, `lifetime_value`, `total_orders` | Positive-quantity LTV and order count, top 20. |
| `sql/analytics/avg_order_value.sql` | AOV query | `avg_order_value` | Average of invoice-level totals where `quantity > 0`. |
| `sql/analytics/repeat_purchase_rate.sql` | Repeat purchase rate query | `repeat_purchase_rate_pct` | Percent of non-null customers with more than one distinct invoice. Does not filter returns. |
| `sql/analytics/customer_retention.sql` | Cohort size query | `cohort_month`, `cohort_size` | Counts customers by first-order month. It is not yet a full retention matrix. |
| `dashboards/powerbi_requirements.md` | BI semantic spec | N/A | Defines intended pages, filters, and measures such as total revenue, orders, customers, return rate, AOV, repeat purchase rate. |

## 5. Metric Definitions

### Executive Metrics

| Metric | Formula | Current Availability |
| --- | --- | --- |
| Gross Revenue / Total Revenue | `SUM(quantity * unit_price)` where `quantity > 0` | Available. Processed export total: 3,279,364.61. |
| Net Revenue | `SUM(quantity * unit_price)` across all lines, including negative quantities | Available from `fact_sales_enriched.csv`. Current net: 2,403,258.63. |
| Return Value | `SUM(quantity * unit_price)` where `quantity < 0` | Available. Current value: -876,105.98. |
| Total Units Sold | `SUM(quantity)` where `quantity > 0` | Available. Current positive units: 1,243,730. |
| Net Units | `SUM(quantity)` across all lines | Available. Current net units: 1,121,959. |
| Returned Units | `ABS(SUM(quantity where quantity < 0))` | Available. Current returned units: 121,771. |
| Active Customers | `COUNT(DISTINCT customer_id)` where `customer_id IS NOT NULL` | Available. Current count: 5,047. |
| Total Transactions / Orders | `COUNT(DISTINCT invoice_number)` | Available. Current all invoices: 29,172; positive-invoice count used for AOV: 26,538. |
| Average Order Value | `AVG(invoice_total)` for invoice totals where `quantity > 0` | Available. Current AOV: 123.57. |
| Repeat Purchase Rate | `customers with >1 distinct invoice / all known customers` | Available. Current rate: 67.25%. |
| Monthly Revenue | `SUM(quantity * unit_price)` where `quantity > 0`, grouped by month | Available for 25 months, no missing months. |

### Customer Metrics

| Metric | Formula | Current Availability |
| --- | --- | --- |
| Lifetime Value / LTV | `SUM(quantity * unit_price)` where `quantity > 0`, by `customer_id` | Available for non-null customers. |
| Order Frequency | `COUNT(DISTINCT invoice_number)` by `customer_id` | Available. |
| Recency | `MAX(invoice_date)` by `customer_id`; optionally days since latest dataset date | Not pre-exported, but computable from enriched fact. |
| Customer Rank | Rank customers by LTV, order count, or net revenue | Computable from enriched fact or `top_customers.csv`. |
| Top Customers | Top N by LTV | Available in `top_customers.csv`, limited to 50. |
| Repeat Customers | Customers with `COUNT(DISTINCT invoice_number) > 1` | Computable. Current count: 3,394. |
| Cohort Size | First purchase month by customer | SQL exists. Full retention over time is not implemented but can be computed from fact data. |

### Product Metrics

| Metric | Formula | Current Availability |
| --- | --- | --- |
| Units Sold | `SUM(quantity)` where `quantity > 0`, by product | Available. |
| Net Revenue by Product | `SUM(quantity * unit_price)` across all lines by product | Computable from enriched fact. |
| Gross Revenue by Product | `SUM(quantity * unit_price)` where `quantity > 0`, by product | Available in `top_products.csv`, top 50 only. |
| Return Rate % | Current export: `COUNT(lines where quantity < 0) / COUNT(all product lines) * 100` | Available for top 50 products. Better dashboard should also compute returned-units rate. |
| Cancelled/Returned Quantity | `ABS(SUM(quantity where quantity < 0))` by product | Computable from enriched fact. |
| High-Return Products | Products with high return-line rate or returned-unit rate, with volume threshold | Computable. |
| Product Profitability/Risk | True profit is not available because cost/margin is absent. Risk can be modeled using revenue, return rate, returned units, and line volume. |

### Geography Metrics

| Metric | Formula | Current Availability |
| --- | --- | --- |
| Revenue by Country | `SUM(quantity * unit_price)` where `quantity > 0`, by country | Available. |
| Order Volume by Country | `COUNT(DISTINCT invoice_number)` by country | Available. |
| Customer Count by Country | `COUNT(DISTINCT customer_id)` by country | Computable from enriched fact. |
| Average Order Value by Country | Positive revenue by country divided by positive distinct invoices by country | Computable. |
| Country Revenue Share | Country revenue divided by total positive revenue | Computable. |

## 6. Data Quality Notes

- Missing customer IDs are significant. The processed fact export has 38,914 null customer rows, 29.16% of rows. The raw workbook has 243,007 missing customer rows across both sheets.
- Cancelled invoices and negative quantities are present. Processed fact has 3,650 negative-quantity return rows and 3,424 invoice rows starting with `C`. Raw data has 22,950 negative-quantity rows and 19,494 `C` invoice rows.
- `is_return` logic is inconsistent across files. ETL uses invoice prefix `C`; export uses `quantity < 0`; DDL does not define `is_return`.
- Negative prices exist in raw data but are filtered by ETL. Raw workbook has 5 negative-price rows.
- Zero-price rows exist. Raw workbook has 6,202 zero-price rows; processed export has 367 zero-price rows.
- Product descriptions are missing in raw data but dropped during transform. Raw workbook has 4,382 missing descriptions.
- Duplicate-looking fact lines exist. Processed fact has 3,869 duplicate rows when excluding `sale_id` and comparing invoice/stock/customer/date/quantity/price/country/product. These may be legitimate repeated line items, but dashboard deduplication should not be assumed.
- Currency appears to be GBP/UK retail pricing by dataset context, but no currency column exists.
- Country naming includes values that may need mapping for Plotly maps: `EIRE`, `RSA`, `USA`, `Unspecified`, `European Community`, `Channel Islands`, `West Indies`.
- Processed country count is 42, while `README.md` says 43 countries. This may reflect filtering or a partial export.
- Date coverage for processed positive monthly revenue is complete from 2009-12 through 2011-12 with no missing months.
- Outliers exist in processed data: 244 rows have `unit_price > 1000`; 67 rows have `ABS(quantity) > 1000`; max unit price is 38,970 and min quantity is -5,368.
- Product-level export includes operational/non-product codes such as `M`/Manual, `DOT`/DOTCOM POSTAGE, `D`/Discount, `CRUK`/CRUK Commission, damages, and ebay rows. A professional dashboard should let users include/exclude these.
- Top product export is limited to 50 products, so product distribution, Pareto, and risk analysis should use `fact_sales_enriched.csv` or direct database queries instead of only `top_products.csv`.

## 7. Recommended Plotly Dash Dashboard Structure

### Tab 1: Executive Overview

Business question: How is the business performing overall, and is revenue trending up or down?

Recommended content:

- KPI cards: Gross Revenue, Net Revenue, Total Units Sold, Active Customers, Total Transactions, AOV, Return Rate %.
- Monthly revenue trend line with optional net revenue overlay.
- Revenue by top countries horizontal bar.
- Revenue concentration cards: UK share, top 10 customer share, top 10 product share.
- Filters: date range, country, include/exclude returns, include/exclude non-product stock codes.

### Tab 2: Customer Intelligence

Business question: Who are the most valuable customers, and how loyal/repeat-driven is the customer base?

Recommended content:

- KPI cards: Active Customers, Repeat Purchase Rate, Median LTV, Average Order Frequency, Guest Checkout Row %.
- Top customers by LTV table and bar chart.
- Order frequency distribution histogram.
- LTV vs order frequency scatter.
- Optional RFM table if recency is computed.
- Filters: date range, country, minimum orders, customer search.

### Tab 3: Product & Return Audit

Business question: Which products drive revenue, and which create return or operational risk?

Recommended content:

- KPI cards: Product Count, Units Sold, Returned Units, Return Rate %, Return Value.
- Top products by gross revenue.
- Product return rate audit table with volume thresholds.
- Revenue vs return rate scatter.
- Product return-risk matrix using revenue and return rate.
- Filters: product search, stock code, minimum revenue, minimum units, include/exclude operational codes.

### Tab 4: Geographic Performance

Business question: Which countries produce revenue, volume, and efficient orders?

Recommended content:

- KPI cards: Country Count, Top Country Revenue Share, International Revenue, International Order Count.
- Choropleth map or country table.
- Country revenue/order volume bubble map or scatter.
- AOV by country.
- Country revenue share/Pareto bar.
- Filters: date range, country group, minimum orders.

### Tab 5: Data Quality / Warehouse Health

Business question: Can the numbers be trusted, and where should analysts be careful?

Recommended content:

- KPI cards: raw rows, processed fact rows, null customer rows, return rows, zero-price rows, outlier rows.
- Data lineage comparison: raw workbook vs processed fact export.
- Return logic comparison: invoice prefix vs negative quantity.
- Country mapping exception table.
- Product code exception table.

This tab is useful because the local processed export row count does not match the full raw dataset size cited in the documentation.

## 8. Recommended Charts

| Chart Title | Type | X-Axis | Y-Axis | Color Encoding | Source | Metric Formula | Why It Belongs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Monthly Revenue Trend | Line chart | `month` | Gross revenue | Revenue line in amber; optional net revenue in teal | `monthly_revenue.csv` or `fact_sales_enriched.csv` | `SUM(quantity * unit_price)` where `quantity > 0`, monthly | Required executive trend view; currently available. |
| Gross vs Net Revenue Over Time | Multi-line chart | Month | Revenue | Gross amber, net teal, returns rose | `fact_sales_enriched.csv` | Gross positive revenue, net all-line revenue, return value | Improves the Looker version by showing refund drag. |
| Revenue by Country | Horizontal bar | Revenue | Country | Blue/teal by revenue intensity | `country_revenue.csv` | Positive revenue by country | Required geographic view; currently available. |
| Country Revenue / Order Volume Map | Choropleth or scatter geo | Country | N/A | Revenue color; order count hover/size | `country_revenue.csv` plus country-name mapping | Positive revenue and distinct invoice count | Possible, but country normalization is needed for `EIRE`, `RSA`, `USA`, `Unspecified`, and region-like labels. |
| AOV by Country | Bar chart | Country | AOV | Green for high AOV, slate for normal | `fact_sales_enriched.csv` or `country_revenue.csv` | `country revenue / country positive invoices` | Reveals order efficiency beyond total volume. |
| Top Customers by LTV | Bar chart/table | Customer ID | LTV | Amber for revenue | `top_customers.csv` or fact aggregation | Positive revenue by customer | Required customer intelligence view; currently available. |
| Customer Order Frequency Distribution | Histogram | Distinct orders per customer | Customer count | Teal | `fact_sales_enriched.csv` | `COUNT(DISTINCT invoice_number)` by customer | Shows loyalty distribution, not just top accounts. |
| LTV vs Order Frequency | Scatter | Order count | LTV | Country or recency bucket | `fact_sales_enriched.csv` | LTV and order count by customer | Separates high-frequency low-value from strategic accounts. |
| Top Products by Net Revenue | Bar chart | Product | Net revenue | Amber positive, rose negative/return drag | `fact_sales_enriched.csv` | `SUM(quantity * unit_price)` by product | More accurate than top positive revenue alone. |
| Top Products by Gross Revenue | Horizontal bar | Gross revenue | Product | Amber | `top_products.csv` or fact aggregation | Positive revenue by product | Required product performance view. |
| Product Return Rate Audit | DataTable | Product/stock code | Return metrics columns | Conditional red/rose for high return rate | `fact_sales_enriched.csv` | Return line rate and returned-unit rate by product | Required return audit view. |
| Revenue vs Return Rate Scatter | Scatter/bubble | Gross revenue | Return rate % | Size = units sold; color = return risk | `fact_sales_enriched.csv` | Revenue by product vs return rate | Possible and strongly recommended; identifies high-value risky products. |
| Product Return-Risk Matrix | Quadrant scatter | Revenue percentile | Return rate percentile | Quadrant colors | `fact_sales_enriched.csv` | Revenue and return risk ranks | Better executive product risk view than a simple table. |
| Revenue Concentration / Pareto | Bar + cumulative line | Ranked customer/product/country | Revenue and cumulative share | Bar amber, cumulative teal | Fact aggregation | Ranked positive revenue and cumulative share | Shows dependency on top customers/products/countries. |
| Customer Cohort / Retention | Heatmap | Months since first order | Cohort month | Retention % color | `fact_sales_enriched.csv` | Customer active month relative to first month | Possible from fact data, but current SQL only provides cohort sizes, not full retention. |

Feasibility assessment:

| Candidate | Feasible Now? | Notes |
| --- | --- | --- |
| Monthly revenue trend | Yes | Already exported. |
| Revenue by country | Yes | Already exported. |
| Top customers by LTV | Yes | Already exported. |
| Customer order frequency distribution | Yes | Compute from enriched fact. |
| Top products by net revenue | Yes | Compute from enriched fact. |
| Product return rate audit | Yes | Use enriched fact; avoid relying only on top 50 product export. |
| Revenue vs return rate scatter | Yes | Compute product aggregation from enriched fact. |
| Country revenue/order volume map | Yes, with cleanup | Needs country name mapping for Plotly geo. |
| AOV by country | Yes | Compute from enriched fact or country export. |
| Revenue concentration / Pareto view | Yes | Compute from fact aggregations. |
| Product return-risk matrix | Yes | Compute from product revenue, units, return rate, and volume thresholds. |

## 9. Better Dashboard Ideas Beyond the Looker Version

- Customer value concentration: show what percentage of revenue comes from the top 10, top 50, and top 100 customers.
- Product return-risk quadrant: classify products into high revenue/high return risk, high revenue/low risk, low revenue/high risk, and low revenue/low risk.
- Revenue vs return rate scatter: expose products that look successful by revenue but create refund risk.
- Country-level order efficiency: compare country revenue, order count, AOV, and customer count.
- Revenue contribution by top 10 customers/products/countries: useful executive dependency metric.
- Guest checkout impact: quantify how much revenue and how many rows cannot be tied to a known customer ID.
- Data quality summary: show raw-to-processed row counts, null customer rate, zero-price rows, return rows, and country mapping exceptions.
- Recency and RFM segmentation: supported by `invoice_date`, `customer_id`, revenue, and frequency. The nested `customer-segmentation-rfm/` folder does not currently implement it, but the data supports it.
- Cohort retention heatmap: supported by transaction dates and customer IDs, but should be built carefully because guest/null customers are excluded.
- Operational-code filter: let users remove `Manual`, postage, discount, commission, damage, and ebay stock codes from product views.

## 10. Recommended Dashboard Style

Recommended professional dark theme:

| Use | Color |
| --- | --- |
| App background | `#050B14` near-black navy |
| Panel background | `#0F172A` slate |
| Secondary panel | `#111827` charcoal |
| Borders/grid | `#243244` muted slate |
| Primary text | `#F8FAFC` white/slate-50 |
| Secondary text | `#CBD5E1` slate-300 |
| Muted text | `#94A3B8` slate-400 |
| Neutral analytics | `#38BDF8` sky blue, `#2DD4BF` teal |
| Revenue highlights | `#F59E0B` amber |
| Return/risk | `#F43F5E` rose/red |
| Positive performance | `#22C55E` green |
| Warning/outlier | `#F97316` orange |

Style guidance:

- Use compact, high-contrast KPI cards with short labels and clear numeric formatting.
- Use slate panels with subtle borders, not heavy gradients.
- Use amber sparingly for revenue metrics so it remains meaningful.
- Use rose/red only for returns, refunds, and risk.
- Use teal/blue for neutral trend and categorical analytics.
- Use green for favorable deltas, high retention, or low-risk markers.
- Prefer dense dashboard layouts over marketing-style hero sections.

## 11. Files Likely Needed for Implementation

Do not modify these yet; this is the recommended Part 2 file plan.

| File | Create/Modify | Purpose |
| --- | --- | --- |
| `dashboard/app.py` | Create | Main Plotly Dash app, layout, callbacks, routing/tabs. |
| `dashboard/assets/style.css` | Create | Dark theme, KPI cards, responsive grid, DataTable styling. |
| `src/dashboard_data.py` | Create | Reusable data loading and metric aggregation functions from CSV or database. |
| `sql/dashboard_queries.sql` | Create | Optional consolidated SQL query layer for direct PostgreSQL mode. |
| `requirements.txt` or `pyproject.toml` | Create/modify if present | Add Dash, Plotly, pandas, SQLAlchemy, psycopg2 if not already managed. No dependency file is currently present. |
| `README.md` | Modify later | Add dashboard run instructions after implementation. |
| `docker-compose.yml` | Optional later | Could add a Dash service only if containerized deployment is desired. |
| `config/config.yaml` | Optional later | Could add dashboard source mode and paths; avoid embedding new secrets. |

Recommended implementation source choice:

- Short term: build Dash from `data/processed/fact_sales_enriched.csv` because it is local and avoids database availability issues.
- Production-style option: support PostgreSQL queries via config, using CSV fallback.
- Before finalizing metrics: confirm why processed fact rows are 133,465 versus the raw workbook's 1,067,371 rows.

## 12. Implementation Risks

- Database connection risk: local PostgreSQL must be running on `127.0.0.1:5433`; credentials are hardcoded in `config/config.yaml` and `src/export_for_bi.py`.
- Schema drift risk: `is_return` is referenced by ETL/reporting docs but missing from `sql/ddl/schema.sql`.
- Data lineage risk: processed fact export row count is much lower than raw workbook row count and README cleaned-record count.
- Dependency risk: no visible `requirements.txt` or `pyproject.toml`; Dash/Plotly dependencies are not currently declared.
- Map risk: Plotly country mapping will need normalization for `EIRE`, `RSA`, `USA`, `Unspecified`, `European Community`, `Channel Islands`, and `West Indies`.
- Performance risk: raw Excel has over 1M rows and should not be parsed on every Dash page load. Use processed CSV, parquet, cached aggregations, or database queries.
- Metric consistency risk: return rate can mean return-line rate, returned-unit rate, cancelled-invoice rate, or return-value rate. The dashboard should label the chosen definition clearly.
- Product semantics risk: non-product stock codes such as `M`, `DOT`, `D`, `CRUK`, damages, and ebay records can distort product rankings.
- Customer analytics risk: guest/null customers cannot be included in LTV, repeat purchase rate, recency, or cohorts.
- Currency risk: no currency column exists; dashboard should label values as assumed GBP or leave currency explicit in notes.
- Outlier risk: extreme unit prices and quantities can distort charts unless tooltips, filters, or robust axes are used.

## Final Recommendations

Recommended dashboard tabs:

1. Executive Overview
2. Customer Intelligence
3. Product & Return Audit
4. Geographic Performance
5. Data Quality / Warehouse Health

Top 5 charts to build first:

1. Monthly Revenue Trend
2. Revenue by Country
3. Top Customers by LTV
4. Revenue vs Return Rate Product Scatter
5. Product Return Rate Audit Table

Missing information before Part 2:

- Confirm whether the dashboard should use local processed CSVs, live PostgreSQL, or both with fallback.
- Confirm why `fact_sales_enriched.csv` has 133,465 rows versus 1,067,371 raw workbook rows.
- Decide whether revenue should default to gross positive revenue or net revenue after returns.
- Decide whether return rate should be line-based, unit-based, value-based, or invoice-cancellation-based.
- Decide whether operational stock codes such as postage, manual, discount, commission, damages, and ebay rows should be excluded from product analytics by default.
