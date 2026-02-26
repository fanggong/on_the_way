{{ config(alias='stg_raw__raw_event') }}

select
  raw_id,
  source_id,
  external_id,
  source_id || '::' || external_id as idempotency_key,
  occurred_at,
  ingested_at,
  cast(payload_json as jsonb) as payload_json,
  cast(payload_json as jsonb) as attributes_json
from {{ source('raw', 'raw_event') }}
