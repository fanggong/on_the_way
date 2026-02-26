# On The Way - v0.1.0 Baseline

This repository implements `v0.1.0` baseline for `poc_signal`:

- `services/api` FastAPI ingestion/query service
- `services/connector-worker` deterministic random connector
- `data/dbt` raw/canonical/domain/mart models and tests
- `apps/ios` full React Native iOS native project (Xcode + Podfile + app logic)
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

- 详细启动与验收说明: `docs/run/交付物启动与验收说明_v0.1.0.md`
