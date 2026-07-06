select
    customer_id,
    first_name,
    last_name,
    number_of_orders,
    lifetime_value
from {{ source('jaffleshop', 'public_customers') }}

