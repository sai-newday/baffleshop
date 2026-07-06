select
    customer_id,
    first_name,
    last_name,
    number_of_orders,
    lifetime_value,
    value_tier,
    case
        when number_of_orders >= 3 then 'repeat'
        else 'new'
    end as order_segment
from {{ ref('local_customer_summary') }}
