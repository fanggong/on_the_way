# On The Way 产品文档 v0.3.1

版本: `v0.3.1`  
日期: `2026-02-27`  
状态: `已验收（已完成）`  
面向角色: 产品、数据研发、后端研发、数据治理、测试

---

## 1. 版本定位与当前进度

### 1.1 当前项目进度（截至 2026-02-27）
- `v0.1.0` 已完成并验证 `Raw -> Canonical -> Domain -> Mart`（POC系统 `poc_signal`）。
- `v0.2.0` 已验收（iOS 首页 UI/UX 改造，不涉及数据层）。
- `v0.3.0` 已验收（健康系统 Garmin 连接器入 Raw，范围止于 `raw.raw_event`）。
- `v0.3.1` 已验收（健康链路分层落地 + POC 全量退役 + OpenMetadata 遗留元数据清理）。

### 1.2 v0.3.1 核心目标
1. 按统一框架完成健康系统 `raw -> canonical -> domain -> mart` ETL（基于现有 Garmin Raw 数据契约）。
2. 完善表与字段注释，确保在 OpenMetadata 可查看（包含存量与 v0.3.1 新增对象）。
3. 退役 v0.1.0 POC 系统：删除 POC 相关代码、数据库对象与历史数据。
4. 在 Mart 层新增活动主题表（覆盖骑行等活动类型）。

### 1.3 成功标准（版本级）
- 健康数据从 `raw.raw_event(source_id=garmin_connect_health)` 稳定进入 `canonical`、`domain_health` 与统一 `mart` schema。
- dbt 构建通过，核心测试通过，Mart 产出可直接消费。
- `mart.health_activity_topic_daily` 可稳定产出活动主题聚合（含骑行等类型）。
- OpenMetadata 中可检索到目标表，且表级/字段级描述完整可见。
- v0.1.0 POC 相关接口、模型、表、数据均完成退役，不再作为运行能力存在。

---

## 2. 范围与非目标

### 2.1 In Scope
1. 健康系统 Canonical 模型建设。
2. 健康系统 Domain 模型建设（`domain_health`）。
3. 健康系统 Mart 模型建设（统一 `mart` schema）。
4. dbt 模型测试与验收 SQL 补齐。
5. 注释治理落地：
   - dbt `description`
   - PostgreSQL `COMMENT ON`
   - OpenMetadata ingestion 范围与验收流程
6. POC 退役（强制）：
   - 删除 v0.1.0 POC 相关后端/API/dbt/iOS 代码
   - 删除 POC 相关数据库对象与数据
7. 文档与运行说明同步到 v0.3.1。

### 2.2 Out of Scope
1. Garmin 连接器采集协议重构（沿用 v0.3.0）。
2. iOS 健康页面与可视化 UI。
3. 复杂主数据治理/多账号权限体系。

### 2.3 本版本边界约束
1. 不再承诺兼容 `poc_signal` 历史能力。
2. POC 退役任务属于 v0.3.1 必做项，不允许“保留旧链路备用”。

### 2.4 分层框架强制约束（修正）
1. ETL 分层必须严格为：`raw -> canonical -> domain -> mart`。
2. Domain 层必须按系统分 schema：本版本健康系统使用 `domain_health`。
3. Mart 层必须跨系统统一一个 schema：本版本统一使用 `mart`。

---

## 3. 现状差距（用于研发开工）

| 主题 | 当前状态 | v0.3.1 目标 |
|---|---|---|
| Health ETL 分层 | 仅 Raw 入库 | 补齐 Canonical + Domain + Mart |
| dbt 健康模型 | 无 | 新增健康模型目录与测试 |
| Canonical 健康对象 | 无 | 形成统一健康事件与指标明细模型 |
| Domain 健康对象 | 无 | 形成健康领域事实与活动主题事实 |
| Mart 健康对象 | 无 | 在统一 `mart` schema 形成健康日汇总与可消费总览 |
| Mart 活动主题 | 无 | 新增活动主题聚合表（骑行等） |
| 模型注释 | 大量缺失 | 表/字段描述全覆盖 |
| DB 原生 COMMENT | 基本缺失 | 全量关键表字段补 COMMENT |
| OpenMetadata schema 采集范围 | 未覆盖 health/mart 及 app | 覆盖并可检索 |
| POC 运行代码 | 仍存在于 API/dbt/iOS | 全量删除 |
| POC DB 对象与数据 | 仍存在 | 全量删除 |

---

## 4. v0.3.1 总体架构

```text
health path:
raw.raw_event (source_id=garmin_connect_health)
  -> canonical.stg_raw__health_event
  -> canonical.health_event
  -> canonical.health_metric_daily
  -> canonical.health_activity_event
  -> domain_health.health_metric_daily_fact
  -> domain_health.health_activity_event_fact
  -> mart.health_metric_daily_summary
  -> mart.health_daily_overview
  -> mart.health_activity_topic_daily

metadata path:
Postgres COMMENT + dbt description
  -> OpenMetadata Postgres ingestion + dbt ingestion

legacy cleanup path:
remove POC API/dbt/client code
  + drop domain_poc_signal/mart_poc_signal
  + delete POC raw/audit/annotation data
```

---

## 5. 数据模型定义（可直接开发）

## 5.1 Raw 输入契约（沿用 v0.3.0）

来源表: `raw.raw_event`  
过滤条件: `source_id = 'garmin_connect_health'`

Raw payload 关键字段：
- `payload_json.connector` = `garmin_connect`
- `payload_json.metric_type`
- `payload_json.metric_date` (`YYYY-MM-DD`)
- `payload_json.account_ref`
- `payload_json.fetched_at`（带 `+08:00`）
- `payload_json.data`（Garmin 原始对象）

连接器字段观察（基于当前代码实现）：
1. payload 顶层固定字段：`connector`、`connector_version`、`account_ref`、`metric_type`、`metric_date`、`timezone`、`fetched_at`、`api_method`、`data`。
2. `metric_type` 当前支持 32 项（含 `activities`、`training_status`、`training_readiness`、`workouts` 等活动相关指标）。
3. `activities` 通过 `get_activities_by_date` / `get_activities` 获取，原始结构不做强改写直接落入 `payload_json.data`。
4. 若 SDK 返回数组，连接器会包装为 `{"value": [...]}`；Canonical 解析需同时兼容对象和数组包装两种形态。

---

## 5.2 Canonical 层目标

### A. `canonical.health_event`（健康事件主表）
粒度: 一条 Raw 健康事件对应一行

| 字段 | 类型 | 说明 |
|---|---|---|
| `health_event_id` | uuid | 主键，默认使用 `raw_id` |
| `raw_id` | uuid | 回溯 Raw 主键 |
| `source_id` | text | 固定 `garmin_connect_health` |
| `external_id` | text | 幂等外部键 |
| `account_ref` | text | 脱敏账号标识 |
| `metric_type` | text | 健康指标类型（32项集合） |
| `metric_date` | date | 业务日期 |
| `timezone` | text | 默认 `Asia/Shanghai` |
| `occurred_at` | timestamptz | `metric_date 00:00:00+08:00` |
| `fetched_at` | timestamptz | 连接器拉取时间 |
| `connector_version` | text | 连接器版本 |
| `api_method` | text | SDK 调用方法名（可空） |
| `data_json` | jsonb | Garmin 原始 data 对象 |
| `payload_json` | jsonb | 完整 payload |
| `ingested_at` | timestamptz | Raw 入库时间 |

### B. `canonical.health_metric_daily`（健康指标标准明细）
粒度: `health_event_id + metric_name`（长表）

| 字段 | 类型 | 说明 |
|---|---|---|
| `metric_row_id` | text | 主键（建议 hash） |
| `health_event_id` | uuid | 关联 `canonical.health_event` |
| `raw_id` | uuid | 回溯键 |
| `account_ref` | text | 脱敏账号标识 |
| `metric_date` | date | 业务日期 |
| `metric_type` | text | 来源指标类型 |
| `metric_name` | text | 标准指标名（统一命名） |
| `metric_value_num` | numeric(18,4) | 数值型值 |
| `metric_value_text` | text | 文本型值（可空） |
| `metric_unit` | text | 单位（如 bpm/min/kg/%） |
| `value_source_path` | text | 提取来源 JSON path |
| `quality_flag` | text | `ok/no_data/not_supported/parse_failed` |
| `occurred_at` | timestamptz | 事件时间 |
| `ingested_at` | timestamptz | 入库时间 |
| `extra_json` | jsonb | 扩展信息（保留） |

### C. Canonical 规则
1. `health_event` 必须覆盖 Raw 健康记录 1:1。
2. `health_metric_daily` 可 1:N 展开；当不可提取时也要落一条 `quality_flag != ok` 的记录，避免静默丢失。
3. `metric_name` 命名采用 snake_case，跨 metric_type 可复用同一语义名。
4. 不在 Canonical 层做业务汇总口径，仅做标准化与可追溯拆解。

### D. `canonical.health_activity_event`（活动标准事件明细）
粒度: `account_ref + activity_id`

来源：
- `canonical.health_event` 中 `metric_type='activities'` 的记录拆解。

| 字段 | 类型 | 说明 |
|---|---|---|
| `activity_event_id` | text | 主键（建议 hash） |
| `health_event_id` | uuid | 关联健康事件 |
| `raw_id` | uuid | 回溯键 |
| `account_ref` | text | 脱敏账号标识 |
| `metric_date` | date | 业务日期 |
| `activity_id` | text | Garmin 活动唯一标识 |
| `activity_type` | text | Garmin 原始活动类型名称（例如 `road_biking`、`indoor_cycling`） |
| `start_at` | timestamptz | 活动开始时间 |
| `duration_seconds` | numeric(18,4) | 活动时长（秒） |
| `distance_meters` | numeric(18,4) | 距离（米） |
| `calories_kcal` | numeric(18,4) | 消耗（kcal） |
| `avg_heart_rate_bpm` | numeric(18,4) | 平均心率 |
| `max_heart_rate_bpm` | numeric(18,4) | 最大心率 |
| `elevation_gain_meters` | numeric(18,4) | 爬升（米） |
| `sport_sub_type` | text | 活动子类型（占位） |
| `activity_name` | text | 活动名称（占位） |
| `device_name` | text | 设备名称（占位） |
| `is_indoor` | boolean | 是否室内（占位） |
| `moving_seconds` | numeric(18,4) | 移动时长（秒，占位） |
| `elapsed_seconds` | numeric(18,4) | 总历时时长（秒，占位） |
| `avg_speed_mps` | numeric(18,4) | 平均速度（m/s，占位） |
| `max_speed_mps` | numeric(18,4) | 最大速度（m/s，占位） |
| `avg_cadence_rpm` | numeric(18,4) | 平均踏频（rpm，占位） |
| `max_cadence_rpm` | numeric(18,4) | 最大踏频（rpm，占位） |
| `avg_power_watts` | numeric(18,4) | 平均功率（W，占位） |
| `max_power_watts` | numeric(18,4) | 最大功率（W，占位） |
| `normalized_power_watts` | numeric(18,4) | 标准化功率（W，占位） |
| `training_effect_aerobic` | numeric(18,4) | 有氧训练效果（占位） |
| `training_effect_anaerobic` | numeric(18,4) | 无氧训练效果（占位） |
| `training_load` | numeric(18,4) | 训练负荷（占位） |
| `vo2max` | numeric(18,4) | VO2max（占位） |
| `ftp_watts` | numeric(18,4) | FTP 功率（W，占位） |
| `steps_count` | numeric(18,4) | 活动步数（占位） |
| `lap_count` | int | 圈数（占位） |
| `avg_temperature_c` | numeric(18,4) | 平均温度（摄氏，占位） |
| `max_temperature_c` | numeric(18,4) | 最高温度（摄氏，占位） |
| `route_id` | text | 路线 ID（占位） |
| `course_id` | text | 课程 ID（占位） |
| `gear_id` | text | 装备 ID（占位） |
| `source_json` | jsonb | 原始活动对象 |
| `reserved_json` | jsonb | 未来扩展占位（原样透传补充字段） |

规则：
1. 无有效 `activity_id` 的活动记录不进入该表。
2. `activity_type` 需做标准化映射，无法识别时落 `other`。
3. 该表仅承载活动实体，不做聚合。
4. 标记为“占位”的字段在 v0.3.1 必须建列，允许全量为 `null`。

---

## 5.3 Domain 层目标（健康系统）

### A. `domain_health.health_metric_daily_fact`（健康指标领域事实）
粒度: `account_ref + metric_date + metric_name`

来源：
- `canonical.health_metric_daily`

| 字段 | 类型 | 说明 |
|---|---|---|
| `domain_metric_row_id` | text | 领域事实主键 |
| `account_ref` | text | 脱敏账号标识 |
| `metric_date` | date | 业务日期 |
| `metric_type` | text | 来源指标类型 |
| `metric_name` | text | 领域标准指标名 |
| `metric_value_num` | numeric(18,4) | 数值型值 |
| `metric_value_text` | text | 文本型值 |
| `metric_unit` | text | 单位 |
| `quality_flag` | text | 质量标记 |
| `is_valid` | boolean | 领域有效性判定 |
| `source_count` | int | 来源样本数 |
| `first_occurred_at` | timestamptz | 首次事件时间 |
| `last_occurred_at` | timestamptz | 最新事件时间 |
| `latest_ingested_at` | timestamptz | 最新入库时间 |

规则：
1. `quality_flag='ok'` 且数值可解析时，`is_valid=true`。
2. Domain 层允许融合业务口径（如异常阈值、单位归一化）。
3. 该表为 Mart 汇总的唯一指标事实输入，不直接从 Canonical 进 Mart。

### B. `domain_health.health_activity_event_fact`（活动领域事实）
粒度: `account_ref + activity_id`

来源：
- `canonical.health_activity_event`

| 字段 | 类型 | 说明 |
|---|---|---|
| `domain_activity_row_id` | text | 领域活动主键 |
| `account_ref` | text | 脱敏账号标识 |
| `activity_id` | text | 活动 ID |
| `activity_type` | text | 领域活动类型 |
| `activity_sub_type` | text | 活动子类型 |
| `activity_date` | date | 活动日期 |
| `start_at` | timestamptz | 活动开始时间 |
| `duration_seconds` | numeric(18,4) | 时长（秒） |
| `distance_meters` | numeric(18,4) | 距离（米） |
| `calories_kcal` | numeric(18,4) | 消耗（kcal） |
| `avg_heart_rate_bpm` | numeric(18,4) | 平均心率 |
| `max_heart_rate_bpm` | numeric(18,4) | 最大心率 |
| `elevation_gain_meters` | numeric(18,4) | 爬升（米） |
| `is_valid` | boolean | 领域有效性判定 |
| `source_json` | jsonb | 来源对象 |

规则：
1. 活动类型沿用 Garmin 原始命名，不做统一归类映射。
2. 该表作为活动主题 Mart 的唯一输入事实表。
3. 占位字段可透传到 `source_json`，不阻塞本版本产出。

## 5.4 Mart 层目标（统一 schema：`mart`）

### A. `mart.health_metric_daily_summary`（日级长表汇总）
粒度: `account_ref + stat_date + metric_name`

| 字段 | 类型 | 说明 |
|---|---|---|
| `account_ref` | text | 脱敏账号标识 |
| `stat_date` | date | 统计日期 |
| `metric_name` | text | 标准指标名 |
| `sample_count` | bigint | 样本条数 |
| `value_avg` | numeric(18,4) | 均值 |
| `value_min` | numeric(18,4) | 最小值 |
| `value_max` | numeric(18,4) | 最大值 |
| `latest_occurred_at` | timestamptz | 最新事件时间 |
| `latest_ingested_at` | timestamptz | 最新入库时间 |
| `quality_ok_count` | bigint | `quality_flag=ok` 条数 |
| `quality_issue_count` | bigint | 非 `ok` 条数 |

### B. `mart.health_daily_overview`（日级总览宽表）
粒度: `account_ref + stat_date`

| 字段 | 类型 | 说明 |
|---|---|---|
| `account_ref` | text | 脱敏账号标识 |
| `stat_date` | date | 统计日期 |
| `sleep_duration_min` | numeric(18,4) | 睡眠时长（分钟） |
| `resting_hr_bpm` | numeric(18,4) | 静息心率 |
| `stress_level_avg` | numeric(18,4) | 压力均值 |
| `body_battery_avg` | numeric(18,4) | 身体电量均值 |
| `steps_count` | numeric(18,4) | 步数 |
| `active_kcal` | numeric(18,4) | 活动消耗 |
| `coverage_metric_count` | int | 当日有值指标数 |
| `quality_issue_count` | int | 当日质量问题总数 |
| `updated_at` | timestamptz | Mart 刷新时间 |

### C. `mart.health_activity_topic_daily`（活动主题表）
粒度: `account_ref + stat_date + activity_type`

| 字段 | 类型 | 说明 |
|---|---|---|
| `account_ref` | text | 脱敏账号标识 |
| `stat_date` | date | 统计日期 |
| `activity_type` | text | Garmin 原始活动类型名称（例如 `road_biking`、`indoor_cycling`） |
| `activity_count` | bigint | 活动次数 |
| `duration_seconds_sum` | numeric(18,4) | 总时长（秒） |
| `distance_meters_sum` | numeric(18,4) | 总距离（米） |
| `calories_kcal_sum` | numeric(18,4) | 总消耗（kcal） |
| `moving_seconds_sum` | numeric(18,4) | 移动时长合计（秒，占位） |
| `elapsed_seconds_sum` | numeric(18,4) | 历时时长合计（秒，占位） |
| `avg_speed_mps_avg` | numeric(18,4) | 平均速度均值（m/s，占位） |
| `max_speed_mps_max` | numeric(18,4) | 最大速度峰值（m/s，占位） |
| `avg_cadence_rpm_avg` | numeric(18,4) | 平均踏频均值（rpm，占位） |
| `max_cadence_rpm_max` | numeric(18,4) | 最大踏频峰值（rpm，占位） |
| `avg_power_watts_avg` | numeric(18,4) | 平均功率均值（W，占位） |
| `max_power_watts_max` | numeric(18,4) | 最大功率峰值（W，占位） |
| `normalized_power_watts_avg` | numeric(18,4) | 标准化功率均值（W，占位） |
| `training_effect_aerobic_avg` | numeric(18,4) | 有氧训练效果均值（占位） |
| `training_effect_anaerobic_avg` | numeric(18,4) | 无氧训练效果均值（占位） |
| `training_load_sum` | numeric(18,4) | 训练负荷合计（占位） |
| `steps_count_sum` | numeric(18,4) | 步数合计（占位） |
| `lap_count_sum` | bigint | 圈数合计（占位） |
| `avg_temperature_c_avg` | numeric(18,4) | 平均温度均值（占位） |
| `max_temperature_c_max` | numeric(18,4) | 最高温度峰值（占位） |
| `route_covered_count` | bigint | 路线覆盖数（distinct route_id，占位） |
| `gear_used_count` | bigint | 装备使用数（distinct gear_id，占位） |
| `avg_heart_rate_bpm_avg` | numeric(18,4) | 平均心率均值 |
| `max_heart_rate_bpm_max` | numeric(18,4) | 最大心率峰值 |
| `elevation_gain_meters_sum` | numeric(18,4) | 总爬升（米） |
| `latest_start_at` | timestamptz | 当日最近活动开始时间 |
| `updated_at` | timestamptz | Mart 刷新时间 |

口径说明：
1. 基于 `domain_health.health_activity_event_fact` 聚合生成。
2. 聚合统计按 Garmin 原始活动类型输出，不额外归并到人工枚举。
3. 该表用于活动主题分析（如骑行趋势、训练负荷、活动结构对比）。
4. 占位聚合字段允许全量为 `null`，但列必须在本版本创建。

---

## 6. dbt 实施与目录改造要求

## 6.1 新增模型目录（health）
- `data/dbt/models/raw_to_canonical/`
  - `stg_raw__health_event.sql`
  - `int_canonical__health_event.sql`
  - `int_canonical__health_metric_daily.sql`
  - `int_canonical__health_activity_event.sql`
  - `schema_health.yml`
- `data/dbt/models/canonical_to_domain_health/`
  - `fct_domain_health__health_metric_daily_fact.sql`
  - `fct_domain_health__health_activity_event_fact.sql`
  - `schema.yml`
- `data/dbt/models/domain_health_to_mart/`
  - `mart__health_metric_daily_summary.sql`
  - `mart__health_daily_overview.sql`
  - `mart__health_activity_topic_daily.sql`
  - `schema.yml`

## 6.2 删除模型目录（POC）
- `data/dbt/models/canonical_to_domain_poc_signal/`
- `data/dbt/models/domain_poc_signal_to_mart/`
- `data/dbt/tests/test_mart_event_count_consistency.sql`（如仅服务 POC）
- 其他仅服务 POC 的测试与文档条目

## 6.3 dbt_project 配置调整
1. 删除 POC 目录配置：
   - `canonical_to_domain_poc_signal`
   - `domain_poc_signal_to_mart`
2. 新增健康目录配置：
   - `canonical_to_domain_health -> schema domain_health`
   - `domain_health_to_mart -> schema mart`
3. 开启文档持久化：
   - `+persist_docs.relation: true`
   - `+persist_docs.columns: true`

## 6.4 活动占位字段实施约束
1. 活动占位字段在 v0.3.1 必须建列（Canonical + Domain + Mart），避免后续 DDL 破坏性变更。
2. 占位字段默认可空，不设置 `not null` 与强校验测试。
3. 当前无稳定来源时，值统一保留 `null`，并通过注释标记“占位字段”。

---

## 7. 注释与 OpenMetadata 治理要求（强制）

## 7.1 覆盖范围
v0.3.1 必须覆盖以下对象（存量 + 新增）：
- `raw.*`
- `canonical.*`
- `domain_health.*`
- `mart.*`
- `annotation.*`
- `app.*`

说明：
- 已退役对象（`domain_poc_signal.*`、`mart_poc_signal.*`）不再纳入“存量可见”范围，需从元数据采集范围中移除。

## 7.2 注释来源规范
1. dbt 管理对象（Canonical/Domain/Mart）：
   - 在 `schema.yml` 为模型与字段补 `description`
   - 开启 `persist_docs` 写回数据库注释
2. 非 dbt 管理对象（raw/annotation/app）：
   - 在初始化 SQL 中补齐 `COMMENT ON TABLE/COLUMN`
3. 注释内容规范：
   - 必须包含“业务语义 + 粒度 + 口径/单位”
   - 禁止仅写“ID/时间/值”等无语义描述

## 7.3 OpenMetadata ingestion 配置要求
1. `infra/docker/openmetadata/ingestion/postgres_ingestion.yml` 的 schema 白名单至少包含：
   - `raw`
   - `canonical`
   - `domain_health`
   - `mart`
   - `annotation`
   - `app`
2. 不再保留：
   - `domain_poc_signal`
   - `mart_poc_signal`
3. `dbt_ingestion.yml` 保持：
   - `dbtUpdateDescriptions: true`

---

## 8. POC 退役任务清单（新增强制任务）

## 8.1 后端/API
1. 删除 POC 写入接口：
   - `POST /v1/ingest/manual-signal`
   - `POST /v1/ingest/connector-signal`
2. 删除 POC 查询接口：
   - `GET /v1/poc/signals`
   - `GET /v1/poc/daily-summary`
3. 保留 `POST /v1/annotation`，但标注目标切换为：
   - `health_event`
   - `health_activity_event`
4. 清理仅服务 POC 的 schema/service/README 说明与示例。

## 8.2 iOS 客户端
1. 删除调试入口与页面（手工录入/结果查看）。
2. 删除仅服务 POC 的 API 客户端调用与类型定义。
3. 首页保留 v0.2.0+ 主题入口，不再暴露 POC 调试能力。

## 8.3 数据库对象
1. 删除 schema：
   - `domain_poc_signal`
   - `mart_poc_signal`
2. 删除 POC 关联数据：
   - `raw.raw_event` 中 `source_id in ('ios_manual','signal_random_connector')`
   - `app.request_audit` 中相同 `source_id` 的历史记录
   - `annotation.annotation` 中 `target_type='signal_event'` 的历史记录

## 8.4 文档
1. 所有“当前能力”文档中移除 POC 作为可运行能力的描述。
2. 保留 v0.1.0 文档仅作历史归档，显式标记“已退役”。

---

## 9. 开发任务拆分（建议）

### 9.1 数据研发
1. 新增 Canonical 健康模型与测试。
2. 新增 Domain 健康模型与测试。
3. 新增 Mart 健康模型与测试（含活动主题表，统一落 `mart` schema）。
4. 删除 POC dbt 模型、测试、配置。

### 9.2 后端研发
1. 删除 POC API 与相关 schema/service 代码。
2. 保留健康连接器接口与健康检查接口。

### 9.3 数据治理
1. 更新 OpenMetadata ingestion schema 范围。
2. 验证退役对象不再出现在主检索结果中。

### 9.4 测试
1. dbt build + tests 全通过。
2. POC 接口访问返回下线状态（404/410，按实现约定）。
3. POC 对象与数据清理 SQL 验收通过。

---

## 10. 验收标准（DoD）

### 10.1 ETL DoD
- `raw -> canonical -> domain_health -> mart` 全链路可跑通。
- `mart.health_metric_daily_summary` 与 `mart.health_daily_overview` 产数稳定。
- `mart.health_activity_topic_daily` 可稳定产出且支持骑行等活动类型聚合。

### 10.2 元数据 DoD
- 目标 schema（`raw/canonical/domain_health/mart/annotation/app`）下所有表存在表注释。
- 所有业务字段存在字段注释。
- OpenMetadata 可检索并查看描述。

### 10.3 POC 退役 DoD
1. POC API 不再可用（返回 404/410）。
2. `domain_poc_signal`、`mart_poc_signal` schema 不存在。
3. POC 源数据（Raw/Audit/Annotation）清理完成。
4. 主文档不再把 POC 描述为现行能力。

---

## 11. 验收 SQL（可直接执行）

### 11.1 健康链路行数检查
```sql
select
  (select count(*) from raw.raw_event where source_id = 'garmin_connect_health') as raw_cnt,
  (select count(*) from canonical.health_event) as canonical_event_cnt,
  (select count(*) from canonical.health_metric_daily) as canonical_metric_cnt,
  (select count(*) from domain_health.health_metric_daily_fact) as domain_metric_fact_cnt,
  (select count(*) from domain_health.health_activity_event_fact) as domain_activity_fact_cnt;
```

### 11.2 Mart 主键粒度重复检查
```sql
select account_ref, stat_date, metric_name, count(*) as dup_cnt
from mart.health_metric_daily_summary
group by 1,2,3
having count(*) > 1;
```

```sql
select account_ref, stat_date, activity_type, count(*) as dup_cnt
from mart.health_activity_topic_daily
group by 1,2,3
having count(*) > 1;
```

### 11.3 POC schema 删除验证
```sql
select schema_name
from information_schema.schemata
where schema_name in ('domain_poc_signal', 'mart_poc_signal');
```

通过标准：返回 0 行。

### 11.4 POC 数据清理验证
```sql
select count(*) as poc_raw_cnt
from raw.raw_event
where source_id in ('ios_manual', 'signal_random_connector');
```

```sql
select count(*) as poc_audit_cnt
from app.request_audit
where source_id in ('ios_manual', 'signal_random_connector');
```

```sql
select count(*) as poc_annotation_cnt
from annotation.annotation
where target_type = 'signal_event';
```

通过标准：以上计数均为 `0`。

### 11.5 活动主题表产数检查
```sql
select
  activity_type,
  count(*) as row_cnt,
  sum(activity_count) as activity_cnt
from mart.health_activity_topic_daily
group by 1
order by 1;
```

通过标准：
- 表有产数。
- 若原始数据存在骑行活动，则可见 Garmin 原始类型（如 `road_biking`、`indoor_cycling`）有对应记录。

### 11.6 活动主题占位字段建表检查
```sql
select column_name
from information_schema.columns
where table_schema = 'mart'
  and table_name = 'health_activity_topic_daily'
  and column_name in (
    'moving_seconds_sum',
    'elapsed_seconds_sum',
    'avg_speed_mps_avg',
    'max_speed_mps_max',
    'avg_cadence_rpm_avg',
    'max_cadence_rpm_max',
    'avg_power_watts_avg',
    'max_power_watts_max',
    'normalized_power_watts_avg',
    'training_effect_aerobic_avg',
    'training_effect_anaerobic_avg',
    'training_load_sum',
    'steps_count_sum',
    'lap_count_sum',
    'avg_temperature_c_avg',
    'max_temperature_c_max',
    'route_covered_count',
    'gear_used_count'
  )
order by 1;
```

通过标准：
- 返回字段数等于 `18`（全占位字段均已建出）。

### 11.7 表注释缺失检查
```sql
select n.nspname as schema_name, c.relname as table_name
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname in ('raw','canonical','domain_health','mart','annotation','app')
  and c.relkind in ('r','v','m')
  and coalesce(obj_description(c.oid, 'pg_class'), '') = ''
order by 1,2;
```

### 11.8 字段注释缺失检查
```sql
select
  n.nspname as schema_name,
  c.relname as table_name,
  a.attname as column_name
from pg_attribute a
join pg_class c on c.oid = a.attrelid
join pg_namespace n on n.oid = c.relnamespace
where n.nspname in ('raw','canonical','domain_health','mart','annotation','app')
  and c.relkind in ('r','v','m')
  and a.attnum > 0
  and not a.attisdropped
  and coalesce(col_description(a.attrelid, a.attnum), '') = ''
order by 1,2,3;
```

通过标准：11.7、11.8 均返回 0 行。

---

## 12. 一次性清理 SQL（执行手册）

> 以下 SQL 用于完成“删除 POC 对象与数据”。在生产环境执行前需先备份。

```sql
begin;

delete from annotation.annotation
where target_type = 'signal_event';

delete from app.request_audit
where source_id in ('ios_manual', 'signal_random_connector');

delete from raw.raw_event
where source_id in ('ios_manual', 'signal_random_connector');

drop schema if exists mart_poc_signal cascade;
drop schema if exists domain_poc_signal cascade;

commit;
```

---

## 13. 交付物清单（v0.3.1）

1. 产品文档（本文）：`docs/product/product_v0.3.1.md`
2. 健康 ETL 模型与测试（Canonical + Domain + Mart，含活动主题表）。
3. POC 退役改造（API/dbt/iOS/DB）。
4. 注释治理改造（dbt description + DB COMMENT）。
5. OpenMetadata ingestion 配置更新与验收记录。

---

## 14. 参考文档

- `docs/frame/frame_v1.0.md`
- `docs/product/product_v0.3.0.md`
- `docs/api/api_v0.3.0.md`
- `docs/run/交付物启动与验收说明_v0.3.0.md`
- `docs/product/product_v0.1.0.md`（历史归档参考，v0.3.1 后不再作为现行能力）
