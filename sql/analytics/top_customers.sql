SELECT
    c.customer_id,
    ROUND(SUM(f.quantity * f.unit_price)::numeric, 2) AS lifetime_value,
    COUNT(DISTINCT f.invoice_number) AS total_orders
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
WHERE f.quantity > 0
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;