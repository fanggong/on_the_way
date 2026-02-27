{{ config(alias='health_activity_event_fact') }}

with ranked as (
  select
    activity_event_id,
    account_ref,
    activity_id,
    activity_type,
    sport_sub_type as activity_sub_type,
    metric_date,
    start_at,
    duration_seconds,
    distance_meters,
    calories_kcal,
    avg_heart_rate_bpm,
    max_heart_rate_bpm,
    elevation_gain_meters,
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
    steps_count,
    lap_count,
    avg_temperature_c,
    max_temperature_c,
    route_id,
    course_id,
    gear_id,
    source_json,
    row_number() over (
      partition by account_ref, activity_id
      order by metric_date desc, start_at desc nulls last, activity_event_id desc
    ) as row_rank
  from {{ ref('int_canonical__health_activity_event') }}
),
final as (
  select
    md5(concat_ws('::', coalesce(account_ref, ''), coalesce(activity_id, ''))) as domain_activity_row_id,
    account_ref,
    activity_id,
    activity_type,
    activity_sub_type,
    coalesce((start_at at time zone 'Asia/Shanghai')::date, metric_date) as activity_date,
    start_at,
    duration_seconds,
    distance_meters,
    calories_kcal,
    avg_heart_rate_bpm,
    max_heart_rate_bpm,
    elevation_gain_meters,
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
    steps_count,
    lap_count,
    avg_temperature_c,
    max_temperature_c,
    route_id,
    course_id,
    gear_id,
    source_json,
    (
      account_ref is not null
      and account_ref <> ''
      and activity_id is not null
      and activity_id <> ''
      and activity_type is not null
      and activity_type <> ''
    ) as is_valid
  from ranked
  where row_rank = 1
)
select
  domain_activity_row_id,
  account_ref,
  activity_id,
  activity_type,
  activity_sub_type,
  activity_date,
  start_at,
  duration_seconds,
  distance_meters,
  calories_kcal,
  avg_heart_rate_bpm,
  max_heart_rate_bpm,
  elevation_gain_meters,
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
  steps_count,
  lap_count,
  avg_temperature_c,
  max_temperature_c,
  route_id,
  course_id,
  gear_id,
  source_json,
  is_valid
from final
