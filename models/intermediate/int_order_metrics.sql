select
    invoice_number,
    min(invoice_date) as first_invoice_date,
    max(invoice_date) as last_invoice_date,
    count(*) as line_count,
    sum(case when is_positive_sale then line_revenue else 0 end) as order_revenue,
    sum(case when is_positive_sale then quantity else 0 end) as quantity_sold,
    bool_or(is_return) as includes_return,
    count(distinct customer_id) filter (where customer_id is not null) as known_customer_count
from {{ ref('stg_sales') }}
group by invoice_number
