SELECT
    ROUND(AVG(order_total)::numeric, 2) AS avg_order_value
FROM (
    SELECT invoice_number, SUM(quantity * unit_price) AS order_total
    FROM fact_sales
    WHERE quantity > 0
    GROUP BY invoice_number
) sub;