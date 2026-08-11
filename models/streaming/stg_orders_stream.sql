-- Typed, governed view over the promoted stream fact.
-- Revenue rule matches the semantic catalog: cancelled orders contribute 0.
select
    order_event_id::bigint                       as order_event_id,
    event_id::bigint                             as event_id,
    order_id::varchar                            as order_id,
    customer_id::bigint                          as customer_id,
    country::varchar                             as country,
    stock_code::varchar                          as stock_code,
    quantity::integer                            as quantity,
    unit_price::numeric(12, 2)                   as unit_price,
    order_status::varchar                        as order_status,
    order_ts::timestamptz                        as order_ts,
    line_revenue::numeric(14, 2)                 as line_revenue,
    (order_status in ('completed', 'shipped'))   as counts_as_revenue,
    promoted_at::timestamptz                     as promoted_at
from {{ source('stream', 'fact_orders_stream') }}
