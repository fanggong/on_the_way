# On The Way 产品文档 v0.1.0

版本: `v0.1.0`  
日期: `2026-02-25`  
状态: `已确认（v0.1.0基线）`  
面向角色: 产品、iOS客户端研发、服务端研发、数据研发、数据治理/AI

---

## 1. 版本定位与硬约束

### 1.1 v0.1.0 目标
- 验证统一架构可行性，确保“接入 -> Raw -> Canonical -> Domain -> Mart -> Serving -> 客户端/分析”全链路可运行。
- 完成交付物框架，不实现 8 个正式系统的业务细节。
- 通过 1 个独立 POC 系统验证技术与流程闭环。

### 1.2 已确认硬约束
- POC 系统独立于健康/时间/收入/财务/能力/关系/生活/保障 8 个系统。
- 客户端形态必须是 iOS App。
- iOS App 至少实现 1 个功能: 手工录入某项数据并写入 Raw 层。
- 本版本采用开放模式，不做登录鉴权和复杂权限。
- POC 系统必须包含 1 个核心非客户端数据源。
- 本地开发环境必须支持 Docker 一键部署。
- 开发库使用 Docker `postgres:17.0`。

### 1.3 非目标
- 不在 v0.1.0 完成 8 个系统的完整领域实现。
- 不在 v0.1.0 实现生产级安全、高可用、多租户。
- 不在 v0.1.0 接入真实复杂外部三方平台（使用可控 POC 数据源验证）。

---

## 2. v0.1.0 交付物定义

### A. 统一数据平台运行体
交付内容:
- 连接器/服务层可写入 Raw。
- dbt 可执行 Raw -> Canonical -> Domain -> Mart。
- Annotation 可参与 Domain 构建。
- Serving Layer 提供可用读取接口。

验收标准:
- iOS 手工录入数据可以进入 Raw 并最终出现在 Mart。
- 非客户端连接器数据可以进入 Raw 并最终出现在 Mart。
- dbt 重跑后结果稳定、链路可追溯。

### B. 独立 POC 系统数据产品
交付内容:
- 独立 POC 系统边界与口径定义。
- POC Domain 模型与 Mart 指标模型。
- 双数据源融合规则（iOS 手工 + 核心连接器）。

验收标准:
- 两条数据路径都可落地并可查询。
- Annotation 改动可反映到 Domain/Mart 结果。

### C. iOS 客户端
交付内容:
- iOS App（RN iOS 目标）具备手工录入页面。
- 成功调用写入 API 并反馈状态。
- 至少一个查询页面展示 Mart 聚合结果。

验收标准:
- 本地 iOS 模拟器或真机可完成录入并看到回流结果。

### D. 元数据治理资产
交付内容:
- OpenMetadata 本地可运行。
- dbt 文档、模型和血缘导入 OpenMetadata。
- 核心术语可检索（POC 系统、Raw、Canonical、Domain、Mart、Annotation）。

验收标准:
- 可在 OpenMetadata 查看跨层血缘。

### E. 文档与规范
交付内容:
- 本文档。
- POC 系统专项说明。
- API 与数据模型说明。
- Docker 一键部署说明。

验收标准:
- 前后端/数据团队可据文档独立开工。

---

## 3. POC 系统设计（独立于 8 系统）

### 3.1 系统名称与目标
系统名称: `poc_signal`（概念验证系统）  
目标: 用最小真实链路验证架构分层、数据治理、客户端写入、连接器写入、指标消费全部可行。

### 3.2 系统边界
包含:
- 数值型信号事件（Signal Event）。
- 信号来源、时间、标签、备注。
- 手工标注与口径修正。

不包含:
- 8 个正式系统领域语义（健康/时间/收入等）。
- 复杂业务流程和策略引擎。

### 3.3 数据源设计
数据源 1（核心非客户端，必选）:
- `signal_random_connector` 定时任务，每 `5` 分钟生成 1 条数值信号写入 Raw。
- 信号值范围: `0-100`。
- 生成策略: 基于时间片与种子形成可重放伪随机值，便于调试和验算。

数据源 2（客户端）:
- iOS App 手工录入信号数据并写入 Raw。
- 字段最小集: `value`、`occurred_at`、`note`。

### 3.4 数据融合与冲突规则
- 幂等键: `source_id + external_id`。
- 同一来源同一外部 ID 重复写入: 保留最新 `ingested_at`。
- 不同来源同时间戳记录: 不覆盖，作为并行事实保留。
- Annotation 只补充语义，不改写 Raw 原始 payload。

---

## 4. 全链路架构与路径矩阵

```text
iOS App 手工录入 -> API -> Raw
随机数连接器定时写入 -> API/内部写入 -> Raw

Raw -> dbt -> Canonical -> dbt -> Domain(poc_signal) -> dbt -> Mart(poc_signal)

Annotation -> Domain 融合
Domain/Mart -> Serving API -> iOS 查询页 / 分析

dbt docs + lineage -> OpenMetadata
```

### 4.1 必须跑通的路径
- 路径 P1: iOS 手工录入 -> Raw -> Canonical -> Domain -> Mart -> iOS 查询。
- 路径 P2: 随机数连接器 -> Raw -> Canonical -> Domain -> Mart -> API 查询。
- 路径 P3: Annotation 写入 -> Domain 口径变化 -> Mart 结果变化。
- 路径 P4: dbt 文档与血缘 -> OpenMetadata 可见。

---

## 5. 数据模型与 Schema 规划（v0.1.0）

### 5.1 Schema 划分
- `raw` 原始层。
- `canonical` 标准层。
- `domain_poc_signal` POC 领域层。
- `mart_poc_signal` 指标层。
- `annotation` 标注层。
- `app` 应用支撑层。
- `domain_<system>` 预留给未来 8 系统（本版本仅建空 schema 或占位模型）。

### 5.2 核心表（最小集合）
- `raw.raw_event`:
  - `raw_id` `source_id` `external_id` `occurred_at` `payload_json` `ingested_at`
- `canonical.event`:
  - `event_id` `raw_id` `event_type` `occurred_at` `source_id` `attributes_json`
- `domain_poc_signal.signal_event`:
  - `signal_event_id` `event_id` `source_type` `value_num` `occurred_at` `is_valid` `tags_json`
- `annotation.annotation`:
  - `annotation_id` `target_type` `target_id` `label` `value` `created_at`
- `mart_poc_signal.signal_daily_summary`:
  - `stat_date` `event_count` `manual_count` `connector_count` `avg_value` `min_value` `max_value`

### 5.3 可扩展性约束
- Canonical 对象模型保持稳定，不因新增系统变化。
- 每个正式系统未来独立 Domain Schema，互不混表。
- Mart 统一从 Domain 读取，不直接读取 Raw。

---

## 6. 服务端与接口设计（开放模式）

### 6.1 服务端职责
- 提供写入 API、查询 API、连接器调度。
- 管理 Raw 入库幂等、审计日志、错误重试。
- 不承载 Domain/Mart 口径计算（由 dbt 负责）。

### 6.2 最小 API 列表
- `POST /v1/ingest/manual-signal`:
  - 来源: iOS App。
  - 作用: 写入 Raw。
- `POST /v1/ingest/connector-signal`:
  - 来源: 随机数连接器。
  - 作用: 写入 Raw。
- `POST /v1/annotation`:
  - 作用: 写入标注。
- `GET /v1/poc/signals`:
  - 作用: 查询 Domain 明细。
- `GET /v1/poc/daily-summary`:
  - 作用: 查询 Mart 聚合。
- `GET /v1/health/connector`:
  - 作用: 查看连接器任务状态。

### 6.3 开放模式约束
- 无用户鉴权。
- 仅本地网络开放端口。
- 保留结构化审计字段（`source_id`、`request_id`、`created_at`）以便未来补权限。

### 6.4 API 请求/响应示例（供前后端联调）
`POST /v1/ingest/manual-signal` 请求示例:
```json
{
  "source_id": "ios_manual",
  "external_id": "ios-20260225-000001",
  "occurred_at": "2026-02-25T10:30:00Z",
  "payload": {
    "value": 73.5,
    "note": "manual input from ios"
  }
}
```

`POST /v1/ingest/manual-signal` 成功响应:
```json
{
  "status": "ok",
  "raw_id": "f6b7a3de-7f74-4c5f-a38c-45a1b2a91a42",
  "ingested_at": "2026-02-25T10:30:01Z",
  "idempotent": false
}
```

`POST /v1/ingest/connector-signal` 请求示例:
```json
{
  "source_id": "signal_random_connector",
  "external_id": "connector-20260225-103000",
  "occurred_at": "2026-02-25T10:30:00Z",
  "payload": {
    "value": 41.2,
    "seed": "20260225-1030",
    "generator_version": "v1"
  }
}
```

`POST /v1/annotation` 请求示例:
```json
{
  "target_type": "signal_event",
  "target_id": "d3d5c008-f6b0-4a7a-9f6f-2685dd4be36b",
  "label": "quality_tag",
  "value": "suspect_outlier"
}
```

`GET /v1/poc/daily-summary?date=2026-02-25` 响应示例:
```json
{
  "status": "ok",
  "stat_date": "2026-02-25",
  "event_count": 289,
  "manual_count": 37,
  "connector_count": 252,
  "avg_value": 49.37,
  "min_value": 1.2,
  "max_value": 98.8
}
```

### 6.5 统一响应与错误码约定
- 成功响应: `{"status":"ok", ...}`。
- 失败响应: `{"status":"error","code":"...","message":"...","request_id":"..."}`。
- 错误码最小集合:
  - `INVALID_ARGUMENT`: 参数不合法或字段缺失。
  - `DUPLICATE_IDEMPOTENCY_KEY`: 幂等键重复且 payload 不一致。
  - `RAW_WRITE_FAILED`: Raw 入库失败。
  - `DEPENDENCY_UNAVAILABLE`: 下游组件不可用（如数据库连接失败）。
  - `INTERNAL_ERROR`: 未分类服务端错误。

### 6.6 可观测性与审计字段约定
- 每个写入请求都应记录: `request_id`、`source_id`、`external_id`、`received_at`、`status`。
- API 日志保留最小语义，不记录敏感原文。
- `/v1/health/connector` 返回最近一次执行时间、最近状态、累计成功/失败次数。

---

## 7. iOS 客户端需求（v0.1.0 强制）

### 7.1 客户端形态
- iOS App（React Native 工程，iOS 平台优先，不要求 Android 同步实现）。

### 7.2 最小功能清单
- 页面 F1: 手工录入。
  - 输入: `value`（必填数字）、`occurred_at`（必填时间）、`note`（可选）。
  - 提交后调用 `POST /v1/ingest/manual-signal`。
- 页面 F2: 结果查看。
  - 展示 `GET /v1/poc/daily-summary` 返回的日汇总结果。
- 页面 F3: 状态提示。
  - 提交成功/失败反馈与重试。

### 7.3 客户端验收
- iOS 本地运行成功。
- 手工录入后 Raw 层可查到记录。
- dbt 跑完后 iOS 页面可见聚合结果。

### 7.4 iOS 实现约束（工程可执行）
- iOS 端仅对接 `v1` API 路径。
- 本地环境通过 `ENV` 配置 `API_BASE_URL`，不硬编码地址。
- 录入页字段校验:
  - `value` 仅允许数值，范围 `0-100`。
  - `occurred_at` 不允许晚于当前时间 `+5` 分钟。
  - `external_id` 由客户端生成并持久化，重试时复用。
- 页面状态最小集合: `idle`、`submitting`、`success`、`error`。
- 错误展示至少区分参数错误与服务不可用两类。

---

## 8. 连接器设计（核心非客户端数据源）

### 8.1 连接器名称
- `signal_random_connector`。

### 8.2 调度策略
- 默认每 `5` 分钟执行。
- 每次生成 1 条或 N 条（默认 1 条）信号数据。

### 8.3 可靠性要求
- 失败重试 3 次，指数退避。
- 记录任务执行日志（成功数/失败数/最后执行时间）。
- 生成幂等 `external_id` 防止重复入库。

### 8.4 为什么采用该方案
- 能持续产生非客户端事实流，验证连接器链路与调度链路。
- 数据规则简单、可控、可重放，便于定位分层问题。
- 不依赖外部第三方平台，降低 v0.1.0 集成风险。

---

## 9. 数据转换与治理

### 9.1 dbt 任务边界
- `raw -> canonical`: 标准化映射。
- `canonical -> domain_poc_signal`: 领域化与标注融合。
- `domain_poc_signal -> mart_poc_signal`: 指标聚合。
- 附带数据测试: 唯一性、非空、引用完整性。

### 9.2 OpenMetadata 任务边界
- 采集 Postgres 元数据。
- 导入 dbt 模型文档与 lineage。
- 维护术语词典与表责任归属。

### 9.3 dbt 目录与命名规范
建议目录:
- `models/raw_to_canonical/`
- `models/canonical_to_domain_poc_signal/`
- `models/domain_poc_signal_to_mart/`
- `models/shared/`

模型命名:
- `stg_raw__*`: Raw 清洗与标准化准备模型。
- `int_canonical__*`: Canonical 中间模型。
- `dim_domain_poc_signal__*`: POC 维度模型。
- `fct_domain_poc_signal__*`: POC 事实模型。
- `mart_poc_signal__*`: 指标与聚合模型。

### 9.4 dbt 质量门禁
- `not_null`: 主键、时间字段、来源字段必须非空。
- `unique`: `raw.raw_event` 上 `source_id + external_id` 唯一。
- `relationships`: Domain 必须引用有效 Canonical 记录。
- `accepted_values`: `source_type` 限定 `manual` 或 `connector`。
- 门禁策略: `dbt build` 任一测试失败即视为链路未通过。

### 9.5 dbt 执行命令约定
- 全量构建: `dbt build --target dev`。
- 仅跑 POC 领域链路: `dbt build --select canonical+domain_poc_signal+mart_poc_signal --target dev`。
- 生成文档: `dbt docs generate --target dev`。
- 产出要求: 构建日志、测试报告、manifest 与 run_results 可用于 OpenMetadata 导入。

---

## 10. Docker 一键部署方案

### 10.1 一键目标
- 在项目根目录执行 `docker compose up -d` 后，基础服务全部可用。
- 执行一次 `dbt build` 后，链路数据可查询。

### 10.2 建议容器清单
- `postgres` 使用 `postgres:17.0`。
- `api-service` Python API。
- `connector-worker` 定时随机数连接器。
- `dbt-runner` 执行建模与测试。
- `openmetadata` 及其官方依赖容器。
- `ios-app` 不容器化，使用本机 Xcode/RN 运行。

### 10.3 启动顺序
1. 启动 Postgres 和 OpenMetadata 依赖。
2. 启动 API 与连接器。
3. 导入种子数据并执行 dbt。
4. 启动 iOS App，执行手工录入。
5. 校验 P1-P4 四条路径。

### 10.4 容器依赖关系（实现 compose 时必须体现）
- `api-service` 依赖 `postgres`。
- `connector-worker` 依赖 `api-service` 与 `postgres`。
- `dbt-runner` 依赖 `postgres`。
- `openmetadata` 依赖其官方依赖服务和 `postgres` 元数据连接可达。

### 10.5 健康检查与启动就绪标准
- `postgres`: `pg_isready` 返回成功。
- `api-service`: `GET /v1/health/live` 返回 `200`。
- `connector-worker`: `GET /v1/health/connector` 可返回最近执行状态。
- `dbt-runner`: 最近一次 `dbt build` 状态为成功。
- `openmetadata`: UI 与 API 可访问，且可连通业务库。

### 10.6 一键验证脚本目标
- 脚本名称建议: `scripts/dev/verify_v0_1_0.sh`。
- 必须检查:
  - 容器运行状态。
  - P1/P2 两条写入路径。
  - Domain/Mart 是否产生数据。
  - OpenMetadata 是否可见 lineage。
- 脚本退出码:
  - `0` 表示全部通过。
  - 非 `0` 表示存在未通过检查项。

---

## 11. 版本矩阵（已确认）

- PostgreSQL: `17.0`（已强制）。
- Python: `3.12`。
- FastAPI: `0.115.x`。
- SQLAlchemy: `2.0.x`。
- dbt-core: `1.9.x`。
- dbt-postgres: `1.9.x`。
- Node.js: `22 LTS`。
- React Native: `0.76.x`（iOS 目标）。
- Xcode: `16.x`。
- OpenMetadata: `latest stable`（官方 Latest Release 为 `1.11.10`，发布时间 `2026-02-18`；实施时使用官方最新稳定补丁版本）。

说明:
- 该矩阵优先考虑本地可跑通和生态兼容性。
- OpenMetadata 版本策略为“最新稳定优先”，避免使用实验版或 RC 版本。
- 版本判断依据: OpenMetadata 官方 [All Releases](https://docs.open-metadata.org/latest/releases/all-releases) 与 [Supported Releases](https://docs.open-metadata.org/latest/releases/supported-releases)。

---

## 12. 团队开工清单

### 产品
- 输出 POC 录入页和结果页原型。
- 确认字段文案和校验规则。

### iOS 客户端
- 建立 iOS RN 工程与页面 F1/F2/F3。
- 对接录入 API 和汇总 API。

### 服务端
- 实现 6 个最小 API。
- 实现随机数连接器调度与幂等写入。

### 数据研发
- 完成 4 层 dbt 模型与测试。
- 输出模型说明和口径文档。

### 数据治理/AI
- 配置 OpenMetadata 与 dbt 血缘导入。
- 建立术语与责任归属。

---

## 13. v0.1.0 验收清单

- [ ] `docker compose up -d` 后核心服务健康。
- [ ] iOS 手工录入写入 Raw 成功。
- [ ] 随机数连接器周期写入 Raw 成功。
- [ ] dbt build 成功，Domain/Mart 有数据。
- [ ] iOS 页面可读到 Mart 日聚合。
- [ ] Annotation 可影响 Domain/Mart 结果。
- [ ] OpenMetadata 可查看跨层血缘。

---

## 14. 工程目录建议（便于并行开发）

- `apps/ios/` iOS App 工程。
- `services/api/` API 与写入服务。
- `services/connector-worker/` 定时连接器任务。
- `data/dbt/` dbt 项目。
- `infra/docker/` compose 与环境配置。
- `docs/product/` 产品与接口文档。
- `docs/data/` 模型口径与数据字典。
- `docs/ops/` 本地部署与排障手册。

---

## 15. 联调与提测流程（v0.1.0）

1. 服务端先完成写入 API 与健康检查接口。
2. 数据研发提供最小 dbt 模型并完成一次全链路构建。
3. iOS 对接手工录入接口，打通 P1 路径。
4. 连接器上线后打通 P2 路径。
5. 数据治理接入 OpenMetadata 并确认 lineage 可见。
6. 执行验收清单，全部通过后冻结 v0.1.0 文档。

提测准入:
- API 文档与请求示例齐备。
- `docker compose up -d` 可拉起核心服务。
- `dbt build` 在开发环境稳定通过。
- iOS 手工录入和汇总查询可演示。

---

## 16. 本轮确认结论

1. `poc_signal` 作为 v0.1.0 独立 POC 系统已确认。
2. 随机数连接器默认调度周期为每 `5` 分钟已确认。
3. OpenMetadata 使用最新稳定版本策略已确认（当前基线建议 `1.11.10`）。

---

## 17. API 字段级数据字典（可直接开发）

### 17.1 通用约定
- 时间字段统一使用 `ISO-8601 UTC`，示例: `2026-02-25T10:30:00Z`。
- 所有写入请求必须包含 `source_id`、`external_id`、`occurred_at`。
- 所有响应都包含 `status`，错误响应额外包含 `code`、`message`、`request_id`。

### 17.2 `POST /v1/ingest/manual-signal` 字段定义

| 字段 | 类型 | 必填 | 约束 | 示例 |
|---|---|---|---|---|
| `source_id` | string | 是 | 固定 `ios_manual` | `ios_manual` |
| `external_id` | string | 是 | 长度 `<=64`，客户端重试复用同一值 | `ios-20260225-000001` |
| `occurred_at` | string(datetime) | 是 | `<= now + 5m` | `2026-02-25T10:30:00Z` |
| `payload.value` | number | 是 | `0 <= value <= 100` | `73.5` |
| `payload.note` | string | 否 | 长度 `<=256` | `manual input from ios` |

成功响应字段:

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | 固定 `ok` |
| `raw_id` | string(uuid) | Raw 主键 |
| `ingested_at` | string(datetime) | 入库时间 |
| `idempotent` | boolean | 是否命中幂等写入 |

### 17.3 `POST /v1/ingest/connector-signal` 字段定义

| 字段 | 类型 | 必填 | 约束 | 示例 |
|---|---|---|---|---|
| `source_id` | string | 是 | 固定 `signal_random_connector` | `signal_random_connector` |
| `external_id` | string | 是 | 由连接器生成，需全局唯一 | `connector-20260225-103000` |
| `occurred_at` | string(datetime) | 是 | 连接器执行时刻 | `2026-02-25T10:30:00Z` |
| `payload.value` | number | 是 | `0 <= value <= 100` | `41.2` |
| `payload.seed` | string | 是 | 与时间片绑定，便于可重放 | `20260225-1030` |
| `payload.generator_version` | string | 是 | 生成器版本号 | `v1` |

### 17.4 `POST /v1/annotation` 字段定义

| 字段 | 类型 | 必填 | 约束 | 示例 |
|---|---|---|---|---|
| `target_type` | string | 是 | 固定 `signal_event` | `signal_event` |
| `target_id` | string(uuid) | 是 | 必须存在于 Domain | `d3d5c008-f6b0-4a7a-9f6f-2685dd4be36b` |
| `label` | string | 是 | 长度 `<=64` | `quality_tag` |
| `value` | string | 是 | 长度 `<=128` | `suspect_outlier` |

### 17.5 `GET /v1/poc/daily-summary` 字段定义

请求参数:

| 参数 | 类型 | 必填 | 约束 | 示例 |
|---|---|---|---|---|
| `date` | string(date) | 是 | `YYYY-MM-DD` | `2026-02-25` |

响应字段:

| 字段 | 类型 | 说明 |
|---|---|---|
| `stat_date` | string(date) | 统计日期 |
| `event_count` | integer | 总事件数 |
| `manual_count` | integer | 手工录入事件数 |
| `connector_count` | integer | 连接器事件数 |
| `avg_value` | number | 均值 |
| `min_value` | number | 最小值 |
| `max_value` | number | 最大值 |

---

## 18. dbt 模型 DoD 与验收 SQL

### 18.1 核心模型 DoD

| 模型 | 粒度 | 关键输入 | DoD（完成定义） |
|---|---|---|---|
| `stg_raw__raw_event` | 单条 Raw 记录 | `raw.raw_event` | 字段标准化完成，主时间字段统一为 UTC |
| `int_canonical__event` | 单条标准事件 | `stg_raw__raw_event` | 每条记录有唯一 `event_id`，可回溯到 `raw_id` |
| `fct_domain_poc_signal__signal_event` | 单条 POC 事实 | `int_canonical__event` + `annotation.annotation` | 产出 `source_type/value_num/is_valid`，标注已融合 |
| `mart_poc_signal__signal_daily_summary` | 天级聚合 | `fct_domain_poc_signal__signal_event` | 聚合指标完整，分来源计数正确 |

### 18.2 必跑测试清单
- `unique` 测试: `raw.raw_event(source_id, external_id)`。
- `not_null` 测试: `occurred_at`、`source_id`、`value_num`。
- `relationships` 测试: Domain `event_id` 引用 Canonical `event_id`。
- `accepted_values` 测试: Domain `source_type IN ('manual','connector')`。
- `custom` 测试: Mart `event_count = manual_count + connector_count`。

### 18.3 验收 SQL（开发环境）

1. Raw 最近 24 小时写入量（按来源）:

```sql
select
  source_id,
  count(*) as row_count
from raw.raw_event
where ingested_at >= now() - interval '24 hour'
group by source_id
order by source_id;
```

2. 幂等冲突检查（应返回 0 行）:

```sql
select
  source_id,
  external_id,
  count(*) as dup_count
from raw.raw_event
group by source_id, external_id
having count(*) > 1;
```

3. Canonical 回溯完整性检查（应返回 0 行）:

```sql
select c.event_id
from canonical.event c
left join raw.raw_event r on c.raw_id = r.raw_id
where r.raw_id is null;
```

4. Domain 来源分布检查:

```sql
select
  source_type,
  count(*) as row_count,
  round(avg(value_num)::numeric, 2) as avg_value
from domain_poc_signal.signal_event
group by source_type
order by source_type;
```

5. Mart 指标一致性检查（应返回 0 行）:

```sql
select stat_date
from mart_poc_signal.signal_daily_summary
where event_count <> manual_count + connector_count;
```

6. 标注生效检查（应返回 `annotated_rows > 0`）:

```sql
select count(*) as annotated_rows
from domain_poc_signal.signal_event s
where exists (
  select 1
  from annotation.annotation a
  where a.target_type = 'signal_event'
    and a.target_id = s.signal_event_id
);
```

---

## 19. Docker Compose 草案与环境变量模板

### 19.1 `docker-compose.yml` 草案（最小结构）

```yaml
services:
  postgres:
    image: postgres:17.0
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

  api-service:
    build: ../../services/api
    environment:
      DATABASE_URL: ${DATABASE_URL}
      API_PORT: ${API_PORT}
    ports:
      - "${API_PORT:-8000}:8000"
    depends_on:
      postgres:
        condition: service_healthy

  connector-worker:
    build: ../../services/connector-worker
    environment:
      DATABASE_URL: ${DATABASE_URL}
      CONNECTOR_INTERVAL_SECONDS: ${CONNECTOR_INTERVAL_SECONDS}
    depends_on:
      postgres:
        condition: service_healthy
      api-service:
        condition: service_started

  dbt-runner:
    image: ghcr.io/dbt-labs/dbt-postgres:1.9.latest
    volumes:
      - ../../data/dbt:/usr/app
    working_dir: /usr/app
    command: ["dbt", "build", "--target", "dev"]
    environment:
      DBT_PROFILES_DIR: /usr/app
    depends_on:
      postgres:
        condition: service_healthy

  openmetadata-server:
    image: openmetadata/server:${OPENMETADATA_VERSION}
    env_file:
      - ./openmetadata/.env
    ports:
      - "${OPENMETADATA_PORT:-8585}:8585"
```

约束:
- OpenMetadata 依赖项（如 MySQL、Elasticsearch、Ingestion）使用官方 Compose 组件，不手写简化替代。
- `ios-app` 不进入 Compose，统一由本机 Xcode/RN 启动。

### 19.2 `.env.example` 模板

```env
POSTGRES_USER=otw
POSTGRES_PASSWORD=otw_dev_password
POSTGRES_DB=otw_dev
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://otw:otw_dev_password@postgres:5432/otw_dev
API_PORT=8000

CONNECTOR_INTERVAL_SECONDS=300
CONNECTOR_SOURCE_ID=signal_random_connector

OPENMETADATA_VERSION=1.11.10
OPENMETADATA_PORT=8585
```

### 19.3 本地启动与验证命令

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs -f api-service
bash scripts/dev/verify_v0_1_0.sh
```

### 19.4 提交到开发团队的最终产物清单
- `docs/product/product_v0.1.0.md` 当前文档。
- `infra/docker/docker-compose.yml` 与 `infra/docker/.env.example`。
- `services/api/` 最小 API 工程。
- `services/connector-worker/` 随机数连接器工程。
- `data/dbt/` POC 分层模型与测试。
