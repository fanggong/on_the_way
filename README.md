# On The Way - v0.4.0 Accepted

Current status:
- `v0.2.0` accepted on `2026-02-26`
- `v0.3.0` accepted on `2026-02-26`
- `v0.3.1` accepted on `2026-02-27`
- `v0.4.0` accepted on `2026-03-02`

This repository currently contains:

- `v0.4.0` web client (`apps/web`) with auth/profile/RBAC navigation flow
- `v0.4.0` API expansion for auth/profile/rbac/system-sources/health-query
- `v0.4.0` connector scheduler policy + sync-job queue (`auto_sync` / `backfill_once`)
- `v0.3.1` health data pipeline: `raw -> canonical -> domain_health -> mart`
- `v0.3.1` metadata governance updates (dbt descriptions + DB comments + OpenMetadata scope)

Core modules:

- `services/api` FastAPI service (`v0.4.0`)
- `services/connector-worker` Garmin connector scheduler (`v0.4.0`)
- `data/dbt` health canonical, domain, and mart models
- `apps/web` React + Semi Design web client
- `apps/ios` React Native iOS app (historical v0.2.0 scope)
- `infra/docker` one-command local deployment
- `scripts/dev/verify_v0_4_0.sh` verification script

## Quick Start

```bash
cp infra/docker/.env.example infra/docker/.env
# fill AUTH_JWT_SECRET / GARMIN_EMAIL / GARMIN_PASSWORD

docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build

# optional: reset dev data before v0.4.0 integration
psql -h localhost -U otw -d otw_dev -f scripts/dev/reset_dev_data_v0_4_0.sql

bash scripts/dev/verify_v0_4_0.sh
```

## Runbook

- v0.4.0 启动与验收: `docs/run/交付物启动与验收说明_v0.4.0.md`
- v0.3.1 启动与验收（历史）: `docs/run/交付物启动与验收说明_v0.3.1.md`
- v0.3.0（历史）: `docs/run/交付物启动与验收说明_v0.3.0.md`
- v0.2.0（历史）: `docs/run/交付物启动与验收说明_v0.2.0.md`
- v0.1.0（历史归档）: `docs/run/交付物启动与验收说明_v0.1.0.md`

## Product / API Docs

- v0.4.0 产品文档: `docs/product/product_v0.4.0.md`
- v0.4.0 API 文档: `docs/api/api_v0.4.0.md`
- v0.3.1 API 文档（历史）: `docs/api/api_v0.3.1.md`
