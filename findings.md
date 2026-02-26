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
