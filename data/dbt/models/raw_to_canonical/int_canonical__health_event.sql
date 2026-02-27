{{ config(alias='health_event') }}

select
  raw_id as health_event_id,
  raw_id,
  source_id,
  external_id,
  account_ref,
  metric_type,
  metric_date,
  coalesce(nullif(timezone, ''), 'Asia/Shanghai') as timezone,
  occurred_at,
  fetched_at,
  connector_version,
  api_method,
  data_json,
  payload_json,
  ingested_at
from {{ ref('stg_raw__health_event') }}
