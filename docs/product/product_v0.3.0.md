# On The Way 产品文档 v0.3.0

版本: `v0.3.0`  
日期: `2026-02-26`  
状态: `已验收`  
面向角色: 产品、后端研发、数据研发、运维、测试

---

## 1. 版本定位与当前进度

### 1.1 当前项目进度（输入基线）
- `v0.1.0` 已完成并验证:
  - 统一链路 `接入 -> Raw -> Canonical -> Domain -> Mart -> Serving`
  - POC 系统 `poc_signal`（iOS 手工 + 随机连接器）
- `v0.2.0` 已验收:
  - iOS 首页 UI/UX 重构
  - 不涉及后端、数据链路变更

### 1.2 v0.3.0 目标
在保持现有架构稳定的前提下，实现**健康系统真实连接器**：
- 从 `Garmin Connect` 拉取个人健康数据
- 通过后端写入 `raw.raw_event`
- 建立可运行、可重试、可观测的连接器机制

### 1.3 版本成功标准（总目标）
- Garmin 数据可稳定进入 Raw 层（非 mock、非随机）
- 连接器具备定时调度、失败重试、幂等去重
- 敏感信息不在代码仓库和日志中明文暴露
- 后端/数据/测试团队可按本文档直接开工与验收

---

## 2. 范围与非目标

### 2.1 范围（In Scope）
1. 健康系统 Garmin 连接器实现（`services/connector-worker`）。
2. 新增健康连接器写入 API（`/v1/ingest/connector-health`）。
3. 定义健康数据写入 Raw 的统一契约（`source_id / external_id / payload`）。
4. 连接器运行配置规范（环境变量、token 缓存、回填窗口）。
5. 连接器健康状态与审计记录复用现有机制（`app.connector_health`、`app.request_audit`）。

### 2.2 非目标（Out of Scope）
1. 本版本不实现 `domain_health` / `mart_health` 建模。
2. 本版本不实现 iOS 健康页面与健康指标展示。
3. 本版本不改造用户登录权限体系（仍按本地开放开发模式）。
4. 本版本不承诺覆盖 Garmin 全部接口，仅覆盖本文件定义的数据集。

---

## 3. 总体架构与数据路径

```text
garmin connect
   -> connector-worker (python-garminconnect)
   -> POST /v1/ingest/connector-health
   -> raw.raw_event
   -> (后续版本) canonical/domain_health/mart_health
```

### 3.1 组件职责
- `connector-worker`
  - 调用 Garmin Connect
  - 组装标准化 raw payload
  - 生成幂等 external_id
  - 调用后端 ingest API
- `api-service`
  - 校验健康连接器请求
  - 复用 `ingest_signal` 写入 `raw.raw_event`
  - 记录审计日志
- `postgres`
  - 作为 Raw 层事实存储
- `dbt`
  - 本版本不新增健康模型，仅保留后续扩展入口

### 3.2 与现有能力兼容性
- 保留既有接口：
  - `POST /v1/ingest/manual-signal`
  - `POST /v1/ingest/connector-signal`
- 新增接口不影响 `v0.1.0/v0.2.0` 已有联调路径。

---

## 4. Garmin 数据接入方案

参考实现: [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)

### 4.1 SDK 与登录策略
- 使用 Python 库 `garminconnect`。
- 登录方式：账号密码 + token 缓存。
- token 缓存目录建议：容器内 `/tmp/.garminconnect`（或挂载持久卷）。
- 必须支持 MFA 场景：首次登录允许人工补充验证码并续登录。

### 4.2 采集数据集（v0.3.0 全量）
本版本按以下清单**全部采集**并写入 Raw。  
说明：
- 不同 Garmin 账号/设备能力不同，部分数据集可能无权限或无数据。
- 连接器必须“尝试采集全部”，对不可用项记录 `no_data` / `not_supported`，不中断整轮任务。
- 本节定义的是**产品契约（metric_type）**，不是 SDK 方法名契约。

#### A. 基础健康（日级/高频）
- `user_summary`
- `sleep`
- `heart_rate`
- `resting_heart_rate`
- `stress`
- `body_battery`
- `respiration`
- `spo2`
- `hrv`
- `intensity_minutes`

#### B. 体成分与生理
- `weight`
- `body_composition`
- `hydration`
- `blood_pressure`
- `menstrual`
- `pregnancy`

#### C. 训练与恢复（运动相关）
- `activities`
- `training_status`
- `training_readiness`
- `recovery_time`
- `max_metrics_vo2`
- `race_prediction`
- `hill_score`
- `endurance_score`
- `lactate_threshold`

#### D. 设备与计划（辅助维度）
- `workouts`
- `training_plans`
- `devices`
- `gear`
- `goals`
- `badges`
- `challenges`

### 4.3 SDK 方法映射规则（后端实现约束）
- 后端必须维护 `metric_type -> SDK 调用函数` 的映射表（建议独立模块）。
- `python-garminconnect` 不同版本方法名可能变化，方法名以当前版本 `Garmin` 类与官方 `demo.py` 为准。
- 映射表必须支持“接口不可用”返回，不可用项写运行日志并继续处理其他数据集。
- 任一 `metric_type` 的异常不得导致整轮采集失败，除非认证失败或全局限流。

### 4.4 调度与增量策略
- 默认调度周期：`3600s`（1小时）。
- 每次运行拉取窗口：`今天 + 前2天`（默认 `3` 天窗口），吸收 Garmin 延迟同步。
- 首次部署支持回填：开发环境固定 `10` 天（`GARMIN_BACKFILL_DAYS=10`）。
- 首次回填定义：连接器第一次上线时，除“当天增量”外，额外补抓过去 `N` 天（`GARMIN_BACKFILL_DAYS`）的历史健康数据并写入 Raw。
- 如需一次性历史全量回填，可临时调大 `GARMIN_BACKFILL_DAYS` 并清理回填标记 `/tmp/.garminconnect/.backfill_done`。

---

## 5. Raw 层数据契约

### 5.1 固定字段约定（写入 `raw.raw_event`）
- `source_id`: `garmin_connect_health`
- `external_id`: `garmin::<account_ref>::<metric_type>::<metric_date>::<payload_digest16>`
- `occurred_at`: 该 `metric_date` 在账号时区 `Asia/Shanghai` 的 `00:00:00+08:00`
- `payload_json`: 采用本节定义的统一 envelope

### 5.2 payload envelope
```json
{
  "connector": "garmin_connect",
  "connector_version": "v0.3.0",
  "account_ref": "sha256(email)_12",
  "metric_type": "sleep",
  "metric_date": "2026-02-26",
  "timezone": "Asia/Shanghai",
  "fetched_at": "2026-02-26T10:10:05+08:00",
  "api_method": "get_sleep_data",
  "data": {
    "...": "原始 Garmin 返回对象"
  }
}
```

### 5.3 幂等与重复策略
- 幂等键仍为 `source_id + external_id`（复用现有实现）。
- `payload_digest16` 基于 `payload_json` 哈希生成:
  - 同 payload 重试：命中幂等（`idempotent=true`）
  - payload 发生变化：生成新 external_id，保留新事实快照

### 5.4 空数据策略
- 当某 `metric_type + date` 无数据时：
  - 不写入 `raw.raw_event`
  - 记录连接器日志 `no_data`
  - 不计为失败

---

## 6. API 与后端改造要求

### 6.1 新增 Endpoint
`POST /v1/ingest/connector-health`

请求示例：
```json
{
  "source_id": "garmin_connect_health",
  "external_id": "garmin::9f20d8a3a1f2::sleep::2026-02-26::7d9e12af4c8a309b",
  "occurred_at": "2026-02-26T00:00:00+08:00",
  "payload": {
    "connector": "garmin_connect",
    "connector_version": "v0.3.0",
    "account_ref": "9f20d8a3a1f2",
    "metric_type": "sleep",
    "metric_date": "2026-02-26",
    "timezone": "Asia/Shanghai",
    "fetched_at": "2026-02-26T10:10:05+08:00",
    "api_method": "get_sleep_data",
    "data": {}
  }
}
```

成功响应沿用统一格式：
```json
{
  "status": "ok",
  "raw_id": "uuid",
  "ingested_at": "2026-02-26T10:10:05+08:00",
  "idempotent": false
}
```

### 6.2 Schema 约束（后端）
- `source_id` 固定值：`garmin_connect_health`
- `external_id`：非空字符串，建议 `<= 128`
- `occurred_at`：必须含时区，不可超未来容忍窗口
- `payload.metric_type` 必须在允许集合中

### 6.3 代码改造落点（建议）
- `services/api/app/schemas/ingest.py`
  - 新增 `HealthConnectorIngestRequest`、`HealthConnectorPayload`
- `services/api/app/api/routes.py`
  - 新增 `/ingest/connector-health`
  - 复用 `ingest_signal`
- `services/connector-worker/connector/main.py`
  - 替换/扩展随机信号逻辑为 Garmin 拉取逻辑
- `services/connector-worker/requirements.txt`
  - 新增 `garminconnect` 依赖

---

## 7. 配置与安全要求

### 7.1 新增环境变量
| 变量名 | 默认值 | 说明 |
|---|---|---|
| `GARMIN_EMAIL` | 无 | Garmin 账号邮箱（必填） |
| `GARMIN_PASSWORD` | 无 | Garmin 密码（必填，密钥注入） |
| `GARMIN_TOKEN_DIR` | `/tmp/.garminconnect` | token 缓存目录 |
| `GARMIN_FETCH_WINDOW_DAYS` | `3` | 每轮增量窗口 |
| `GARMIN_BACKFILL_DAYS` | `10` | 开发环境首次回填天数 |
| `GARMIN_METRICS` | `all` | 拉取数据集列表（即 4.2 全量清单） |
| `GARMIN_TIMEZONE` | `Asia/Shanghai` | 账号业务时区 |
| `GARMIN_IS_CN` | `true` | Garmin SDK 中国区开关，影响接口返回质量 |
| `CONNECTOR_INTERVAL_SECONDS` | `3600` | 调度周期 |

### 7.2 凭据管理强制要求
- 禁止在仓库中提交明文账号密码。
- 禁止在日志打印 `GARMIN_PASSWORD`、token、cookie。
- 文档与示例仅保留变量名，不记录明文密码。
- 产品方提供的真实凭据仅通过 `.env`（本地）或密钥系统注入。

### 7.3 观测与告警
- 复用 `/v1/health/connector`，至少保证可观察:
  - `last_run_at`
  - `last_status`
  - `success_count / failure_count`
- 失败日志需包含：`metric_type`、`date`、`http_status/exception`。

---

## 8. 验收标准（后端可执行）

### 8.1 功能验收
1. 启动后 `connector-worker` 能成功登录 Garmin。
2. 连接器按 `4.2` 全量清单执行采集并写入 Raw（无权限/无数据项记录为 `no_data`）。
3. 重复执行同一轮采集不会产生重复脏数据（幂等生效）。
4. 同一天数据变化可形成新快照（external_id 变化）。

### 8.2 数据验收 SQL（示例）
```sql
-- 最近 24 小时 Garmin 入库量
select count(*)
from raw.raw_event
where source_id = 'garmin_connect_health'
  and ingested_at >= now() - interval '24 hours';

-- 按 metric_type 查看入库情况
select
  payload_json ->> 'metric_type' as metric_type,
  count(*) as cnt,
  min(occurred_at) as min_occurred_at,
  max(occurred_at) as max_occurred_at
from raw.raw_event
where source_id = 'garmin_connect_health'
group by 1
order by 1;
```

### 8.3 稳定性验收
- 模拟一次 API 失败（5xx）后，连接器可自动重试并恢复。
- `/v1/health/connector` 在成功/失败后状态正确更新。
- 不出现敏感字段明文日志。

---

## 9. 开发任务拆分建议

### 9.1 后端研发
1. 新增 `connector-health` ingest schema 与 route。
2. 补充请求字段校验与错误码映射。
3. 保持旧接口兼容并回归通过。

### 9.2 连接器研发
1. 集成 `python-garminconnect` 登录与拉取。
2. 实现 metric 拉取、payload 组装、external_id 生成。
3. 实现调度、重试、异常分类、健康状态更新。

### 9.3 数据研发
1. 定义/确认 Raw payload 字段口径与命名。
2. 补充数据质量检查 SQL（Raw 层）。
3. 为后续 `domain_health` 预留字段映射说明。

### 9.4 测试
1. 接口契约测试（成功、幂等、非法参数）。
2. 连接器集成测试（登录、拉取、重试）。
3. 安全检查（日志脱敏、配置合规）。

---

## 10. 风险与应对

| 风险 | 说明 | 应对 |
|---|---|---|
| Garmin 非官方接口变更 | `python-garminconnect` 依赖上游网页接口 | 固定依赖版本 + 异常告警 + 降级到最小数据集 |
| 429/频控 | 拉取过于频繁可能触发限制 | 1小时调度 + 指数退避 + 限制回填窗口 |
| MFA/二次验证 | 首次登录可能需验证码 | 设计人工初始化流程并缓存 token |
| 时区错位 | 数据日期与 UTC 映射偏移 | 强制 `metric_date + timezone` 入 payload |
| 凭据泄露 | 密码/token 泄漏风险 | 环境变量注入 + 日志脱敏 + 禁止明文入库 |

---

## 11. 交付物清单（v0.3.0）

1. 产品文档：`docs/product/product_v0.3.0.md`（本文）。
2. API 变更实现（新增 health ingest endpoint）。
3. Garmin 连接器实现（可运行容器）。
4. 配置模板更新（`infra/docker/.env.example` 新增 Garmin 变量）。
5. 验收脚本更新（新增/补充 Garmin Raw 验证步骤）。

---

## 12. 已确认项

1. 本项目统一时区：`Asia/Shanghai`。
2. `v0.3.0` 范围仅到 Raw，不要求同步产出 `domain_health` MVP。
3. `v0.3.0` 采集范围为 4.2 清单中的全部数据集。
4. 开发环境 `GARMIN_BACKFILL_DAYS=10`。
5. 本版本已于 `2026-02-26` 完成验收，历史回填按设备启用日期从 `2024-05-10` 执行过一次。

---

## 13. 参考资料
- 项目框架文档：`docs/frame/frame_v1.0.md`
- 产品基线文档：`docs/product/product_v0.1.0.md`、`docs/product/product_v0.2.0.md`
- API 文档：`docs/api/api_v0.1.0.md`、`docs/api/api_v0.3.0.md`
- 启动与验收文档：`docs/run/交付物启动与验收说明_v0.3.0.md`
- Garmin SDK 参考：
  - [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
  - [python-garminconnect README](https://github.com/cyberjunky/python-garminconnect/blob/master/README.md)
