# On The Way - v0.3.1 Accepted

Current status:
- `v0.2.0` accepted on `2026-02-26`
- `v0.3.0` accepted on `2026-02-26`
- `v0.3.1` accepted on `2026-02-27`

This repository currently contains:

- `v0.3.1` health data pipeline: `raw -> canonical -> domain_health -> mart`
- `v0.3.1` POC retirement (`poc_signal` API/dbt/iOS debug path removed)
- `v0.3.1` metadata governance updates (dbt descriptions + DB comments + OpenMetadata scope + legacy metadata cleanup)

Core modules:

- `services/api` FastAPI ingestion/annotation/health service
- `services/connector-worker` Garmin health connector worker
- `data/dbt` health canonical, domain, and mart models
- `apps/ios` React Native iOS app (home theme navigation only)
- `infra/docker` one-command local deployment
- `scripts/dev/verify_v0_3_1.sh` verification script

## Quick Start

```bash
cp infra/docker/.env.example infra/docker/.env
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d
bash scripts/dev/run_openmetadata_ingestion.sh
bash scripts/dev/verify_v0_3_1.sh
```

## Runbook

- v0.3.1 启动与验收: `docs/run/交付物启动与验收说明_v0.3.1.md`
- v0.3.0（历史）: `docs/run/交付物启动与验收说明_v0.3.0.md`
- v0.2.0（历史）: `docs/run/交付物启动与验收说明_v0.2.0.md`
- v0.1.0（历史归档）: `docs/run/交付物启动与验收说明_v0.1.0.md`

## Product / API Docs

- v0.3.1 产品文档: `docs/product/product_v0.3.1.md`
- v0.3.1 API 文档: `docs/api/api_v0.3.1.md`
