{{ config(alias='health_metric_daily_fact') }}

with base as (
  select
    account_ref,
    metric_date,
    metric_type,
    metric_name,
    metric_value_num,
    metric_value_text,
    metric_unit,
    quality_flag,
    occurred_at,
    ingested_at
  from {{ ref('int_canonical__health_metric_daily') }}
),
aggregated as (
  select
    account_ref,
    metric_date,
    metric_name,
    max(metric_type) as metric_type,
    round(avg(metric_value_num) filter (where metric_value_num is not null)::numeric, 4)::numeric(18,4) as metric_value_num,
    max(metric_value_text) filter (
      where metric_value_text is not null
        and metric_value_text <> ''
    ) as metric_value_text,
    max(metric_unit) filter (
      where metric_unit is not null
        and metric_unit <> ''
    ) as metric_unit,
    case
      when count(*) filter (where quality_flag = 'ok') > 0 then 'ok'
      when count(*) filter (where quality_flag = 'no_data') = count(*) then 'no_data'
      when count(*) filter (where quality_flag = 'not_supported') = count(*) then 'not_supported'
      else 'parse_failed'
    end as quality_flag,
    count(*)::int as source_count,
    min(occurred_at) as first_occurred_at,
    max(occurred_at) as last_occurred_at,
    max(ingested_at) as latest_ingested_at
  from base
  group by 1, 2, 3
)
select
  md5(concat_ws('::', coalesce(account_ref, ''), coalesce(metric_date::text, ''), coalesce(metric_name, ''))) as domain_metric_row_id,
  account_ref,
  metric_date,
  metric_type,
  metric_name,
  metric_value_num,
  metric_value_text,
  metric_unit,
  quality_flag,
  (quality_flag = 'ok' and metric_value_num is not null) as is_valid,
  source_count,
  first_occurred_at,
  last_occurred_at,
  latest_ingested_at
from aggregated
