# Power BI CSV Exports

Run the export script from the project root:

```bash
export DBT_POSTGRES_PASSWORD='your-local-postgres-password'
python src/export_dbt_marts_for_powerbi.py
```

Generated CSV files are written here for local Power BI Desktop import. CSV files may be large and are ignored by the repository-level `*.csv` rule.

`customer_intelligence_powerbi.xlsx` combines the mart CSV exports into a single workbook for Power BI Service browser import.
