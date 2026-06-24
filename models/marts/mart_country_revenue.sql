select
    country_name,
    total_revenue,
    invoice_count,
    customer_count,
    aov
from {{ ref('int_country_metrics') }}
order by total_revenue desc
