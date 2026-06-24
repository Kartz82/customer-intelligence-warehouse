select
    customer_id::bigint as customer_id
from {{ source('warehouse', 'dim_customer') }}
