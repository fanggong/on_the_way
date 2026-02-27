# Progress Log

## Session: 2026-02-25

### Current Status
- **Phase:** 5 - Delivery
- **Started:** 2026-02-25
- **Runtime validation:** Passed

### Actions Taken
- Completed monorepo bootstrap for API / connector / dbt / infra / docs.
- Completed `poc_signal` API, DB bootstrap, annotation flow and serving endpoints.
- Completed connector worker with deterministic random signal generation and retry.
- Completed dbt layering models and tests (`raw -> canonical -> domain -> mart`).
- Added OpenMetadata docker stack and ingestion workflows.
- Added docker mirror/proxy support in compose and Dockerfiles.
- Fixed OpenMetadata runtime issues:
  - MySQL startup option mismatch removed.
  - DB driver/scheme settings corrected.
  - Migration rerun on clean OpenMetadata DB.
  - Healthcheck switched to TCP probe because image has no `curl`.
- Fixed API ingest 500 error caused by SQL parameter cast syntax.
- Updated OpenMetadata ingestion to JWT-authenticated flow and fixed dbt ingestion config schema.
- Generated full RN native project from official RN CLI and merged existing app logic:
  - Added `apps/ios/ios/OnTheWayIOS.xcodeproj`
  - Added `apps/ios/ios/Podfile`
  - Preserved `App.tsx` and `src/` business screens.
- Updated runbook/docs and environment templates.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `bash -n scripts/dev/verify_v0_1_0.sh` | shell script syntax valid | passed | PASS |
| `bash -n scripts/dev/run_openmetadata_ingestion.sh` | shell script syntax valid | passed | PASS |
| `bash scripts/dev/run_openmetadata_ingestion.sh` | Postgres + dbt metadata ingestion success | completed with success summary | PASS |
| `bash scripts/dev/verify_v0_1_0.sh` | Full v0.1.0 checks all pass | all checks PASS, script exit 0 | PASS |
| `docker compose ... ps` | Core services running | postgres/api/connector/dbt/openmetadata all running | PASS |
| RN scaffold check (`apps/ios/ios/*.xcodeproj`, `Podfile`) | Native iOS project present | files present and integrated | PASS |

### Residual Notes
- OpenMetadata Postgres ingestion logs non-fatal warning for `pg_stat_statements` query collection (extension not enabled). Metadata and lineage ingestion still succeeded.

## Session: 2026-02-25 (iOS Startup Support)

### Actions Taken
- Installed CocoaPods via Homebrew (`brew install cocoapods`) because `pod` command was missing.
- Ran `pod install` successfully in `apps/ios/ios`.
- Launched iOS simulator app with `npx react-native run-ios --simulator "iPhone 17"`.
- Started Metro server with elevated permission (`npm start`) and confirmed JS bundle loading.

### Errors & Resolution
| Error | Resolution |
|-------|------------|
| `bundle install` failed (system Ruby 2.6 native extension build for `json` gem) | Bypassed Bundler flow and installed CocoaPods via Homebrew. |
| Metro failed to bind `0.0.0.0:8081` in sandbox (`EPERM`) | Started Metro with elevated permission outside sandbox. |

### Outcome
- iOS app successfully built, installed, launched, and connected to Metro (`Running "OnTheWayIOS"` observed in Metro logs).

## Session: 2026-02-26 (Dead Code & Docs Finalization)

### Actions Taken
- Removed confirmed unused API code:
  - `AppError.as_response` helper
  - `query_service.update_connector_health` (API-side duplicate unused implementation)
  - `services/api/app/schemas/query.py` (unused response schema file)
- Removed empty `services/api/app/models` directory.
- Cleaned generated/local artifacts from workspace:
  - iOS: `node_modules`, `Pods`, `build`, `vendor`, `.bundle`
  - dbt: `target`, `logs`, `.user.yml`
- Updated ignore rules in root `.gitignore` for iOS/dbt generated artifacts.
- Updated iOS startup scripts/docs:
  - `apps/ios/package.json` `pods` script switched to `bundle exec pod install || pod install`.
  - `apps/ios/README.md` and runbook updated to use CocoaPods-first flow.
- Fixed runbook link in root `README.md`.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `python3 -m compileall -q services/api/app services/connector-worker/connector` | Python code compiles after dead code removal | passed | PASS |
| `bash -n scripts/dev/verify_v0_1_0.sh` | verification script syntax valid | passed | PASS |
| `bash -n scripts/dev/run_openmetadata_ingestion.sh` | ingestion script syntax valid | passed | PASS |
| `rg` residual reference check for removed symbols | no remaining references | no output | PASS |

### Residual Notes
- If `dbt-runner` container remains active, `data/dbt/target`、`data/dbt/logs`、`data/dbt/.user.yml` can be auto-generated again; ignore rules are already added.

## Session: 2026-02-26 (v0.2.0 UI/UX Development)

### Current Status
- **Phase:** Completed
- **Started:** 2026-02-26
- **Scope:** iOS home redesign only, no backend/data changes

### Actions Taken
- Read and parsed `docs/product/product_v0.2.0.md` full constraints.
- Verified related baseline docs (`frame/api/runbook`) and iOS app current structure.
- Executed skill-driven workflow:
  - `planning-with-files`
  - `ui-ux-pro-max`
  - `vercel-react-native-skills`
- Collected RN implementation constraints:
  - prefer `Pressable` over touchable components
  - prefer GPU-friendly animation properties (`transform`/`opacity`)
  - ensure safe-area compatible scroll layout
  - avoid JSX falsy `&&` rendering pitfalls in RN
- Rebased planning files to v0.2.0 objective and phase tracking.

### Pending
- None.

### Delivered
- Added MUJI-aligned token system and topic config.
- Added new home UI components and screen:
  - `ThemeNavBar`
  - `ThemeCard`
  - `ThemeIcon`
  - `HomeScreen`
- Switched `App.tsx` first screen to Home.
- Added hidden debug access path:
  - long-press home brand area -> debug pages (`手工录入` / `结果查看`)
- Updated iOS/docs for v0.2.0 run and acceptance flow.
- Bumped iOS package version to `0.2.0`.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `npm run lint` (apps/ios) | RN TS/JS lint passes | passed | PASS |
| `npm test -- --watch=false` (apps/ios) | Jest passes | passed | PASS |
| `npx tsc --noEmit` (apps/ios) | Type check passes | passed | PASS |

### Errors & Resolution
| Error | Resolution |
|-------|------------|
| Jest failed with AsyncStorage native module null | Added AsyncStorage official Jest mock in `__tests__/App.test.tsx`. |
| TypeScript route narrowing warning in `App.tsx` | Removed impossible selected-state comparison in debug-only branch. |
| TypeScript test file missing `jest` type | Imported `jest` from `@jest/globals`. |

## Session: 2026-02-26 (Final Wrap-up)

### Current Status
- **Phase:** Completed
- **Scope:** dead code cleanup + final documentation polish

### Actions Taken
- Performed dead code scan on iOS TS sources:
  - orphan-file scan across `apps/ios/src`
  - strict no-unused check with `npx tsc --noEmit --noUnusedLocals --noUnusedParameters`
- Simplified redundant code in `apps/ios/App.tsx`:
  - removed unnecessary `useMemo`
  - reduced debug title computation to direct branch expression
- Updated version docs to acceptance-complete state:
  - `docs/product/product_v0.2.0.md`
  - `docs/run/交付物启动与验收说明_v0.2.0.md`
  - `apps/ios/README.md`
  - `README.md`
- Cleaned generated dbt runtime artifacts:
  - `data/dbt/target`
  - `data/dbt/logs`
  - `data/dbt/.user.yml`

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` | no unused TS locals/params in iOS app | passed | PASS |
| `npx tsc --noEmit` | iOS type check passes after cleanup | passed | PASS |
| `npm run lint` | iOS lint passes after cleanup | passed | PASS |
| `npm test -- --watch=false` | iOS Jest smoke test passes | passed | PASS |

## Session: 2026-02-26 (v0.3.0 Product Documentation)

### Current Status
- **Phase:** 2 - Document drafting
- **Scope:** 定义健康系统 Garmin 连接器写入 Raw 层的 v0.3.0 产品文档

### Actions Taken
- 已读取现有框架与产品基线文档：
  - `docs/frame/frame_v1.0.md`
  - `docs/product/product_v0.1.0.md`
  - `docs/product/product_v0.2.0.md`
  - `docs/api/api_v0.1.0.md`
  - `docs/run/交付物启动与验收说明_v0.1.0.md`
  - `docs/run/交付物启动与验收说明_v0.2.0.md`
- 已读取关键实现：
  - `services/api/app/api/routes.py`
  - `services/api/app/services/ingest_service.py`
  - `services/connector-worker/connector/main.py`
  - `services/connector-worker/connector/config.py`
  - `services/api/app/db/init_db.py`
  - `data/dbt/models/*`
- 已完成 Garmin 参考方案调研（`python-garminconnect` README / source）。
- 已切换并更新规划文件到 v0.3.0 任务上下文。

### Pending
- 输出 `docs/product/product_v0.3.0.md`
- 文档自检与问题清单确认

### Completion
- 已完成 `docs/product/product_v0.3.0.md` 产出。
- 文档已包含：
  - 当前项目进度与版本边界
  - Garmin 连接器方案（认证/调度/增量/重试）
  - Raw 数据契约与 API 变更点
  - 安全规范、验收 SQL、任务拆分与风险应对
- 保留 3 项待确认产品参数，不阻塞后端启动开发。
- 用户已确认：统一时区 Asia/Shanghai、v0.3.0 仅到 Raw、开发环境回填天数 30（文档已同步更新）。
- 用户确认：v0.3.0 采集 4.2 全量数据集；开发环境首次回填天数调整为 10 天（文档已更新）。

## Session: 2026-02-26 (v0.3.0 Docs Final Check)

### Actions Taken
- 完成 `docs/product/product_v0.3.0.md` 复核与补充：
  - 明确全量采集清单
  - 回填窗口改为开发环境 10 天
  - 新增 SDK 方法映射规则，避免版本方法名耦合
- 新增文档：
  - `docs/api/api_v0.3.0.md`
  - `docs/run/交付物启动与验收说明_v0.3.0.md`
- 更新索引与配置模板：
  - `README.md` 增加 v0.3.0 入口
  - `infra/docker/.env.example` 增加 Garmin 变量

### Verification
- 文档一致性检查通过：product/api/run/README 相互引用完整。
- 敏感信息检查通过：未写入用户提供的真实 Garmin 邮箱/密码。

## Session: 2026-02-26 (v0.3.0 Development Implementation)

### Current Status
- **Phase:** 1 - Gap Review
- **Scope:** 将 v0.3.0 文档方案落地为可运行代码

### Actions Taken
- 复核现有规划文件并重置任务计划到“实现阶段”。
- 完成 API / connector / compose 现状差距审计：
  - API 尚未实现 `/v1/ingest/connector-health`
  - connector 仍为随机信号逻辑
  - compose 尚未注入 Garmin 相关环境变量

### Next
- 开始 API schema 与路由改造（Phase 2）。

### Completion
- API 实现完成：
  - 新增健康 ingest schema（`HealthConnectorPayload` / `HealthConnectorIngestRequest`）
  - 新增路由 `POST /v1/ingest/connector-health`
  - 复用既有 `ingest_signal` + `request_audit` 错误记录链路
- Connector 实现完成：
  - 随机信号逻辑替换为 Garmin 拉取逻辑
  - 新增 32 数据集映射、日期窗口回填、单指标容错、API 重试
  - 新增可选 MFA 恢复码处理（`GARMIN_MFA_CODE`）
- 部署与文档同步：
  - compose 与 `.env.example` 已注入完整 Garmin 变量
  - README 状态更新为 v0.3.0 已实现（待验收）
  - 固化 connector 契约值：`source_id` 与 `ingest_path` 不再受历史 `.env` 覆盖

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `python3 -m compileall -q services/api/app services/connector-worker/connector` | Python 代码语法可编译 | passed | PASS |
| `PYTHONPATH=services/api python3 - <<'PY' ... HealthConnectorIngestRequest.model_validate(...)` | v0.3.0 请求 schema 可成功校验 | passed | PASS |
| `PYTHONPATH=services/connector-worker python3 - <<'PY' ... print(settings...)` | connector 新配置可正常加载 | passed | PASS |

### Errors & Resolution
| Error | Resolution |
|-------|------------|
| 宿主环境缺少 FastAPI，`from app.main import app` 导入失败 | 记录为环境依赖缺失；改用 compile/schema 级校验，完整联调应在 docker compose 环境执行。 |

### Integration Verification (docker compose)
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `docker compose ... up -d --build postgres api-service connector-worker` | v0.3.0 API+connector 服务可启动 | services all running (api healthy) | PASS |
| 容器内 `GET /v1/health/live` | API 存活 | `200` + `status=ok` | PASS |
| 容器内 `POST /v1/ingest/manual-signal` | v0.1.0 手工入口不回归 | `200` + `idempotent=false` | PASS |
| 容器内 `POST /v1/ingest/connector-signal` | v0.1.0 连接器入口不回归 | `200` + `idempotent=false` | PASS |
| 容器内 `POST /v1/ingest/connector-health` (2次同 payload) | v0.3.0 新入口可用且幂等 | 第1次 `idempotent=false`，第2次 `idempotent=true` | PASS |
| 容器内 `POST /v1/ingest/connector-health` (`occurred_at` 错位) | 契约校验生效 | `422 INVALID_ARGUMENT` | PASS |

## Session: 2026-02-26 (Timezone & Heart Rate Hotfix)

### Current Status
- **Phase:** Completed
- **Scope:** 修复时区统一与 Garmin 心率空值问题

### Actions Taken
- 根因排查：
  - 发现 DB 默认时区为 `UTC`，导致 Raw/健康接口时间字段出现 `+00` 输出。
  - 发现 Garmin 账号在 `is_cn=false` 下 `get_heart_rates` 返回结构存在但核心心率字段全空；`is_cn=true` 下可返回有效值。
- 代码修复：
  - 新增 `GARMIN_IS_CN` 配置（默认 `true`），接入 Garmin 客户端初始化逻辑。
  - Garmin 写入时间统一为东8区：
    - `occurred_at` 使用 `+08:00`
    - `payload.fetched_at` 使用 `+08:00`
  - API `connector-health` schema 强制 `occurred_at`/`fetched_at` 使用东8区偏移并校验本地零点对齐。
  - DB 时区统一：
    - API SQLAlchemy 连接强制 `timezone=Asia/Shanghai`
    - connector psycopg 连接强制 `timezone=Asia/Shanghai`
    - init SQL 增加数据库默认时区设置为 `Asia/Shanghai`
  - `GET /v1/health/live` 时间输出改为东8区。
  - 增加 `heart_rate` / `resting_heart_rate` 有效数据判定，避免空壳数据写入。
- 数据修复：
  - 清理历史坏数据：删除 `30` 条 `heart_rate` 关键值全空记录。

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `current_setting('TIMEZONE')` | DB 时区为东8区 | `Asia/Shanghai` | PASS |
| `/v1/health/live` | 返回东8区时间字符串 | `2026-02-26T15:41:22.272705+08:00` | PASS |
| 最近7天 `heart_rate` 数据质量 | 每条有 `heartRateValues` 与 `restingHeartRate` | `14/14` 非空 | PASS |
| `heart_rate` 行时间字段 | `occurred_at` + payload `fetched_at` 均东8区 | `+08:00` | PASS |

### Errors & Resolution
| Error | Resolution |
|-------|------------|
| Docker 命令偶发 `permission denied ... docker.sock` | 通过提权执行容器内 SQL/健康校验命令。 |
| SQL 直接取心率长度时报 `cannot get array length of a scalar` | 增加 `jsonb_typeof` 判型后再计算长度。 |

## Session: 2026-02-26 (Final Cleanup & Docs Polish)

### Current Status
- **Phase:** Completed
- **Scope:** 清理死代码并完成 v0.3.0 终版文档

### Actions Taken
- 代码清理：
  - `services/connector-worker/connector/config.py` 改为读取 `CONNECTOR_INGEST_PATH`，消除“配置有定义但不生效”问题。
  - `infra/docker/docker-compose.yml` / `.env.example` / 本地 `.env` 移除 `CONNECTOR_SOURCE_ID` 无效配置项。
- 文档终版：
  - `README.md` 状态改为 `v0.3.0 Accepted`。
  - `docs/product/product_v0.3.0.md` 更新为已验收口径，并统一东8区时间示例。
  - `docs/api/api_v0.3.0.md` 更新 `occurred_at/fetched_at/ingested_at` 示例为 `+08:00`。
  - `docs/run/交付物启动与验收说明_v0.3.0.md` 增加 `GARMIN_IS_CN` 与一次性全量回填步骤。

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `python -m compileall services/api services/connector-worker` | 改动后 Python 可编译 | passed | PASS |
| `docker compose -f infra/docker/docker-compose.yml config` | compose 配置合法 | `OK` | PASS |

## Session: 2026-02-26 (v0.3.1 Product Documentation Drafting)

### Current Status
- **Phase:** 2 - v0.3.1 scope definition
- **Scope:** 产出健康系统 `raw -> canonical -> mart` 与注释治理的产品文档

### Actions Taken
- 已完成输入基线梳理：
  - `docs/product/product_v0.3.0.md`
  - `docs/api/api_v0.3.0.md`
  - `docs/run/交付物启动与验收说明_v0.3.0.md`
  - `docs/frame/frame_v1.0.md`
- 已完成现状代码盘点：
  - `services/api/app/db/init_db.py`
  - `data/dbt/models/*`
  - `infra/docker/openmetadata/ingestion/*.yml`
  - `scripts/dev/run_openmetadata_ingestion.sh`
- 已识别 v0.3.1 关键缺口：
  - health 仅到 Raw，尚无 canonical/domain/mart health 模型
  - dbt 模型缺 description，OpenMetadata 字段语义不可读
  - Postgres ingestion 白名单未纳入 health 相关 schema
  - 数据库表字段未落 COMMENT，非 dbt 表注释不可见

### Next
- 输出 `docs/product/product_v0.3.1.md`：
  - 明确 ETL 目标模型、开发拆分、DoD、验收 SQL
  - 明确 OpenMetadata 注释可见性的实施标准与验收口径
  - 补充 Mart 结构待确认问题并给默认方案

### Completion
- 已完成 `docs/product/product_v0.3.1.md` 产出，内容包含：
  - v0.3.1 版本范围、边界、当前进度
  - health `raw -> canonical -> mart_health` 目标模型与字段口径
  - dbt 模型目录、配置改造与测试清单
  - 注释治理（dbt description + DB COMMENT）与 OpenMetadata ingestion 要求
  - 可执行验收 SQL 与 DoD
  - Mart 结构待确认问题及默认执行假设

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| 文档结构自检（章节/范围/路径） | 覆盖用户要求的 ETL + 注释治理 | 已覆盖且路径正确 | PASS |
| 代码/运行命令执行 | 本次任务仅文档输出，不改代码 | 未执行 | N/A |

## Session: 2026-02-27 (v0.3.1 Full Implementation)

### Current Status
- **Phase:** 2 - Data layer implementation
- **Scope:** 按 `docs/product/product_v0.3.1.md` 完成代码落地（ETL + POC退役 + 注释治理）

### Actions Taken
- 启用 `planning-with-files` 流程并完成会话恢复检查。
- 完成全仓盘点（API/dbt/iOS/OpenMetadata/init SQL/脚本/文档）。
- 对齐 v0.3.1 与现状差距，锁定实施计划与默认假设：
  - annotation 保留但切换到 health 目标对象
  - POC 代码与数据对象执行强退役
- 已重写 `task_plan.md` 为本轮实施计划（5个阶段）。
- 已补充 `findings.md` 本轮 gap 与关键决策记录。

### Next
- 实施 dbt health 模型 + 删除 POC dbt 模型与测试。
- 实施 API/DB/iOS 退役改造。
- 更新 OpenMetadata ingestion 与 v0.3.1 文档。

### Completion
- 已完成 v0.3.1 代码落地：
  - 数据层：health canonical + mart_health 全链路。
  - API 层：POC 路由退役，annotation 目标切换到 health。
  - DB 层：POC schema/data 清理 + COMMENT 治理。
  - iOS 层：移除 POC 调试能力。
  - 元数据层：OpenMetadata schema 白名单调整并重跑 ingestion。
  - 文档层：新增 `api_v0.3.1`、`run_v0.3.1`，更新 `README`、模块 README、`product_v0.3.1` 状态。

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `python3 -m compileall -q services/api/app services/connector-worker/connector` | Python 代码可编译 | passed | PASS |
| `bash -n scripts/dev/verify_v0_3_1.sh` | 验收脚本语法正确 | passed | PASS |
| `cd apps/ios && npx tsc --noEmit` | iOS TS 类型检查通过 | passed | PASS |
| `cd apps/ios && npm run lint` | iOS lint 通过 | passed | PASS |
| `cd apps/ios && npm test -- --watch=false` | iOS Jest 通过 | passed | PASS |
| `docker compose ... run --rm dbt-runner dbt parse --target dev` | dbt 配置可解析 | passed | PASS |
| `docker compose ... run --rm dbt-runner dbt build --target dev` | 新模型与测试通过 | `PASS=69` | PASS |
| `bash scripts/dev/run_openmetadata_ingestion.sh` | 元数据与血缘摄取成功 | completed | PASS |
| `bash scripts/dev/verify_v0_3_1.sh` | v0.3.1 全量验收通过 | passed | PASS |
| `POST /v1/annotation`（`health_event` / `health_activity_event`） | annotation 新目标类型可写入 | 两种 target_type 均 `200` | PASS |

### Errors & Resolution
| Error | Resolution |
|-------|------------|
| API 启动时报 `cannot alter type of a column used by a view or rule` | 先 `drop schema domain_poc_signal/mart_poc_signal`，再执行 `annotation.target_id` 列类型调整。 |
| 初次执行 `verify_v0_3_1.sh` 在沙箱内无法访问 Docker socket | 提权执行并在重建 API + 重跑 OpenMetadata ingestion 后复测通过。 |

## Session: 2026-02-27 (v0.3.1 Docs Rebaseline)

### Current Status
- **Phase:** Completed
- **Trigger:** `docs/product/product_v0.3.1.md` scope changed significantly
- **Outcome:** Re-implemented v0.3.1 to match new four-layer architecture

### Actions Taken
- Reworked dbt model topology:
  - removed `canonical_to_mart_health`
  - added `canonical_to_domain_health` and `domain_health_to_mart`
  - updated tests to target `mart__*` models
- Added new Domain fact models:
  - `fct_domain_health__health_metric_daily_fact`
  - `fct_domain_health__health_activity_event_fact`
- Re-targeted Mart models to unified `mart` schema:
  - `mart__health_metric_daily_summary`
  - `mart__health_daily_overview`
  - `mart__health_activity_topic_daily`
- Updated infra/governance:
  - `dbt_project.yml` schema mappings
  - `init_db.py` schema migration (`mart_health` retirement, `mart` + `domain_health` comments)
  - OpenMetadata Postgres ingestion schema whitelist
- Updated v0.3.1 run/API/README docs to new naming and acceptance SQL.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `docker compose ... dbt build --target dev` | New models compile and tests pass | PASS=87, ERROR=0 | PASS |
| `bash scripts/dev/run_openmetadata_ingestion.sh` | New `mart`/`domain_health` metadata ingested | Completed successfully | PASS |
| `bash scripts/dev/verify_v0_3_1.sh` | Full v0.3.1 acceptance passes | `[DONE] verify_v0_3_1 passed` | PASS |

### Notes
- OpenMetadata ingestion still logs non-blocking `pg_stat_statements` warning; does not affect metadata or lineage ingestion success.

### Additional Closure Updates (2026-02-27)
- Executed DB cleanup: `drop schema if exists mart_health cascade` to enforce unified `mart` schema boundary.
- Hardened `verify_v0_3_1.sh` OpenMetadata check:
  - if `health_metric_daily_summary` is not yet searchable, script auto-runs ingestion refresh once and retries.
- Re-verified full acceptance after cleanup: `[DONE] verify_v0_3_1 passed`.

## Session: 2026-02-27 (Activity Type + Activity Metrics Fix)

### Scope
- Keep Garmin original `activity_type` naming (remove manual category mapping).
- Fix missing activity metrics in mart aggregation (`duration_seconds_sum` and related fields).

### Actions Taken
- Refactored `int_canonical__health_activity_event.sql`:
  - removed manual activity-type mapping to `cycling/running/walking/swimming/other`
  - `activity_type` now directly uses Garmin raw type naming
  - replaced regex-based numeric parsing with `pg_input_is_valid(..., 'numeric')`
  - added `activityTrainingLoad` parsing for `training_load`
- Refactored downstream models:
  - `fct_domain_health__health_activity_event_fact`: removed fixed enum validity constraint
  - `mart__health_activity_topic_daily`: removed fixed enum filter; added non-null-safe sums for key metrics
- Updated tests/docs:
  - removed `activity_type` accepted-values constraints in canonical/domain/mart schema yml
  - added not-null tests for mart key aggregates (`duration_seconds_sum`, `distance_meters_sum`, `calories_kcal_sum`)
  - updated product/run docs to describe raw Garmin activity types

### Validation
| Check | Result |
|------|--------|
| `dbt build --target dev` | PASS=87, ERROR=0 |
| `dbt build --select int_canonical__health_activity_event+` | PASS=30, ERROR=0 |
| `bash scripts/dev/verify_v0_3_1.sh` | `[DONE] verify_v0_3_1 passed` |

### Data Profiling After Fix
- `canonical.health_activity_event`:
  - `duration_seconds/distance_meters/calories_kcal/avg_heart_rate_bpm/max_heart_rate_bpm/training_load`: null=0
  - `elevation_gain_meters`: null=49 (source-level absence)
- `mart.health_activity_topic_daily`:
  - `duration_seconds_sum/distance_meters_sum/calories_kcal_sum/training_load_sum`: null=0
  - `avg_power_watts_avg/max_power_watts_max`: null=82 (source has no corresponding keys)

### Note
- Raw activity types currently observed: `indoor_cycling`, `road_biking`.

## Session: 2026-02-27 (OpenMetadata POC Legacy Metadata Cleanup)

### Scope
- 用户反馈 OpenMetadata 仍存在 POC 相关元数据残留，需要排查根因并彻底清理。

### Actions Taken
- 通过 OpenMetadata API 检索并确认残留对象：
  - `domain_poc_signal.signal_event`
  - `mart_poc_signal.signal_daily_summary`
  - `mart_health.*`
- 交叉验证 PostgreSQL `pg_namespace`：实际仅存在 `mart`，确认问题为元数据残留而非物理表残留。
- 修复采集与清理流程：
  - `postgres_ingestion.yml` 增加 `markDeletedTables/markDeletedSchemas`
  - `run_openmetadata_ingestion.sh` 增加第 `[4/4]` 步：legacy 元数据 hard delete（含 404 幂等处理）
  - `verify_v0_3_1.sh` 增加 OpenMetadata legacy 检查并强化 mart 可见性精确匹配
- 重跑 ingestion 与全量验收。

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `bash scripts/dev/run_openmetadata_ingestion.sh` | ingestion + legacy cleanup succeed | `[DONE] OpenMetadata ingestion complete` | PASS |
| `bash scripts/dev/verify_v0_3_1.sh` | includes OpenMetadata legacy cleanup assertion | `[PASS] openmetadata legacy metadata removed` | PASS |
| OpenMetadata API strict FQN scan | no `poc_signal` / `.mart_health.` entities | `legacy_fqn_hits 0` | PASS |

### Notes
- OpenMetadata 在搜索词层面（如 `mart_health`）会返回语义相关结果；验收已改为 FQN 精确匹配，避免误判。

## Session: 2026-02-27 (v0.3.1 Final Closure)

### Scope
- 用户确认已完成验证，要求执行版本收尾：
  - 清理死代码
  - 最后一次完善版本文档

### Actions Taken
- 死代码清理：
  - 删除 `services/api/app/core/config.py` 未使用字段 `env`、`api_port`。
- 文档定稿：
  - `README.md` 状态改为 v0.3.1 已验收
  - `docs/product/product_v0.3.1.md` 状态改为已验收，并补充 v0.3.1 验收结论
  - `docs/api/api_v0.3.1.md` 增加验收状态
  - `docs/run/交付物启动与验收说明_v0.3.1.md` 增加 OpenMetadata 遗留元数据检查项与收尾记录
  - `apps/ios/README.md`、`services/api/README.md` 同步验收状态
  - `task_plan.md` 增加 Phase 6（Version Closure）并标记完成

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `python3 -m compileall -q services/api/app services/connector-worker/connector` | Python compile passes after cleanup | passed | PASS |
| `cd apps/ios && npx tsc --noEmit --noUnusedLocals --noUnusedParameters` | no unused TS locals/params | passed | PASS |
| `bash scripts/dev/verify_v0_3_1.sh` | full v0.3.1 acceptance remains green | `[DONE] verify_v0_3_1 passed` | PASS |

### Notes
- 首次在沙箱内执行 `verify_v0_3_1.sh` 因 Docker socket 权限受限失败，提权重跑后通过。
