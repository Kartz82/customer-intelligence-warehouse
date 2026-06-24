select
    customer_id,
    total_revenue,
    order_count,
    first_order_date,
    last_order_date,
    customer_lifetime_value
from {{ ref('int_customer_lifetime_value') }}
