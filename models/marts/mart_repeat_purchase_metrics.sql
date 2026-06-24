select
    count(*) filter (where is_repeat_customer) as repeat_customers,
    count(*) as total_customers,
    count(*) filter (where is_repeat_customer)::numeric / nullif(count(*), 0) as repeat_purchase_rate
from {{ ref('int_customer_orders') }}
