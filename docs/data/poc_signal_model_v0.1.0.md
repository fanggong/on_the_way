# poc_signal 数据模型说明 v0.1.0

## 1. Raw

表: `raw.raw_event`

- `raw_id` (uuid, pk)
- `source_id` (text)
- `external_id` (text)
- `occurred_at` (timestamptz)
- `payload_json` (jsonb)
- `payload_hash` (text)
- `request_id` (uuid)
- `ingested_at` (timestamptz)

唯一约束: `(source_id, external_id)`

## 2. Canonical

表: `canonical.event`

- `event_id` (uuid)
- `raw_id` (uuid)
- `event_type` (text)
- `occurred_at` (timestamptz)
- `source_id` (text)
- `attributes_json` (jsonb)

## 3. Domain

表: `domain_poc_signal.signal_event`

- `signal_event_id` (uuid)
- `event_id` (uuid)
- `source_type` (`manual`/`connector`)
- `value_num` (numeric)
- `occurred_at` (timestamptz)
- `is_valid` (bool)
- `tags_json` (jsonb)

## 4. Annotation

表: `annotation.annotation`

- `annotation_id` (uuid)
- `target_type` (text)
- `target_id` (uuid)
- `label` (text)
- `value` (text)
- `created_at` (timestamptz)

## 5. Mart

表: `mart_poc_signal.signal_daily_summary`

- `stat_date` (date)
- `event_count` (int)
- `manual_count` (int)
- `connector_count` (int)
- `avg_value` (numeric)
- `min_value` (numeric)
- `max_value` (numeric)

## 6. dbt 测试

- `not_null`
- `unique`
- `relationships`
- `accepted_values`
- 自定义一致性测试:
  - `test_raw_event_idempotent_unique.sql`
  - `test_mart_event_count_consistency.sql`
