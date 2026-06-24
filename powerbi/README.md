# Power BI / Power Query Documentation

This folder documents the Power BI-ready semantic layer and export workflow for the Customer Intelligence Data Warehouse.

Current status: this folder documents the Power BI-ready semantic layer and export workflow. A `.pbix` file is not included yet.

## Purpose

The dbt project produces validated marts for executive KPI reporting, customer lifetime value, repeat purchase behavior, country revenue, and monthly sales trends. The Power BI proof layer explains how those marts can be exported to CSV and imported into Power BI Desktop without claiming that a Power BI workbook has already been built.

## Source dbt Marts

- `mart_executive_kpis`
- `mart_customer_lifetime_value`
- `mart_repeat_purchase_metrics`
- `mart_country_revenue`
- `mart_sales_monthly`

## Planned Dashboard Pages

- Executive Overview
- Customer LTV
- Repeat Purchase & Retention
- Country Revenue
- Monthly Sales Trends

## Export dbt Marts

Start PostgreSQL, run the ETL if the warehouse is empty, then build dbt models:

```bash
docker compose up -d
python src/etl/pipeline.py
export DBT_POSTGRES_PASSWORD='your-local-postgres-password'
dbt run
dbt test
python src/export_dbt_marts_for_powerbi.py
```

The script writes CSV files to `powerbi/exports/`.

## Import CSVs Into Power BI Desktop

1. Open Power BI Desktop.
2. Select **Get Data > Text/CSV**.
3. Import each CSV from `powerbi/exports/`.
4. Use Power Query to set data types, rename columns, and confirm date/numeric fields.
5. Create or import a Date table for monthly trend analysis.
6. Build report pages using the marts and DAX measures documented in this folder.

## Screenshots To Add Later

Add screenshots to `powerbi/screenshots/` after a real report is built. Recommended screenshots:

- Executive Overview page
- Customer LTV page
- Repeat Purchase & Retention page
- Country Revenue page
- Monthly Sales Trends page
- Model view showing relationships and Date table

No `.pbix`, `.pbit`, or `.pq` files are included in this phase.
