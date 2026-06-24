select
    stock_code::varchar as stock_code,
    description::varchar as product_name,
    unit_price_reference::numeric(10, 2) as unit_price_reference
from {{ source('warehouse', 'dim_product') }}
