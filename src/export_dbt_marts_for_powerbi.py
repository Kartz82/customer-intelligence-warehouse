from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "powerbi" / "exports"

MARTS = [
    "mart_executive_kpis",
    "mart_customer_lifetime_value",
    "mart_repeat_purchase_metrics",
    "mart_country_revenue",
    "mart_sales_monthly",
]


def build_database_url() -> str:
    user = os.getenv("DBT_POSTGRES_USER", "analytics_engineer")
    password = os.getenv("DBT_POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("DBT_POSTGRES_HOST", "localhost")
    port = os.getenv("DBT_POSTGRES_PORT", "5433")
    database = os.getenv("DBT_POSTGRES_DB", "customer_intelligence_db")

    safe_user = quote_plus(user)
    auth = safe_user
    if password:
        auth = f"{safe_user}:{quote_plus(password)}"

    return f"postgresql+psycopg2://{auth}@{host}:{port}/{database}"


def export_mart(engine, schema: str, mart_name: str) -> bool:
    inspector = inspect(engine)
    if not inspector.has_table(mart_name, schema=schema):
        print(f"SKIP: {schema}.{mart_name} was not found. Run dbt first.")
        return False

    query = text(f'SELECT * FROM "{schema}"."{mart_name}"')
    df = pd.read_sql(query, engine)
    output_path = EXPORT_DIR / f"{mart_name}.csv"
    df.to_csv(output_path, index=False)
    print(f"OK: exported {schema}.{mart_name} -> {output_path.relative_to(PROJECT_ROOT)} ({len(df):,} rows)")
    return True


def main() -> int:
    schema = os.getenv("DBT_MART_SCHEMA", "analytics_marts")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting Power BI CSV export from dbt marts")
    print(f"Source schema: {schema}")
    print(f"Export folder: {EXPORT_DIR.relative_to(PROJECT_ROOT)}")

    try:
        engine = create_engine(build_database_url())
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print(f"ERROR: could not connect to PostgreSQL: {exc}")
        return 1

    exported = 0
    for mart in MARTS:
        try:
            exported += int(export_mart(engine, schema, mart))
        except SQLAlchemyError as exc:
            print(f"ERROR: failed to export {schema}.{mart}: {exc}")

    missing = len(MARTS) - exported
    print(f"Finished Power BI export: {exported} exported, {missing} missing or failed")
    return 0 if exported == len(MARTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
