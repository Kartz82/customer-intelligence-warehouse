select
    sale_id::integer as sale_id,
    invoice_number::varchar as invoice_number,
    stock_code::varchar as stock_code,
    customer_id::bigint as customer_id,
    country_id::integer as country_id,
    quantity::integer as quantity,
    invoice_date::timestamp as invoice_date,
    unit_price::numeric(10, 2) as unit_price,
    coalesce(is_return::boolean, quantity < 0, false) as is_return,
    (quantity::numeric * unit_price::numeric) as line_revenue,
    (quantity > 0 and unit_price >= 0) as is_positive_sale
from {{ source('warehouse', 'fact_sales') }}
