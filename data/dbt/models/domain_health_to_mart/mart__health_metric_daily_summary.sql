{{ config(alias='health_metric_daily_summary') }}

select
  account_ref,
  metric_date as stat_date,
  metric_name,
  sum(source_count)::bigint as sample_count,
  round(avg(metric_value_num) filter (where metric_value_num is not null)::numeric, 4)::numeric(18,4) as value_avg,
  min(metric_value_num)::numeric(18,4) as value_min,
  max(metric_value_num)::numeric(18,4) as value_max,
  max(last_occurred_at) as latest_occurred_at,
  max(latest_ingested_at) as latest_ingested_at,
  sum(case when quality_flag = 'ok' then source_count else 0 end)::bigint as quality_ok_count,
  sum(case when quality_flag <> 'ok' then source_count else 0 end)::bigint as quality_issue_count
from {{ ref('fct_domain_health__health_metric_daily_fact') }}
group by 1, 2, 3
