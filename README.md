# On The Way - v0.2.0 UI on v0.1.0 Baseline

Current status: `v0.2.0 accepted on 2026-02-26`.

This repository currently contains:

- `v0.1.0` runnable data platform baseline for `poc_signal`
- `v0.2.0` iOS home UI/UX redesign (no backend/data changes)

Core modules:

- `services/api` FastAPI ingestion/query service
- `services/connector-worker` deterministic random connector
- `data/dbt` raw/canonical/domain/mart models and tests
- `apps/ios` full React Native iOS native project (Xcode + Podfile + app logic + v0.2.0 home)
- `infra/docker` one-command local deployment
- `scripts/dev/verify_v0_1_0.sh` verification script

## Quick Start

```bash
cp infra/docker/.env.example infra/docker/.env
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d
bash scripts/dev/run_openmetadata_ingestion.sh
bash scripts/dev/verify_v0_1_0.sh
```

## Runbook

- v0.1.0 全量交付物启动与验收: `docs/run/交付物启动与验收说明_v0.1.0.md`
- v0.2.0 iOS 首页 UI/UX 验收: `docs/run/交付物启动与验收说明_v0.2.0.md`
