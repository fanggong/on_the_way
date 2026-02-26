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
