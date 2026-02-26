# Task Plan: on_the_way v0.1.0 Implementation

## Goal
Deliver a runnable v0.1.0 baseline for `poc_signal` covering API + connector + dbt + Docker + OpenMetadata + full React Native iOS native project + verification scripts + supporting docs.

## Current Phase
Phase 5

## Phases

### Phase 1: Requirements & Discovery
- [x] Read `docs/product/product_v0.1.0.md`
- [x] Read `docs/frame/frame_v1.0.md`
- [x] Extract mandatory deliverables and constraints into findings
- **Status:** complete

### Phase 2: Planning & Project Skeleton
- [x] Create target directory structure for apps/services/data/infra/scripts/docs
- [x] Define API and DB model mapping from product document
- [x] Define dbt model graph and test strategy
- [x] Define Docker composition and startup flow
- **Status:** complete

### Phase 3: Implementation
- [x] Implement FastAPI service with required v1 endpoints and health checks
- [x] Implement PostgreSQL schema bootstrap and idempotent raw ingest
- [x] Implement connector worker (5-min deterministic random signal + retry)
- [x] Implement dbt project (raw -> canonical -> domain -> mart + tests)
- [x] Implement React Native app logic (manual ingest + daily summary)
- [x] Integrate full RN native project scaffold (`ios/` + `Podfile` + native entry files)
- [x] Implement Docker compose and env templates
- [x] Implement `scripts/dev/verify_v0_1_0.sh`
- [x] Implement `scripts/dev/run_openmetadata_ingestion.sh`
- [x] Add developer docs for setup and runbook
- **Status:** complete

### Phase 4: Testing & Verification
- [x] Run local validation checks for API
- [x] Run lint/static checks for Python and scripts
- [x] Run dbt build/docs/ingestion checks in Docker
- [x] Verify documentation consistency with code
- [x] Run `bash scripts/dev/verify_v0_1_0.sh` end-to-end and pass
- **Status:** complete

### Phase 5: Delivery
- [x] Summarize completed items vs v0.1.0 acceptance checklist
- [x] Call out risks/gaps and decisions requiring user confirmation
- [x] Clean dead code and generated artifacts for v0.1.0 handoff
- [x] Finalize v0.1.0 docs consistency (startup, verification, links)
- [x] Deliver final report with changed files and next steps
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Keep `poc_signal` as independent bounded context and avoid 8-system business modeling | Explicitly required by product v0.1.0 scope. |
| Use SQLAlchemy + raw SQL for ingest/idempotency behavior | Fits FastAPI + Postgres requirements and keeps data-path logic transparent. |
| Use OpenMetadata with JWT-based ingestion auth in scripts | Required by OpenMetadata 1.11 ingestion workflow and avoids manual token copy steps. |
| Keep OpenMetadata server healthcheck as TCP probe inside container | Server image lacks `curl`; TCP probe keeps compose health status reliable. |
| Build RN app from official CLI scaffold, then merge existing business UI/logic | Satisfies “full iOS native project” requirement with standard `ios` project structure. |
| Remove unused API schema/helper code and runtime artifacts before handoff | Reduces maintenance noise and avoids shipping generated/local-only files in v0.1.0. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| Docker image pull/network instability | Added mirror/proxy support (`IMAGE_MIRROR_PREFIX`, `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`) and retried successfully. |
| API ingest returned 500 due `:request_id::uuid` SQL syntax | Replaced with `cast(:request_id as uuid)` in ingest/audit SQL. |
| OpenMetadata ingestion failed (`authProvider: no-auth` invalid) | Switched ingestion workflow auth to `openmetadata` + JWT token fetched by script login. |
| OpenMetadata server unhealthy due missing `curl` in image | Replaced healthcheck with bash `/dev/tcp` probe. |
| dbt ingestion config schema mismatch (`dbtConfigType` missing) | Updated dbt ingestion YAML to `dbtConfigType: local`. |
