select
  account_ref,
  stat_date,
  activity_type,
  count(*) as dup_cnt
from {{ ref('mart__health_activity_topic_daily') }}
group by 1, 2, 3
having count(*) > 1
