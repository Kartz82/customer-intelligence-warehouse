with customer_first_purchase as (
    select
        customer_id,
        date_trunc('month', min(invoice_date))::date as cohort_month
    from {{ ref('stg_sales') }}
    where customer_id is not null
      and is_positive_sale
    group by customer_id
),

customer_monthly_activity as (
    select
        customer_id,
        date_trunc('month', invoice_date)::date as activity_month,
        count(distinct invoice_number) as monthly_order_count,
        sum(line_revenue) as monthly_revenue
    from {{ ref('stg_sales') }}
    where customer_id is not null
      and is_positive_sale
    group by
        customer_id,
        date_trunc('month', invoice_date)::date
),

customer_order_summary as (
    select
        customer_id,
        order_count,
        total_revenue
    from {{ ref('int_customer_orders') }}
)

select
    activity.customer_id,
    first_purchase.cohort_month,
    activity.activity_month,
    (
        extract(year from age(activity.activity_month, first_purchase.cohort_month))::integer * 12
        + extract(month from age(activity.activity_month, first_purchase.cohort_month))::integer
    ) as months_since_first_purchase,
    activity.monthly_order_count,
    activity.monthly_revenue,
    customer_orders.order_count as lifetime_order_count,
    customer_orders.total_revenue as lifetime_revenue,
    (customer_orders.order_count > 1) as is_repeat_customer
from customer_monthly_activity as activity
inner join customer_first_purchase as first_purchase
    on activity.customer_id = first_purchase.customer_id
inner join customer_order_summary as customer_orders
    on activity.customer_id = customer_orders.customer_id
