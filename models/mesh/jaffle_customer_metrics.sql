select
    customer_id,
    number_of_orders,
    lifetime_value as lifetime_value,
    case
        when lifetime_value >= 150 then 'high_value'
        when lifetime_value >= 75 then 'mid_value'
        else 'standard'
    end as value_tier
from {{ source('jaffleshop', 'public_customers') }}
