select
    s.sale_id,
    s.invoice_number,
    s.stock_code,
    s.customer_id,
    s.country_id,
    s.quantity,
    s.invoice_date,
    date_trunc('month', s.invoice_date)::date as sales_month,
    s.unit_price,
    s.is_return,
    s.line_revenue,
    s.is_positive_sale,
    p.product_name,
    p.unit_price_reference,
    c.country_name
from {{ ref('stg_sales') }} as s
left join {{ ref('stg_products') }} as p
    on s.stock_code = p.stock_code
left join {{ ref('stg_countries') }} as c
    on s.country_id = c.country_id
left join {{ ref('stg_customers') }} as cu
    on s.customer_id = cu.customer_id
