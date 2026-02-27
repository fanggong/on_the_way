{{ config(alias='health_activity_event') }}

with activity_events as (
  select
    health_event_id,
    raw_id,
    account_ref,
    metric_date,
    data_json
  from {{ ref('int_canonical__health_event') }}
  where metric_type = 'activities'
),
activity_items as (
  select
    e.health_event_id,
    e.raw_id,
    e.account_ref,
    e.metric_date,
    item.activity_json
  from activity_events e
  cross join lateral (
    select activity_json
    from jsonb_array_elements(
      case
        when jsonb_typeof(e.data_json) = 'array' then e.data_json
        when jsonb_typeof(e.data_json -> 'value') = 'array' then e.data_json -> 'value'
        when jsonb_typeof(e.data_json -> 'activities') = 'array' then e.data_json -> 'activities'
        when jsonb_typeof(e.data_json -> 'activityList') = 'array' then e.data_json -> 'activityList'
        else '[]'::jsonb
      end
    ) as a(activity_json)
  ) item
),
prepared as (
  select
    i.health_event_id,
    i.raw_id,
    i.account_ref,
    i.metric_date,
    i.activity_json,
    coalesce(
      nullif(i.activity_json ->> 'activityId', ''),
      nullif(i.activity_json ->> 'activity_id', ''),
      nullif(i.activity_json ->> 'summaryId', ''),
      nullif(i.activity_json ->> 'id', '')
    ) as activity_id,
    coalesce(
      nullif(i.activity_json #>> '{activityType,typeKey}', ''),
      nullif(i.activity_json #>> '{activityType,typeName}', ''),
      nullif(i.activity_json ->> 'activityType', ''),
      nullif(i.activity_json ->> 'typeKey', ''),
      nullif(i.activity_json ->> 'type', ''),
      'unknown'
    ) as garmin_activity_type
  from activity_items i
),
final as (
  select
    md5(coalesce(p.account_ref, '') || '::' || p.activity_id) as activity_event_id,
    p.health_event_id,
    p.raw_id,
    p.account_ref,
    p.metric_date,
    p.activity_id,
    p.garmin_activity_type as activity_type,
    case
      when coalesce(p.activity_json ->> 'startTimeGMT', '') ~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?([zZ]|[+-]\\d{2}:\\d{2})$'
        then (p.activity_json ->> 'startTimeGMT')::timestamptz
      when coalesce(p.activity_json ->> 'startTime', '') ~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?([zZ]|[+-]\\d{2}:\\d{2})$'
        then (p.activity_json ->> 'startTime')::timestamptz
      when coalesce(p.activity_json ->> 'startTimeLocal', '') ~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?$'
        then ((p.activity_json ->> 'startTimeLocal') || '+08:00')::timestamptz
      else null
    end as start_at,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'duration', ''), 'numeric')
          then (p.activity_json ->> 'duration')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'durationInSeconds', ''), 'numeric')
          then (p.activity_json ->> 'durationInSeconds')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'movingDuration', ''), 'numeric')
          then (p.activity_json ->> 'movingDuration')::numeric(18,4)
      end
    ) as duration_seconds,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'distance', ''), 'numeric')
          then (p.activity_json ->> 'distance')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'distanceInMeters', ''), 'numeric')
          then (p.activity_json ->> 'distanceInMeters')::numeric(18,4)
      end
    ) as distance_meters,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'calories', ''), 'numeric')
          then (p.activity_json ->> 'calories')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'kcal', ''), 'numeric')
          then (p.activity_json ->> 'kcal')::numeric(18,4)
      end
    ) as calories_kcal,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'averageHR', ''), 'numeric')
          then (p.activity_json ->> 'averageHR')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'avgHR', ''), 'numeric')
          then (p.activity_json ->> 'avgHR')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'averageHeartRate', ''), 'numeric')
          then (p.activity_json ->> 'averageHeartRate')::numeric(18,4)
      end
    ) as avg_heart_rate_bpm,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'maxHR', ''), 'numeric')
          then (p.activity_json ->> 'maxHR')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'maxHeartRate', ''), 'numeric')
          then (p.activity_json ->> 'maxHeartRate')::numeric(18,4)
      end
    ) as max_heart_rate_bpm,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'elevationGain', ''), 'numeric')
          then (p.activity_json ->> 'elevationGain')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'elevationGainInMeters', ''), 'numeric')
          then (p.activity_json ->> 'elevationGainInMeters')::numeric(18,4)
      end
    ) as elevation_gain_meters,
    coalesce(
      nullif(p.activity_json #>> '{activityType,parentTypeId}', ''),
      nullif(p.activity_json ->> 'sportSubType', '')
    ) as sport_sub_type,
    coalesce(
      nullif(p.activity_json ->> 'activityName', ''),
      nullif(p.activity_json ->> 'name', '')
    ) as activity_name,
    coalesce(
      nullif(p.activity_json ->> 'deviceName', ''),
      nullif(p.activity_json ->> 'sourceDeviceName', '')
    ) as device_name,
    case
      when lower(coalesce(p.activity_json ->> 'isIndoor', '')) = 'true' then true
      when lower(coalesce(p.activity_json ->> 'isIndoor', '')) = 'false' then false
      when lower(coalesce(p.activity_json ->> 'indoor', '')) = 'true' then true
      when lower(coalesce(p.activity_json ->> 'indoor', '')) = 'false' then false
      else null
    end as is_indoor,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'movingDuration', ''), 'numeric')
        then (p.activity_json ->> 'movingDuration')::numeric(18,4)
    end as moving_seconds,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'elapsedDuration', ''), 'numeric')
        then (p.activity_json ->> 'elapsedDuration')::numeric(18,4)
    end as elapsed_seconds,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'averageSpeed', ''), 'numeric')
        then (p.activity_json ->> 'averageSpeed')::numeric(18,4)
    end as avg_speed_mps,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'maxSpeed', ''), 'numeric')
        then (p.activity_json ->> 'maxSpeed')::numeric(18,4)
    end as max_speed_mps,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'averageCadence', ''), 'numeric')
        then (p.activity_json ->> 'averageCadence')::numeric(18,4)
    end as avg_cadence_rpm,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'maxCadence', ''), 'numeric')
        then (p.activity_json ->> 'maxCadence')::numeric(18,4)
    end as max_cadence_rpm,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'averagePower', ''), 'numeric')
        then (p.activity_json ->> 'averagePower')::numeric(18,4)
    end as avg_power_watts,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'maxPower', ''), 'numeric')
        then (p.activity_json ->> 'maxPower')::numeric(18,4)
    end as max_power_watts,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'normalizedPower', ''), 'numeric')
        then (p.activity_json ->> 'normalizedPower')::numeric(18,4)
    end as normalized_power_watts,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'aerobicTrainingEffect', ''), 'numeric')
        then (p.activity_json ->> 'aerobicTrainingEffect')::numeric(18,4)
    end as training_effect_aerobic,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'anaerobicTrainingEffect', ''), 'numeric')
        then (p.activity_json ->> 'anaerobicTrainingEffect')::numeric(18,4)
    end as training_effect_anaerobic,
    coalesce(
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'activityTrainingLoad', ''), 'numeric')
          then (p.activity_json ->> 'activityTrainingLoad')::numeric(18,4)
      end,
      case
        when pg_input_is_valid(nullif(p.activity_json ->> 'trainingLoad', ''), 'numeric')
          then (p.activity_json ->> 'trainingLoad')::numeric(18,4)
      end
    ) as training_load,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'vO2MaxValue', ''), 'numeric')
        then (p.activity_json ->> 'vO2MaxValue')::numeric(18,4)
    end as vo2max,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'functionalThresholdPower', ''), 'numeric')
        then (p.activity_json ->> 'functionalThresholdPower')::numeric(18,4)
    end as ftp_watts,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'steps', ''), 'numeric')
        then (p.activity_json ->> 'steps')::numeric(18,4)
    end as steps_count,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'lapCount', ''), 'integer')
        then (p.activity_json ->> 'lapCount')::int
    end as lap_count,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'avgTemperature', ''), 'numeric')
        then (p.activity_json ->> 'avgTemperature')::numeric(18,4)
    end as avg_temperature_c,
    case
      when pg_input_is_valid(nullif(p.activity_json ->> 'maxTemperature', ''), 'numeric')
        then (p.activity_json ->> 'maxTemperature')::numeric(18,4)
    end as max_temperature_c,
    nullif(p.activity_json ->> 'routeId', '') as route_id,
    nullif(p.activity_json ->> 'courseId', '') as course_id,
    nullif(p.activity_json ->> 'gearId', '') as gear_id,
    p.activity_json as source_json,
    jsonb_build_object('garmin_activity_type', p.garmin_activity_type) as reserved_json
  from prepared p
),
ranked as (
  select
    f.*,
    row_number() over (
      partition by f.account_ref, f.activity_id
      order by f.metric_date desc, f.health_event_id desc
    ) as row_rank
  from final f
)
select
  activity_event_id,
  health_event_id,
  raw_id,
  account_ref,
  metric_date,
  activity_id,
  activity_type,
  start_at,
  duration_seconds,
  distance_meters,
  calories_kcal,
  avg_heart_rate_bpm,
  max_heart_rate_bpm,
  elevation_gain_meters,
  sport_sub_type,
  activity_name,
  device_name,
  is_indoor,
  moving_seconds,
  elapsed_seconds,
  avg_speed_mps,
  max_speed_mps,
  avg_cadence_rpm,
  max_cadence_rpm,
  avg_power_watts,
  max_power_watts,
  normalized_power_watts,
  training_effect_aerobic,
  training_effect_anaerobic,
  training_load,
  vo2max,
  ftp_watts,
  steps_count,
  lap_count,
  avg_temperature_c,
  max_temperature_c,
  route_id,
  course_id,
  gear_id,
  source_json,
  reserved_json
from ranked
where activity_id is not null
  and row_rank = 1
