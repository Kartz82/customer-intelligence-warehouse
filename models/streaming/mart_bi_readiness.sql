-- =====================================================================
-- BI-Readiness score for the streaming pipeline.
-- One row: the trust scorecard a stakeholder / AI agent can read before
-- relying on the streamed data. Scores are 0..100.
-- =====================================================================
with landed as (
    select count(*) as n_landed,
           max(ingested_at) as last_ingested
    from {{ source('stream', 'raw_orders_events') }}
),
promoted as (
    select count(*) as n_promoted,
           count(*) filter (where counts_as_revenue) as n_revenue_rows,
           coalesce(sum(line_revenue), 0) as stream_revenue
    from {{ ref('stg_orders_stream') }}
),
quarantined as (
    select count(*) as n_quarantined
    from {{ source('stream', 'orders_quarantine') }}
),
audits as (
    select
        count(*) as n_decisions,
        count(*) filter (where method = 'llm') as n_llm,
        count(*) filter (where method = 'rule') as n_rule
    from {{ source('stream', 'orders_clean_audit') }}
),
calc as (
    select
        l.n_landed,
        p.n_promoted,
        q.n_quarantined,
        p.stream_revenue,
        a.n_decisions,
        a.n_llm,
        -- no event is ever silently dropped
        (l.n_landed = p.n_promoted + q.n_quarantined) as reconciles,
        -- share of events trusted enough to promote
        round(100.0 * p.n_promoted / nullif(l.n_landed, 0), 1) as accept_score,
        -- how often the deterministic rules were enough (cheaper = better)
        round(100.0 * a.n_rule / nullif(a.n_decisions, 0), 1) as rule_coverage_score,
        -- freshness: 100 if seen in last 5 min, decays after
        greatest(0, round(100 - extract(epoch from (now() - l.last_ingested)) / 3.0, 1)) as freshness_score
    from landed l
    cross join promoted p
    cross join quarantined q
    cross join audits a
)
select
    n_landed,
    n_promoted,
    n_quarantined,
    stream_revenue,
    n_llm as llm_interventions,
    reconciles,
    accept_score,
    rule_coverage_score,
    freshness_score,
    -- overall readiness: reconciliation is a hard gate (0 if broken)
    case when reconciles
         then round((accept_score + rule_coverage_score + freshness_score) / 3.0, 1)
         else 0 end as bi_readiness_score
from calc
