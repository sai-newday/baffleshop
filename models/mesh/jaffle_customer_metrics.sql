select
    customer_id,
    number_of_orders
from {{ source('jaffleshop', 'public_customers') }}
