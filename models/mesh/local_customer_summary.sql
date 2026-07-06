select
    metrics.customer_id,
    names.first_name,
    names.last_name,
    metrics.number_of_orders,
    metrics.lifetime_value,
    metrics.value_tier
from {{ ref('jaffle_customer_metrics') }} as metrics
left join {{ ref('jaffle_customer_names') }} as names
    on metrics.customer_id = names.customer_id
