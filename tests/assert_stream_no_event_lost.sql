-- Governance invariant: every landed event is accounted for — either promoted
-- to the stream fact or explicitly quarantined. Nothing is dropped silently.
-- This test FAILS (returns rows) if landed <> promoted + quarantined.
with landed as (
    select count(*) as n from {{ source('stream', 'raw_orders_events') }}
),
promoted as (
    select count(*) as n from {{ source('stream', 'fact_orders_stream') }}
),
quarantined as (
    select count(*) as n from {{ source('stream', 'orders_quarantine') }}
)
select
    landed.n      as n_landed,
    promoted.n    as n_promoted,
    quarantined.n as n_quarantined
from landed, promoted, quarantined
where landed.n <> promoted.n + quarantined.n
