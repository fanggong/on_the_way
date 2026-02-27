{{ config(alias='health_metric_daily') }}

with recursive base as (
  select
    health_event_id,
    raw_id,
    account_ref,
    metric_date,
    metric_type,
    occurred_at,
    ingested_at,
    data_json
  from {{ ref('int_canonical__health_event') }}
),
special_metrics as (
  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'sleep_duration_min'::text as metric_name,
    (
      coalesce(
        case when nullif(b.data_json ->> 'sleepTimeSeconds', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'sleepTimeSeconds')::numeric(18,4) end,
        case when nullif(b.data_json ->> 'sleepTimeInSeconds', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'sleepTimeInSeconds')::numeric(18,4) end,
        case when nullif(b.data_json #>> '{dailySleepDTO,sleepTimeSeconds}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{dailySleepDTO,sleepTimeSeconds}')::numeric(18,4) end,
        case when nullif(b.data_json #>> '{dailySleepDTO,sleepTimeInSeconds}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{dailySleepDTO,sleepTimeInSeconds}')::numeric(18,4) end,
        case when nullif(b.data_json #>> '{sleepScores,sleepDurationSeconds}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{sleepScores,sleepDurationSeconds}')::numeric(18,4) end
      ) / 60.0
    )::numeric(18,4) as metric_value_num,
    null::text as metric_value_text,
    'minutes'::text as metric_unit,
    '$.sleep_duration'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b

  union all

  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'resting_hr_bpm'::text as metric_name,
    coalesce(
      case when nullif(b.data_json ->> 'restingHeartRate', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'restingHeartRate')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{allMetrics,metricsMap,RESTING_HEART_RATE,inMetrics,0,value}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{allMetrics,metricsMap,RESTING_HEART_RATE,inMetrics,0,value}')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{allMetrics,metricsMap,RESTING_HEART_RATE,currentDayValue}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{allMetrics,metricsMap,RESTING_HEART_RATE,currentDayValue}')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{groupedMetrics,restingHeartRate}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{groupedMetrics,restingHeartRate}')::numeric(18,4) end
    ) as metric_value_num,
    null::text as metric_value_text,
    'bpm'::text as metric_unit,
    '$.resting_heart_rate'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b

  union all

  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'stress_level_avg'::text as metric_name,
    coalesce(
      case when nullif(b.data_json ->> 'avgStressLevel', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'avgStressLevel')::numeric(18,4) end,
      case when nullif(b.data_json ->> 'overallStressLevel', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'overallStressLevel')::numeric(18,4) end,
      case when nullif(b.data_json ->> 'stressAvg', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'stressAvg')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{stressScores,overall}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{stressScores,overall}')::numeric(18,4) end
    ) as metric_value_num,
    null::text as metric_value_text,
    'score'::text as metric_unit,
    '$.stress_level'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b

  union all

  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'body_battery_avg'::text as metric_name,
    coalesce(
      case when nullif(b.data_json ->> 'bodyBatteryAverage', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'bodyBatteryAverage')::numeric(18,4) end,
      case when nullif(b.data_json ->> 'bodyBatteryValue', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'bodyBatteryValue')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{bodyBatteryStats,average}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{bodyBatteryStats,average}')::numeric(18,4) end
    ) as metric_value_num,
    null::text as metric_value_text,
    'score'::text as metric_unit,
    '$.body_battery'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b

  union all

  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'steps_count'::text as metric_name,
    coalesce(
      case when nullif(b.data_json ->> 'totalSteps', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'totalSteps')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{summary,steps}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{summary,steps}')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{allMetrics,metricsMap,steps,currentDayValue}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{allMetrics,metricsMap,steps,currentDayValue}')::numeric(18,4) end
    ) as metric_value_num,
    null::text as metric_value_text,
    'count'::text as metric_unit,
    '$.steps'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b

  union all

  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'active_kcal'::text as metric_name,
    coalesce(
      case when nullif(b.data_json ->> 'activeKilocalories', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'activeKilocalories')::numeric(18,4) end,
      case when nullif(b.data_json ->> 'activeKiloCalories', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json ->> 'activeKiloCalories')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{summary,activeKilocalories}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{summary,activeKilocalories}')::numeric(18,4) end,
      case when nullif(b.data_json #>> '{allMetrics,metricsMap,activeKilocalories,currentDayValue}', '') ~ '^-?[0-9]+(\\.[0-9]+)?$' then (b.data_json #>> '{allMetrics,metricsMap,activeKilocalories,currentDayValue}')::numeric(18,4) end
    ) as metric_value_num,
    null::text as metric_value_text,
    'kcal'::text as metric_unit,
    '$.active_kcal'::text as value_source_path,
    b.occurred_at,
    b.ingested_at,
    '{}'::jsonb as extra_json
  from base b
),
recursive_flattened as (
  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    b.occurred_at,
    b.ingested_at,
    '$'::text as json_path,
    b.data_json as value_json
  from base b
  where b.metric_type <> 'activities'

  union all

  select
    f.health_event_id,
    f.raw_id,
    f.account_ref,
    f.metric_date,
    f.metric_type,
    f.occurred_at,
    f.ingested_at,
    c.next_path,
    c.next_value
  from recursive_flattened f
  join lateral (
    select
      f.json_path || '.' || e.key as next_path,
      e.value as next_value
    from jsonb_each(f.value_json) as e
    where jsonb_typeof(f.value_json) = 'object'

    union all

    select
      f.json_path || '[' || (a.ordinality - 1)::text || ']' as next_path,
      a.value as next_value
    from jsonb_array_elements(f.value_json) with ordinality as a(value, ordinality)
    where jsonb_typeof(f.value_json) = 'array'
  ) as c on true
  where jsonb_typeof(f.value_json) in ('object', 'array')
),
leaf_metrics as (
  select
    f.health_event_id,
    f.raw_id,
    f.account_ref,
    f.metric_date,
    f.metric_type,
    lower(trim(both '_' from regexp_replace(regexp_replace(f.json_path, '[^a-zA-Z0-9]+', '_', 'g'), '_+', '_', 'g'))) as metric_name,
    case
      when jsonb_typeof(f.value_json) = 'number' then (f.value_json::text)::numeric(18,4)
      when jsonb_typeof(f.value_json) = 'string'
        and nullif(trim(both '"' from f.value_json::text), '') ~ '^-?[0-9]+(\\.[0-9]+)?$'
        then (trim(both '"' from f.value_json::text))::numeric(18,4)
      else null
    end as metric_value_num,
    case
      when jsonb_typeof(f.value_json) = 'string' then nullif(trim(both '"' from f.value_json::text), '')
      when jsonb_typeof(f.value_json) = 'boolean' then f.value_json::text
      else null
    end as metric_value_text,
    case
      when f.json_path ~* '(heart[_]?rate|bpm)' then 'bpm'
      when f.json_path ~* '(duration|second|time)' then 'seconds'
      when f.json_path ~* '(distance|meter)' then 'meters'
      when f.json_path ~* '(calorie|kcal)' then 'kcal'
      when f.json_path ~* '(percent|percentage|spo2)' then '%'
      else null
    end as metric_unit,
    f.json_path as value_source_path,
    f.occurred_at,
    f.ingested_at,
    jsonb_build_object('value_type', jsonb_typeof(f.value_json)) as extra_json
  from recursive_flattened f
  where jsonb_typeof(f.value_json) not in ('object', 'array')
    and f.json_path <> '$'
),
metric_rows as (
  select
    s.health_event_id,
    s.raw_id,
    s.account_ref,
    s.metric_date,
    s.metric_type,
    s.metric_name,
    s.metric_value_num,
    s.metric_value_text,
    s.metric_unit,
    s.value_source_path,
    'ok'::text as quality_flag,
    s.occurred_at,
    s.ingested_at,
    s.extra_json
  from special_metrics s
  where s.metric_value_num is not null

  union all

  select
    l.health_event_id,
    l.raw_id,
    l.account_ref,
    l.metric_date,
    l.metric_type,
    l.metric_name,
    l.metric_value_num,
    case
      when l.metric_value_num is null then l.metric_value_text
      else null
    end as metric_value_text,
    l.metric_unit,
    l.value_source_path,
    'ok'::text as quality_flag,
    l.occurred_at,
    l.ingested_at,
    l.extra_json
  from leaf_metrics l
  where l.metric_name is not null
    and (l.metric_value_num is not null or (l.metric_value_text is not null and length(l.metric_value_text) <= 128))
),
events_with_rows as (
  select distinct health_event_id
  from metric_rows
),
fallback_rows as (
  select
    b.health_event_id,
    b.raw_id,
    b.account_ref,
    b.metric_date,
    b.metric_type,
    'event_payload'::text as metric_name,
    null::numeric(18,4) as metric_value_num,
    null::text as metric_value_text,
    null::text as metric_unit,
    '$'::text as value_source_path,
    case
      when b.data_json is null or b.data_json in ('{}'::jsonb, '[]'::jsonb) then 'no_data'
      else 'parse_failed'
    end as quality_flag,
    b.occurred_at,
    b.ingested_at,
    jsonb_build_object('fallback', true) as extra_json
  from base b
  where not exists (
    select 1
    from events_with_rows e
    where e.health_event_id = b.health_event_id
  )
),
final_rows as (
  select * from metric_rows
  union all
  select * from fallback_rows
)
select
  md5(
    final_rows.health_event_id::text
    || '::' || final_rows.metric_name
    || '::' || final_rows.value_source_path
    || '::' || coalesce(final_rows.metric_value_num::text, '')
    || '::' || coalesce(final_rows.metric_value_text, '')
  ) as metric_row_id,
  final_rows.health_event_id,
  final_rows.raw_id,
  final_rows.account_ref,
  final_rows.metric_date,
  final_rows.metric_type,
  final_rows.metric_name,
  final_rows.metric_value_num,
  final_rows.metric_value_text,
  final_rows.metric_unit,
  final_rows.value_source_path,
  final_rows.quality_flag,
  final_rows.occurred_at,
  final_rows.ingested_at,
  final_rows.extra_json
from final_rows
