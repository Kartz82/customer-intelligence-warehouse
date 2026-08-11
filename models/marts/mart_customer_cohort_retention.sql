with cohort_activity as (
    select *
    from {{ ref('int_customer_cohort_activity') }}
),

cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size,
        count(distinct customer_id) filter (where is_repeat_customer) as repeat_customers
    from cohort_activity
    where months_since_first_purchase = 0
    group by cohort_month
),

monthly_retention as (
    select
        cohort_month,
        activity_month,
        months_since_first_purchase,
        count(distinct customer_id) as retained_customers,
        sum(monthly_order_count) as cohort_orders,
        sum(monthly_revenue) as cohort_revenue
    from cohort_activity
    group by
        cohort_month,
        activity_month,
        months_since_first_purchase
)

select
    retention.cohort_month,
    retention.activity_month,
    retention.months_since_first_purchase,
    sizes.cohort_size,
    retention.retained_customers,
    retention.retained_customers::numeric / nullif(sizes.cohort_size, 0) as retention_rate,
    sizes.repeat_customers,
    sizes.repeat_customers::numeric / nullif(sizes.cohort_size, 0) as repeat_purchase_rate,
    retention.cohort_orders,
    retention.cohort_revenue,
    sum(retention.cohort_revenue) over (
        partition by retention.cohort_month
        order by retention.months_since_first_purchase
        rows between unbounded preceding and current row
    ) as cumulative_cohort_revenue,
    sum(retention.cohort_revenue) over (
        partition by retention.cohort_month
        order by retention.months_since_first_purchase
        rows between unbounded preceding and current row
    ) / nullif(sizes.cohort_size, 0) as cumulative_cohort_ltv
from monthly_retention as retention
inner join cohort_sizes as sizes
    on retention.cohort_month = sizes.cohort_month
