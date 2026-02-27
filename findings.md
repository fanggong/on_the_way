# Findings & Decisions

## Requirements
- v0.1.0 must validate end-to-end: ingest -> raw -> canonical -> domain -> mart -> serving.
- `poc_signal` is independent from the 8 formal systems.
- iOS app is mandatory and must support at least manual ingest to Raw plus one query page.
- A non-client connector source is mandatory (5-minute default cadence).
- API minimum endpoint set and unified error/response shape are required.
- Local one-command Docker deploy is required with `postgres:17.0`.
- dbt layering and quality checks are required.
- Annotation must affect domain/mart results.
- OpenMetadata local runtime and lineage visibility are required.

## Current Findings
- End-to-end runtime validation now passes (`verify_v0_1_0.sh` exit 0).
- OpenMetadata ingestion now succeeds with JWT-authenticated CLI flow.
- Full RN native project exists under `apps/ios` with Xcode project + Podfile + native entry files.
- Product constraints for iOS form factor and end-to-end pipeline are implemented.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Use FastAPI + SQLAlchemy service and explicit SQL for idempotent raw ingest | Keeps behavior deterministic and auditable for v0.1.0. |
| Keep dbt as single transformation engine for canonical/domain/mart | Enforces architecture boundary and lineage consistency. |
| Use OpenMetadata API login in scripts to fetch JWT automatically | Avoids manual token handling and resolves 401 on search/ingestion checks. |
| Use `dbtConfigType: local` for dbt metadata ingestion | Matches OpenMetadata 1.11 ingestion schema requirements. |
| Generate RN native scaffold via official CLI and then overlay business app code | Fastest path to production-like native project structure with minimal risk. |

## Issues Encountered and Resolution
| Issue | Resolution |
|-------|------------|
| Docker pull/network instability in environment | Added mirror/proxy configuration and retried with working network path. |
| API ingest failed with SQL syntax error near `:request_id::uuid` | Changed to `cast(:request_id as uuid)` in both insert statements. |
| OpenMetadata container reported unhealthy | Replaced healthcheck command with bash TCP probe (`/dev/tcp`). |
| OpenMetadata ingestion config rejected `authProvider: no-auth` | Switched to `authProvider: openmetadata` and injected JWT token. |
| dbt ingestion config failed schema validation | Added `dbtConfigType: local` in `dbt_ingestion.yml`. |
| Initial app only had RN logic skeleton without native project files | Integrated full RN project scaffold into `apps/ios`. |

## Risks / Follow-up
- iOS app runtime on local simulator/real device should still be validated on the target machine with `npm run pods && npm run ios`.
- OpenMetadata query usage extraction warning remains if `pg_stat_statements` is not enabled; this does not block metadata/lineage ingestion.

## Additional Finding (2026-02-25 iOS startup)
- On this machine, using Bundler with system Ruby for Pods is unreliable due native extension compile issues (`json` gem with Ruby 2.6 + current SDK headers).
- Stable startup path is:
  - Install CocoaPods by Homebrew (`brew install cocoapods`)
  - Run `pod install` directly in `apps/ios/ios`
  - Start Metro and `run-ios`

## Additional Finding (2026-02-26 cleanup)
- API code had confirmed unused items:
  - `services/api/app/core/errors.py::AppError.as_response`
  - `services/api/app/services/query_service.py::update_connector_health`
  - `services/api/app/schemas/query.py` (entire file)
- Workspace contained generated/local artifacts not required for delivery:
  - `apps/ios/node_modules`, `apps/ios/ios/Pods`, `apps/ios/ios/build`, `apps/ios/vendor`, `apps/ios/.bundle`
  - `data/dbt/target`, `data/dbt/logs`, `data/dbt/.user.yml`
- Root `README.md` runbook path was inconsistent and was corrected to `docs/run/交付物启动与验收说明_v0.1.0.md`.
- While `dbt-runner` container keeps running, `data/dbt/target`、`data/dbt/logs`、`data/dbt/.user.yml` may be re-generated automatically; they are now explicitly ignored.

## Resources
- `docs/product/product_v0.1.0.md`
- `docs/frame/frame_v1.0.md`
- `docs/ops/docker_deploy_v0.1.0.md`

---

## v0.2.0 Requirements Snapshot (2026-02-26)

- Scope is UI/UX-only on iOS client home; backend/API/dbt/schema changes are forbidden.
- Home must include:
  - top brand/info area (`On The Way`, subtitle `今日概览`, current date)
  - horizontal nav with 8 topics (default selected: `健康`)
  - topic card area (2 columns x 4 rows)
  - footer note for v0.2.0 UI version
- All 8 topics must be visible/clickable and return unified "coming soon" feedback.
- Client-visible copy must not contain `系统`.
- Visual style must follow MUJI direction with low-saturation neutral palette and high whitespace.
- iOS v0.1.0 manual/query pages should remain accessible for debug only, not as home/main nav.

## v0.2.0 Current Code Reality

- `apps/ios/App.tsx` still uses v0.1.0 dual-tab entry (`手工录入` / `结果查看`) as first screen.
- No `HomeScreen`, `ThemeNavBar`, `ThemeCard`, `tokens`, or `themes` modules exist yet.
- Existing iOS client can already call ingest/query APIs via `src/api/client.ts`; this must remain untouched.

## v0.2.0 Risk Notes

- Product requires "formal" icon assets for 8 topics, but repository currently has no dedicated icon asset package for these topics.
- To avoid dependency churn, default implementation path is coded monochrome icons in RN component form; replaceable if user provides explicit asset pack.

## v0.2.0 Implementation Findings (2026-02-26)

- Implemented modules:
  - `apps/ios/src/theme/tokens.ts`
  - `apps/ios/src/config/themes.ts`
  - `apps/ios/src/components/ThemeNavBar.tsx`
  - `apps/ios/src/components/ThemeCard.tsx`
  - `apps/ios/src/components/ThemeIcon.tsx`
  - `apps/ios/src/screens/HomeScreen.tsx`
- `App.tsx` now defaults to `HomeScreen`; debug pages are still reachable through hidden long-press entry from home brand area.
- Home interactions are UI-only:
  - nav click and card click produce unified "即将开放" feedback
  - no new network request path introduced
- Product copy constraint validated: no `系统` word in app UI source under `apps/ios/src` and `apps/ios/App.tsx`.
- Docs updated for v0.2.0:
  - `apps/ios/README.md`
  - `README.md`
  - `docs/run/交付物启动与验收说明_v0.2.0.md`
  - `docs/product/product_v0.2.0.md` status updated to `已实现（待验收）`

## v0.2.0 Closure Findings (2026-02-26)

- User confirmed v0.2.0 acceptance is completed.
- Documentation status has been unified to accepted/completed:
  - `docs/product/product_v0.2.0.md` -> `已验收（已完成）`
  - `docs/run/交付物启动与验收说明_v0.2.0.md` added closure record section
  - `apps/ios/README.md` and root `README.md` updated with accepted status
- Dead-code cleanup result:
  - No orphan TS/TSX source files found in `apps/ios/src`
  - `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` passed
  - Simplified redundant branch logic in `apps/ios/App.tsx` (removed unnecessary `useMemo` + unreachable title branch in debug path)
- Workspace runtime artifacts were cleaned again:
  - `data/dbt/target`
  - `data/dbt/logs`
  - `data/dbt/.user.yml`

---

## v0.3.0 Discovery Findings (2026-02-26)

- 当前项目状态：
  - `v0.1.0` 已完成 POC 数据链路（`poc_signal`）
  - `v0.2.0` 已验收，仅 iOS 首页 UI/UX 重构
- 服务端现状：
  - Ingest API 仅有 `manual-signal` 与 `connector-signal` 两条写入路径
  - Raw 层统一入库表为 `raw.raw_event`，幂等键为 `source_id + external_id`
  - 请求审计与连接器健康状态已具备（`app.request_audit`、`app.connector_health`）
- 连接器现状：
  - `connector-worker` 当前为伪随机信号生成器，每 300s 写入一次
  - 已具备重试、健康状态回写、API 写入链路
- 数据层现状：
  - dbt 已形成 `raw -> canonical -> domain_poc_signal -> mart_poc_signal`
  - 尚未实现 `domain_health` 实体模型（仅 schema 预留）
- v0.3.0 缺口：
  - 缺少真实健康数据源连接器（Garmin Connect）
  - 缺少健康源数据 raw payload 规范
  - 缺少健康连接器的运行配置规范（凭据、token、回填窗口、速率限制）

## Garmin Reference Findings (python-garminconnect)

- 官方库提供 `Garmin` 客户端，支持账号密码登录 + token 复用（默认 token 目录 `~/.garminconnect`）。
- 认证流程支持 MFA 场景（`return_on_mfa` / `resume_login`）。
- 文档明确可获取多类健康指标，示例与方法包括：
  - `get_user_summary(cdate)`
  - `get_heart_rates(cdate)`
  - `get_sleep_data(cdate)`
  - `get_stress_data(cdate)`
  - `get_body_battery(startdate, enddate)`
  - `get_respiration_data(cdate)` / `get_spo2_data(cdate)`
- 该库基于非官方 Garmin Connect 接口，存在 4xx/429 风险，需要在产品方案中显式定义重试、降级与告警策略。

## v0.3.0 Documentation Finalization Findings (2026-02-26)

- 为满足“后端可直接开工”，新增两份执行文档：
  - `docs/api/api_v0.3.0.md`（新增 endpoint 契约、字段约束、幂等规则）
  - `docs/run/交付物启动与验收说明_v0.3.0.md`（启动步骤、联调检查、SQL 验收、回归清单）
- `docs/product/product_v0.3.0.md` 已消除关键歧义：
  - 数据集范围固定为全量清单（用户确认）
  - 开发环境回填固定 `10` 天（用户确认）
  - SDK 方法名不作为产品契约，改为“metric_type 契约 + 映射表实现约束”
- `README.md` 已加入 v0.3.0 文档入口，方便团队检索。
- `infra/docker/.env.example` 已补齐 Garmin 相关变量，减少研发启动时的隐性配置缺口。

## v0.3.0 Implementation Gap Findings (2026-02-26)

- API 现状：
  - 仅存在 `manual-signal` 与 `connector-signal` 两个 ingest schema/路由。
  - `ingest_service` 已具备可复用的幂等与审计写入能力，可直接承载 `connector-health`。
- Connector 现状：
  - `connector-worker` 仍为随机信号生成器，默认写入 `/v1/ingest/connector-signal`。
  - `config.py` 尚无 Garmin 凭据、时区、窗口、数据集等配置项。
  - 依赖未包含 `garminconnect`。
- Infra 现状：
  - `.env.example` 已有 Garmin 变量，但 `docker-compose.yml` 的 `connector-worker` 还未透传这些变量。
- 结论：
  - `v0.3.0` 文档已齐备，但代码尚未落地。
  - 优先级应为：API 新入口 -> connector Garmin 化 -> compose/env 对齐 -> 回归验证。

## v0.3.0 Implementation Findings (2026-02-26)

- API 已实现：
  - `services/api/app/schemas/ingest.py` 新增：
    - `HealthConnectorPayload`
    - `HealthConnectorIngestRequest`
  - 新增校验：
    - `metric_type` 白名单校验（32 项）
    - `occurred_at` 与 `metric_date + Asia/Shanghai` 对齐校验
  - `services/api/app/api/routes.py` 新增：
    - `POST /v1/ingest/connector-health`
  - 统一复用现有 `ingest_signal` 幂等入库与 `request_audit` 错误审计逻辑
- Connector 已实现：
  - `services/connector-worker/connector/main.py` 从随机信号改为 Garmin 拉取流程：
    - SDK 客户端创建与登录（多签名兼容 + MFA 补码恢复尝试）
    - 32 个 `metric_type` 的方法映射与容错调用
    - 首次回填标记机制（token 目录 `.backfill_done`）
    - `no_data/not_supported` 不中断整轮
    - API 写入重试与 `connector_health` 状态更新
  - `services/connector-worker/connector/config.py` 增加 Garmin 配置解析
  - `services/connector-worker/requirements.txt` 增加 `garminconnect` 依赖
- Infra 与文档对齐：
  - `infra/docker/docker-compose.yml` 已透传 Garmin 相关环境变量并切换默认 ingest 路径
  - `infra/docker/.env.example` 已补齐 `CONNECTOR_INGEST_PATH/CONNECTOR_VERSION/CONNECTOR_REQUEST_TIMEOUT_SECONDS/GARMIN_MFA_CODE`
  - `README.md` 状态已更新为 v0.3.0 已实现待验收
- 校验结果：
  - `python3 -m compileall -q services/api/app services/connector-worker/connector` 通过
  - `HealthConnectorIngestRequest` 示例对象校验通过
  - 宿主环境未安装 FastAPI，无法直接导入 `app.main` 做路由运行时校验；需在容器环境执行联调验收

## v0.3.0 Runtime Verification Findings (2026-02-26)

- 通过 `docker compose` 启动最小服务集后，容器内回归接口验证全部通过：
  - `GET /v1/health/live` -> 200
  - `POST /v1/ingest/manual-signal` -> 200
  - `POST /v1/ingest/connector-signal` -> 200
  - `POST /v1/ingest/connector-health` 首次写入 -> 200 + `idempotent=false`
  - 同 payload 再次写入 -> 200 + `idempotent=true`
  - 错位 `occurred_at` -> 422 `INVALID_ARGUMENT`
- 发现一个环境落地注意点：
  - 现有本地 `infra/docker/.env` 里的历史值会覆盖 compose 默认值（例：`CONNECTOR_INTERVAL_SECONDS=300`），导致 connector 实际运行参数偏离 v0.3.0 默认约定。
  - 已在代码层强制固定 `source_id=garmin_connect_health` 与 `ingest_path=/v1/ingest/connector-health`，避免历史 `.env` 值破坏核心契约；其余运行参数仍建议同步 `.env`。

## v0.3.0 Hotfix Findings (2026-02-26, Timezone & Heart Rate)

- 时区统一修复：
  - PostgreSQL 当前会话与数据库默认时区已切为 `Asia/Shanghai`（验证：`current_setting('TIMEZONE') = Asia/Shanghai`）。
  - `connector-health` 写入的 `occurred_at` 与 payload 字段 `fetched_at` 均改为东8区格式（`+08:00`），不再写 `Z`。
  - `GET /v1/health/live` 返回时间已改为东8区。
- Garmin 心率空值根因：
  - 对账号 `yongchao.fang@outlook.com` 实测：
    - `is_cn=false` 时 `get_heart_rates` 返回结构存在但关键值全部为 `null`。
    - `is_cn=true` 时可返回有效心率（如 `restingHeartRate=71`，`heartRateValues` 长度 `227`）。
  - 因此新增配置 `GARMIN_IS_CN`（默认 `true`），并用于 Garmin 客户端构造。
- 心率数据质量修复：
  - 新增“关键字段有效性判断”，避免把 `heart_rate` 空壳数据写入 Raw（`heartRateValues/restingHeartRate/max/min` 全空视为 `no_data`）。
  - 清理了历史坏数据：删除 `30` 条 `heart_rate` 全空记录。
  - 修复后验证最近 7 天：
    - `heart_rate_rows_last7 = 14`
    - `with_hr_values = 14`
    - `with_resting_hr = 14`
    - 即最近 7 天心率记录关键字段均非空（两轮成功写入）。

## v0.3.0 Final Cleanup Findings (2026-02-26)

- 死代码/无效配置清理：
  - `CONNECTOR_SOURCE_ID` 在 v0.3.0 契约下固定为 `garmin_connect_health`，但 compose/.env.example 中仍暴露可配项，实际不生效。
  - 已从 `infra/docker/docker-compose.yml` 与 `infra/docker/.env.example`（以及本地 `.env`）移除该无效配置，避免误导。
  - `CONNECTOR_INGEST_PATH` 之前存在于 compose 但代码未读取，属于“配置存在但无效”；已改为 `config.py` 正式读取该环境变量。
- 文档终版对齐：
  - `docs/product/product_v0.3.0.md` 状态改为“已验收”，并补充一次性全量回填操作说明。
  - `docs/api/api_v0.3.0.md` 与 `docs/product/product_v0.3.0.md` 的时间样例统一为 `Asia/Shanghai` 偏移格式（`+08:00`），移除“转 UTC”表述。
  - `docs/run/交付物启动与验收说明_v0.3.0.md` 补充 `GARMIN_IS_CN`，新增历史全量回填操作步骤与回填标记说明。

## v0.3.1 Discovery Findings (2026-02-26)

- 版本现状：
  - `v0.3.0` 已验收，健康系统仅完成 Raw 入库（`garmin_connect_health -> raw.raw_event`）。
  - `v0.3.1` 目标是补齐健康链路到 `canonical` 与 `mart`，并完善注释治理。
- 数据模型现状：
  - `data/dbt` 仅存在 `poc_signal` 领域链路（`raw_to_canonical -> domain_poc_signal -> mart_poc_signal`）。
  - `canonical.event` 当前固定 `event_type='signal_event'`，尚未区分健康事件类型。
  - 数据库已预留 `domain_health` schema，但暂无 dbt 模型落地。
- 元数据治理现状：
  - `dbt_ingestion.yml` 已开启 `dbtUpdateDescriptions: true`，可同步 dbt 描述到 OpenMetadata。
  - 当前模型 `schema.yml` 基本无 description，导致 OpenMetadata 字段语义不完整。
  - `postgres_ingestion.yml` schema 白名单仅含 `raw/canonical/domain_poc_signal/mart_poc_signal/annotation`，尚未覆盖 `domain_health` 和未来 `mart_health`。
- 注释落地现状：
  - `services/api/app/db/init_db.py` 中表和字段未设置 `COMMENT ON`，数据库原生元数据描述缺失。
  - 若只做 dbt description，不会覆盖 Raw/App/Annotation 这类非 dbt 管理表的注释需求。
- v0.3.1 文档编写约束：
  - 必须同时定义“dbt description + PostgreSQL COMMENT + OpenMetadata ingestion 范围更新”的组合方案，才能满足“所有表和字段在 OpenMetadata 可查看注释”。
  - Mart 层结构仍存在产品决策空间，文档需附带待确认问题并给默认假设，避免阻塞数据开发启动。

## v0.3.1 Product Doc Decisions (2026-02-26)

- 已输出 `docs/product/product_v0.3.1.md`，并给出可开工默认方案：
  - Canonical：`health_event` + `health_metric_daily`（长表标准化）
  - Mart：`metric_daily_summary`（长表汇总）+ `daily_overview`（宽表总览）
- 注释治理采用“双轨并行”：
  - dbt 模型通过 `schema.yml description` + `persist_docs` 落注释
  - 非 dbt 表通过 `COMMENT ON TABLE/COLUMN` 落注释
- OpenMetadata 可见性依赖以下同时满足：
  - Postgres ingestion schema 白名单覆盖 `app`、`mart_health`（及保留的 `domain_health`）
  - dbt ingestion 保持 `dbtUpdateDescriptions: true`
- Mart 未决策项已在文档中显式列出，并设置默认执行假设，避免阻塞研发启动。

## v0.3.1 Implementation Gap Findings (2026-02-27)

- API 仍存在完整 POC 能力：
  - `POST /v1/ingest/manual-signal`
  - `POST /v1/ingest/connector-signal`
  - `GET /v1/poc/signals`
  - `GET /v1/poc/daily-summary`
- annotation 仍强绑定 `signal_event`：
  - `services/api/app/schemas/annotation.py` 仅允许 `target_type=signal_event`
  - `annotation_service` 仅校验 `domain_poc_signal.signal_event`
- dbt 仍是 v0.1.0 POC 链路：
  - 仅有 `raw_to_canonical -> canonical_to_domain_poc_signal -> domain_poc_signal_to_mart`
  - 不存在 `health_event/health_metric_daily/health_activity_event` 与 `mart_health` 模型
  - `dbt_project.yml` 未启用 `persist_docs`
- iOS 仍含 POC 调试能力：
  - 首页长按进入 debug
  - `ManualInputScreen` + `DailySummaryScreen`
  - `src/api/client.ts` 仍调用 `manual-signal` 与 `poc/daily-summary`
- OpenMetadata ingestion 仍采集 POC schema：
  - `postgres_ingestion.yml` 包含 `domain_poc_signal/mart_poc_signal`
  - 未包含 `mart_health` 与 `app`
- DB 初始化脚本仍创建 POC schema 且缺少 COMMENT：
  - `init_db.py` 仍创建 `domain_poc_signal` / `mart_poc_signal`
  - `raw/annotation/app` 表字段未落 `COMMENT ON`

## v0.3.1 Implementation Decisions (2026-02-27)

- 默认保留 annotation 能力，但从 `signal_event` 切换到健康对象：
  - `health_event`
  - `health_activity_event`
- POC 退役将通过“代码删除 + 启动时幂等清理 SQL”同时落地：
  - 删除 API/dbt/iOS POC 代码
  - 在 init SQL 中执行 POC 历史数据删除与 schema drop
- health Canonical 采用两层策略：
  - `health_event` 保留 1:1 Raw 追溯
  - `health_metric_daily` 通过 JSON 拆解产出标准化明细并补质量标记
- 活动主题采用实体明细 + 日聚合：
  - `canonical.health_activity_event`
  - `mart_health.activity_topic_daily`

## v0.3.1 Implementation Findings (2026-02-27)

- dbt 已完成 v0.3.1 健康链路替换：
  - 新增 `canonical`：
    - `stg_raw__health_event`
    - `health_event`
    - `health_metric_daily`
    - `health_activity_event`
  - 新增 `mart_health`：
    - `metric_daily_summary`
    - `daily_overview`
    - `activity_topic_daily`
  - 删除 POC 模型与测试（`domain_poc_signal` / `mart_poc_signal`）。
- API 已完成 POC 退役与健康化：
  - 删除 `manual-signal` / `connector-signal` / `/v1/poc/*` 路由。
  - 保留 `connector-health`、`annotation`、health endpoints。
  - annotation 目标切换为 `health_event` / `health_activity_event`。
- DB 初始化脚本已完成：
  - POC schema drop（`domain_poc_signal` / `mart_poc_signal`）。
  - POC 历史数据清理（raw/audit/annotation）。
  - `raw/annotation/app` 表字段 COMMENT 补齐。
- iOS 已完成 POC 调试退役：
  - 删除调试入口、手工录入页、结果查询页及相关客户端 API/types/utils。
  - 首页保持 v0.2.0 主题入口能力。
- OpenMetadata 已更新采集白名单：
  - 保留 `raw/canonical/annotation/app`
  - 新增 `mart_health`
  - 移除 `domain_poc_signal/mart_poc_signal`

## v0.3.1 Verification Findings (2026-02-27)

- 静态检查：
  - `python3 -m compileall -q services/api/app services/connector-worker/connector` 通过。
  - `bash -n scripts/dev/verify_v0_3_1.sh` 通过。
  - `apps/ios`：`npx tsc --noEmit`、`npm run lint`、`npm test -- --watch=false` 通过。
- dbt 验证：
  - `docker compose ... run --rm dbt-runner dbt parse --target dev` 通过。
  - `docker compose ... run --rm dbt-runner dbt build --target dev` 通过（`PASS=69`）。
- 端到端验收：
  - `bash scripts/dev/run_openmetadata_ingestion.sh` 通过。
  - `bash scripts/dev/verify_v0_3_1.sh` 通过（含 POC 退役接口 404 校验、POC schema/data 清理校验、OpenMetadata `metric_daily_summary` 可见性校验）。

## v0.3.1 Bugfix Notes (2026-02-27)

- 发现并修复一次启动失败：
  - 现象：API 启动时 `alter table annotation.annotation alter column target_id type text` 报错，提示被 `domain_poc_signal.signal_event` 视图依赖。
  - 根因：在 drop POC schema 之前执行了 `alter column`。
  - 修复：将 `drop schema if exists mart_poc_signal/domain_poc_signal` 提前到 `alter column` 之前执行。

## v0.3.1 Rebaseline Findings (2026-02-27)

- 产品文档已从 `raw -> canonical -> mart_health` 调整为强制四层：`raw -> canonical -> domain_health -> mart`。
- 旧实现中的 `canonical_to_mart_health` 目录与 `mart_health.*` 目标表不再满足新版要求。
- 已完成重构：
  - dbt 目录改为 `canonical_to_domain_health` 与 `domain_health_to_mart`
  - 新增 `domain_health.health_metric_daily_fact` / `domain_health.health_activity_event_fact`
  - Mart 统一为 `mart.health_metric_daily_summary` / `mart.health_daily_overview` / `mart.health_activity_topic_daily`
- OpenMetadata Postgres ingestion 白名单已切换为：`raw/canonical/domain_health/mart/annotation/app`。
- `verify_v0_3_1.sh` 已更新并通过，覆盖 Domain 与 Mart 新对象。
- 为避免旧对象残留干扰，数据库初始化加入 `drop schema if exists mart_health cascade` 作为迁移清理步骤。

## Activity Parsing Bug Fix (2026-02-27)

- 用户反馈确认两点：
  1. `activity_type` 不应做人为归类，需沿用 Garmin 原始命名。
  2. `mart` 活动聚合出现缺失（`duration_seconds_sum` 等应有值字段为空）。

### Root Cause
- `int_canonical__health_activity_event.sql` 中数值提取大量依赖正则匹配；在 dbt 实际落表执行上下文下，关键字段（`duration/distance/calories/averageHR/maxHR`）被批量解析为 `null`。
- 下游 Domain/Mart 继承了这些空值，导致 `mart.health_activity_topic_daily` 中关键聚合字段缺失。
- `training_load` 还存在字段名偏差：Garmin 原始字段为 `activityTrainingLoad`，而模型只解析了 `trainingLoad`。

### Fix
- Canonical 活动模型改为使用 `pg_input_is_valid(..., 'numeric')` 做数值可解析判断，替代原正则判断。
- `activity_type` 改为直接使用 Garmin 原始类型值（如 `road_biking`、`indoor_cycling`），移除人为映射逻辑。
- `training_load` 增加对 `activityTrainingLoad` 的解析。
- Mart 活动聚合：
  - 移除对固定活动类型枚举的过滤。
  - 对 `duration_seconds_sum/distance_meters_sum/calories_kcal_sum/elevation_gain_meters_sum` 增加 `coalesce(sum(...),0)`。
- 模型测试与文档同步：去除 `activity_type` 固定枚举约束，更新 run/product 文档口径。

### Data Quality Verification
- Canonical `health_activity_event`（98行）关键字段空值：
  - `duration_seconds/distance_meters/calories_kcal/avg_heart_rate_bpm/max_heart_rate_bpm/training_load` 均为 `0` 空值。
  - `elevation_gain_meters` 空值 `49`（对应部分活动源数据缺失该字段）。
- Mart `health_activity_topic_daily`（82行）关键聚合字段空值：
  - `duration_seconds_sum/distance_meters_sum/calories_kcal_sum/avg_heart_rate_bpm_avg/max_heart_rate_bpm_max/training_load_sum` 均为 `0` 空值。
  - `avg_power_watts_avg/max_power_watts_max` 仍为空（源数据无 `averagePower/maxPower` 字段）。
  - `max_speed_mps_max` 部分为空（源数据仅 48/98 条包含 `maxSpeed`）。

## OpenMetadata Legacy Metadata Cleanup (2026-02-27)

### Symptom
- OpenMetadata 中仍可检索到退役对象：
  - `otw_postgres.otw_dev.domain_poc_signal.signal_event`
  - `otw_postgres.otw_dev.mart_poc_signal.signal_daily_summary`
  - `otw_postgres.otw_dev.mart_health.*`
- PostgreSQL 实体层已无对应 schema（仅剩 `mart`），说明属于 OpenMetadata 历史元数据残留。

### Root Cause
- `infra/docker/openmetadata/ingestion/postgres_ingestion.yml` 未开启 `markDeletedTables/markDeletedSchemas`，导致源端已删除对象未自动标记删除。
- OpenMetadata Search 会返回 `deleted=true` 的历史实体；仅做 soft-delete 时用户仍可能“看见”这些残留。

### Fix
- 在 Postgres ingestion 配置中启用：
  - `markDeletedTables: true`
  - `markDeletedSchemas: true`
- 增强 `scripts/dev/run_openmetadata_ingestion.sh`：
  - ingestion 完成后新增 `[4/4]` 步骤，对 `domain_poc_signal`、`mart_poc_signal`、`mart_health` 相关 `table/databaseSchema` 执行 OpenMetadata API `hardDelete=true&recursive=true`。
  - 清理逻辑做了幂等处理：删除遇到 404 视为“已删除”，不会导致脚本失败。
- 增强 `scripts/dev/verify_v0_3_1.sh`：
  - OpenMetadata 可见性校验改为精确匹配 `otw_postgres.otw_dev.mart.health_metric_daily_summary`。
  - 新增 `openmetadata legacy metadata removed` 校验，强制检查上述遗留关键字不再出现在实体 FQN。

### Validation
- `bash scripts/dev/run_openmetadata_ingestion.sh`：通过。
- `bash scripts/dev/verify_v0_3_1.sh`：通过，新增检查项显示 `[PASS] openmetadata legacy metadata removed`。
- OpenMetadata API 复核：
  - `q=domain_poc_signal` -> `hits 0`
  - `q=mart_poc_signal` -> `hits 0`
  - FQN 严格过滤（`poc_signal`/`.mart_health.`）-> `legacy_fqn_hits 0`

## v0.3.1 Closure Findings (2026-02-27)

### Dead Code Cleanup
- API 配置对象中存在确认未使用字段：
  - `Settings.env`
  - `Settings.api_port`
- 以上字段已从 `services/api/app/core/config.py` 删除，避免保留无调用配置路径。
- 复核结果：
  - `python3 -m compileall -q services/api/app services/connector-worker/connector` 通过
  - `apps/ios` `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过

### Documentation Finalization
- v0.3.1 文档状态统一更新为 `已验收（已完成）`：
  - `README.md`
  - `docs/product/product_v0.3.1.md`
  - `docs/api/api_v0.3.1.md`
  - `docs/run/交付物启动与验收说明_v0.3.1.md`
  - `apps/ios/README.md`
  - `services/api/README.md`
- 运行手册补充了收尾记录与 OpenMetadata 遗留元数据“无残留”验收结论。

### Final Verification
- `bash scripts/dev/verify_v0_3_1.sh` 通过（含 OpenMetadata legacy metadata removed 检查项）。
