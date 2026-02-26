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
