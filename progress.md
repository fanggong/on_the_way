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
