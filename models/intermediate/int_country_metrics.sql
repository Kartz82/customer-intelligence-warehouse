select
    c.country_id,
    c.country_name,
    sum(case when s.is_positive_sale then s.line_revenue else 0 end) as total_revenue,
    count(distinct s.invoice_number) as invoice_count,
    count(distinct s.customer_id) filter (where s.customer_id is not null) as customer_count,
    sum(case when s.is_positive_sale then s.quantity else 0 end) as quantity_sold,
    sum(case when s.is_positive_sale then s.line_revenue else 0 end)
        / nullif(count(distinct s.invoice_number), 0) as aov
from {{ ref('stg_sales') }} as s
left join {{ ref('stg_countries') }} as c
    on s.country_id = c.country_id
group by c.country_id, c.country_name
