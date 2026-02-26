select
  stat_date
from {{ ref('mart_poc_signal__signal_daily_summary') }}
where event_count <> manual_count + connector_count
