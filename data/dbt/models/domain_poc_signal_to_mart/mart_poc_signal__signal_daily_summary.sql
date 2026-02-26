{{ config(schema='mart_poc_signal', alias='signal_daily_summary') }}

select
  cast(date_trunc('day', occurred_at at time zone 'UTC') as date) as stat_date,
  count(*) as event_count,
  count(*) filter (where source_type = 'manual') as manual_count,
  count(*) filter (where source_type = 'connector') as connector_count,
  round(avg(value_num), 2) as avg_value,
  min(value_num) as min_value,
  max(value_num) as max_value
from {{ ref('fct_domain_poc_signal__signal_event') }}
where is_valid = true
group by 1
