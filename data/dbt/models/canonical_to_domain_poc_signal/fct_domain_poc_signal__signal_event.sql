{{ config(schema='domain_poc_signal', alias='signal_event') }}

with base as (
  select
    event_id,
    occurred_at,
    case
      when source_id = 'ios_manual' then 'manual'
      when source_id = 'signal_random_connector' then 'connector'
      else 'unknown'
    end as source_type,
    cast(attributes_json ->> 'value' as numeric(10, 2)) as value_num
  from {{ ref('int_canonical__event') }}
),
annotation_agg as (
  select
    target_id,
    jsonb_object_agg(label, value) as tags_json,
    bool_or(label = 'quality_tag' and value = 'suspect_outlier') as has_suspect_outlier
  from {{ source('annotation', 'annotation') }}
  where target_type = 'signal_event'
  group by target_id
)
select
  b.event_id as signal_event_id,
  b.event_id,
  b.source_type,
  b.value_num,
  b.occurred_at,
  case when coalesce(a.has_suspect_outlier, false) then false else true end as is_valid,
  coalesce(a.tags_json, '{}'::jsonb) as tags_json
from base b
left join annotation_agg a
  on a.target_id = b.event_id
where b.source_type in ('manual', 'connector')
  and b.value_num between 0 and 100
