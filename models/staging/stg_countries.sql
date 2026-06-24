select
    country_id::integer as country_id,
    country_name::varchar as country_name
from {{ source('warehouse', 'dim_country') }}
