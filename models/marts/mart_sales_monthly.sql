select
    date_trunc('month', invoice_date)::date as month,
    sum(case when is_positive_sale then line_revenue else 0 end) as revenue,
    count(distinct invoice_number) as invoice_count,
    sum(case when is_positive_sale then quantity else 0 end) as quantity_sold
from {{ ref('stg_sales') }}
group by 1
order by 1
