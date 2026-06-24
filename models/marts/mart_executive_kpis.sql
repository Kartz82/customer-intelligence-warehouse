with orders as (
    select
        sum(order_revenue) as total_revenue,
        count(*) as total_invoices,
        sum(quantity_sold) as total_quantity_sold
    from {{ ref('int_order_metrics') }}
),
customers as (
    select
        count(*) as total_customers,
        count(*) filter (where is_repeat_customer) as repeat_customers
    from {{ ref('int_customer_orders') }}
)
select
    o.total_revenue,
    o.total_invoices,
    c.total_customers,
    o.total_revenue / nullif(o.total_invoices, 0) as aov,
    c.repeat_customers::numeric / nullif(c.total_customers, 0) as repeat_purchase_rate,
    o.total_quantity_sold
from orders as o
cross join customers as c
