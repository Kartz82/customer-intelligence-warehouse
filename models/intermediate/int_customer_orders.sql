select
    customer_id,
    min(invoice_date) as first_order_date,
    max(invoice_date) as last_order_date,
    count(distinct invoice_number) as order_count,
    sum(case when is_positive_sale then line_revenue else 0 end) as total_revenue,
    (count(distinct invoice_number) > 1) as is_repeat_customer
from {{ ref('stg_sales') }}
where customer_id is not null
group by customer_id
