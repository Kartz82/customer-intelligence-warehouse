select
    customer_id,
    first_order_date,
    last_order_date,
    order_count,
    total_revenue,
    total_revenue as customer_lifetime_value
from {{ ref('int_customer_orders') }}
