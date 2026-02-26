{{ config(schema='canonical', alias='event') }}

select
  raw_id as event_id,
  raw_id,
  'signal_event'::text as event_type,
  occurred_at,
  source_id,
  attributes_json
from {{ ref('stg_raw__raw_event') }}
