SELECT
    ROUND(
        100.0 * COUNT(CASE WHEN order_count > 1 THEN 1 END) / COUNT(*), 2
    ) AS repeat_purchase_rate_pct
FROM (
    SELECT customer_id, COUNT(DISTINCT invoice_number) AS order_count
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
) sub;