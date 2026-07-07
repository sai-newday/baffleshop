with from_public_customers as (
    select
        customer_id,
        first_name,
        last_name,
        number_of_orders,
        lifetime_value,
        cast(null as varchar) as value_tier,
        cast(null as varchar) as order_segment,
        'public_customers_from_jaffle' as record_source
    from {{ ref('public_customers_from_jaffle') }}
),
from_customer_names as (
    select
        customer_id,
        first_name,
        last_name,
        cast(null as integer) as number_of_orders,
        cast(null as double) as lifetime_value,
        cast(null as varchar) as value_tier,
        cast(null as varchar) as order_segment,
        'jaffle_customer_names' as record_source
    from {{ ref('jaffle_customer_names') }}
),
from_customer_metrics as (
    select
        customer_id,
        cast(null as varchar) as first_name,
        cast(null as varchar) as last_name,
        number_of_orders,
        lifetime_value,
        value_tier,
        cast(null as varchar) as order_segment,
        'jaffle_customer_metrics' as record_source
    from {{ ref('jaffle_customer_metrics') }}
),
from_customer_segments as (
    select
        customer_id,
        first_name,
        last_name,
        number_of_orders,
        lifetime_value,
        value_tier,
        order_segment,
        'local_customer_segments' as record_source
    from {{ ref('local_customer_segments') }}
)

select * from from_public_customers
union all
select * from from_customer_names
union all
select * from from_customer_metrics
union all
select * from from_customer_segments
