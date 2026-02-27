{{ config(alias='health_daily_overview') }}

with metric_summary as (
  select
    account_ref,
    stat_date,
    metric_name,
    value_avg,
    value_min,
    value_max,
    quality_ok_count,
    quality_issue_count
  from {{ ref('mart__health_metric_daily_summary') }}
)
select
  account_ref,
  stat_date,
  max(value_avg) filter (where metric_name = 'sleep_duration_min')::numeric(18,4) as sleep_duration_min,
  max(value_avg) filter (where metric_name = 'resting_hr_bpm')::numeric(18,4) as resting_hr_bpm,
  max(value_avg) filter (where metric_name = 'stress_level_avg')::numeric(18,4) as stress_level_avg,
  max(value_avg) filter (where metric_name = 'body_battery_avg')::numeric(18,4) as body_battery_avg,
  max(coalesce(value_max, value_avg, value_min)) filter (where metric_name = 'steps_count')::numeric(18,4) as steps_count,
  max(coalesce(value_max, value_avg, value_min)) filter (where metric_name = 'active_kcal')::numeric(18,4) as active_kcal,
  count(*) filter (
    where quality_ok_count > 0
      and coalesce(value_avg, value_min, value_max) is not null
  )::int as coverage_metric_count,
  coalesce(sum(quality_issue_count), 0)::int as quality_issue_count,
  now() as updated_at
from metric_summary
group by 1, 2
