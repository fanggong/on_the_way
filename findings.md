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
