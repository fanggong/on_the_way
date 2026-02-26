# poc_signal 专项说明 v0.1.0

版本: `v0.1.0`  
日期: `2026-02-25`

## 1. 边界

`poc_signal` 为独立 POC 系统，用于验证统一分层架构，不承载 8 大正式系统业务语义。

包含:
- 信号事件值 `value_num`（0-100）
- 信号来源 `manual/connector`
- 发生时间 `occurred_at`
- 标注融合（`annotation.annotation`）

不包含:
- 健康/时间/收入/财务/能力/关系/生活/保障领域语义建模

## 2. 双数据源

- 客户端: `ios_manual` 通过 `POST /v1/ingest/manual-signal`
- 连接器: `signal_random_connector` 默认 300 秒周期写入 `POST /v1/ingest/connector-signal`

## 3. 幂等规则

幂等键: `source_id + external_id`

- 同键且 payload 一致: 返回 `idempotent=true`
- 同键但 payload/occurred_at 不一致: 返回 `DUPLICATE_IDEMPOTENCY_KEY`

## 4. 标注融合规则

- `annotation.target_type = signal_event`
- `annotation.target_id = domain_poc_signal.signal_event.signal_event_id`
- 若存在 `quality_tag=suspect_outlier`，Domain 标记 `is_valid=false`
- Mart 仅聚合 `is_valid=true` 事件

## 5. 分层落地

- Raw: `raw.raw_event`
- Canonical: `canonical.event`
- Domain: `domain_poc_signal.signal_event`
- Mart: `mart_poc_signal.signal_daily_summary`

## 6. 验收路径

- P1: iOS 手工录入 -> Raw -> dbt -> Mart -> iOS 查询
- P2: 连接器写入 -> Raw -> dbt -> Mart -> API 查询
- P3: Annotation 写入 -> Domain `is_valid` 变化 -> Mart 变化
- P4: dbt 元数据可供 OpenMetadata 接入
