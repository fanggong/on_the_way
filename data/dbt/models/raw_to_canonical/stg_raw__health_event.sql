{{ config(alias='stg_raw__health_event') }}

select
  raw_id,
  source_id,
  external_id,
  source_id || '::' || external_id as idempotency_key,
  occurred_at,
  ingested_at,
  cast(payload_json as jsonb) as payload_json,
  cast(payload_json as jsonb) as attributes_json,
  payload_json ->> 'connector' as connector,
  payload_json ->> 'connector_version' as connector_version,
  payload_json ->> 'account_ref' as account_ref,
  payload_json ->> 'metric_type' as metric_type,
  case
    when coalesce(payload_json ->> 'metric_date', '') ~ '^\d{4}-\d{2}-\d{2}$'
      then (payload_json ->> 'metric_date')::date
    else null
  end as metric_date,
  payload_json ->> 'timezone' as timezone,
  case
    when coalesce(payload_json ->> 'fetched_at', '') <> ''
      then (payload_json ->> 'fetched_at')::timestamptz
    else null
  end as fetched_at,
  nullif(payload_json ->> 'api_method', '') as api_method,
  coalesce(payload_json -> 'data', '{}'::jsonb) as data_json
from {{ source('raw', 'raw_event') }}
where source_id = 'garmin_connect_health'
