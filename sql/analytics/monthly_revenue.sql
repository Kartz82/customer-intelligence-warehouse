SELECT
    DATE_TRUNC('month', invoice_date) AS month,
    ROUND(SUM(quantity * unit_price)::numeric, 2) AS revenue
FROM fact_sales
WHERE quantity > 0
GROUP BY 1
ORDER BY 1;