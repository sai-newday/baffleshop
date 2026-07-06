-- Test model for blast radius analysis demo
-- This model demonstrates the impact analysis workflow

{{ config(
    materialized='table'
) }}

SELECT
  1 as test_id,
  'test_value' as test_column,
  CURRENT_TIMESTAMP as created_at,
  'demo_field' as demo_field
WHERE 1=1
