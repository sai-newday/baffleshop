select
    customer_id,
    first_name,
    last_name as last_name
from {{ source('jaffleshop', 'public_customers') }}
