select
  account_ref,
  stat_date,
  metric_name,
  count(*) as dup_cnt
from {{ ref('mart__health_metric_daily_summary') }}
group by 1, 2, 3
having count(*) > 1
