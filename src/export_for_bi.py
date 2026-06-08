import os
import pandas as pd
from sqlalchemy import create_engine

# Verified Docker container link over port 5433
engine = create_engine("postgresql://analytics_engineer:Password123!@127.0.0.1:5433/customer_intelligence_db")

os.makedirs("data/processed", exist_ok=True)

print("📤 Starting pre-aggregated warehouse export for Looker Studio...")

# 1. Export enriched fact sales, dynamically setting return status based on quantity sign
fact_sales = pd.read_sql("""
    SELECT 
        f.sale_id,
        f.invoice_number,
        f.stock_code,
        f.customer_id,
        f.quantity,
        f.invoice_date,
        f.unit_price,
        CASE WHEN f.quantity < 0 THEN true ELSE false END AS is_return,
        ROUND((f.quantity * f.unit_price)::numeric, 2) AS line_revenue,
        dc.country_name,
        dp.description AS product_name
    FROM fact_sales f
    LEFT JOIN dim_country dc ON f.country_id = dc.country_id
    LEFT JOIN dim_product dp ON f.stock_code = dp.stock_code
""", engine)

fact_sales.to_csv("data/processed/fact_sales_enriched.csv", index=False)
print(f"✅ Exported fact_sales_enriched ({len(fact_sales):,} rows)")

# 2. Monthly Velocity (Filtering out returns via quantity logic)
monthly_revenue = pd.read_sql("""
    SELECT
        DATE_TRUNC('month', invoice_date)::date AS month,
        ROUND(SUM(quantity * unit_price)::numeric, 2) AS revenue
    FROM fact_sales
    WHERE quantity > 0
    GROUP BY 1 ORDER BY 1
""", engine)
monthly_revenue.to_csv("data/processed/monthly_revenue.csv", index=False)
print(f"✅ Exported monthly_revenue ({len(monthly_revenue):,} rows)")

# 3. Top Customers
top_customers = pd.read_sql("""
    SELECT
        f.customer_id,
        ROUND(SUM(f.quantity * f.unit_price)::numeric, 2) AS lifetime_value,
        COUNT(DISTINCT f.invoice_number) AS total_orders
    FROM fact_sales f
    WHERE f.quantity > 0 AND f.customer_id IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC
    LIMIT 50
""", engine)
top_customers.to_csv("data/processed/top_customers.csv", index=False)
print(f"✅ Exported top_customers ({len(top_customers):,} rows)")

# 4. Country Revenue Breakdown
country_revenue = pd.read_sql("""
    SELECT
        dc.country_name,
        ROUND(SUM(f.quantity * f.unit_price)::numeric, 2) AS revenue,
        COUNT(DISTINCT f.invoice_number) AS order_count
    FROM fact_sales f
    LEFT JOIN dim_country dc ON f.country_id = dc.country_id
    WHERE f.quantity > 0
    GROUP BY 1 ORDER BY 2 DESC
""", engine)
country_revenue.to_csv("data/processed/country_revenue.csv", index=False)
print(f"✅ Exported country_revenue ({len(country_revenue):,} rows)")

# 5. Top Products with return risk metric included
top_products = pd.read_sql("""
    SELECT
        dp.description AS product_name,
        f.stock_code,
        ROUND(SUM(CASE WHEN f.quantity > 0 THEN f.quantity * f.unit_price ELSE 0 END)::numeric, 2) AS revenue,
        SUM(CASE WHEN f.quantity > 0 THEN f.quantity ELSE 0 END) AS units_sold,
        ROUND(AVG(f.unit_price)::numeric, 2) AS avg_price,
        ROUND(
            (COUNT(CASE WHEN f.quantity < 0 THEN 1 END)::numeric / NULLIF(COUNT(*), 0)) * 100, 2
        ) AS return_rate_percentage
    FROM fact_sales f
    LEFT JOIN dim_product dp ON f.stock_code = dp.stock_code
    GROUP BY 1, 2 ORDER BY 3 DESC
    LIMIT 50
""", engine)
top_products.to_csv("data/processed/top_products.csv", index=False)
print(f"✅ Exported top_products ({len(top_products):,} rows)")

print("\n🎉 All 5 localized CSVs cleanly generated in data/processed/!")