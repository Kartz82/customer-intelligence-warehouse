SELECT
    DATE_TRUNC('month', first_order) AS cohort_month,
    COUNT(DISTINCT customer_id) AS cohort_size
FROM (
    SELECT customer_id, MIN(invoice_date) AS first_order
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
) sub
GROUP BY 1
ORDER BY 1;