#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"
ENV_FILE="${ROOT_DIR}/infra/docker/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[INFO] ${ENV_FILE} not found, copying from .env.example"
  cp "${ROOT_DIR}/infra/docker/.env.example" "${ENV_FILE}"
fi

compose() {
  docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

env_get() {
  local key="$1"
  local default_value="$2"
  local value
  value="$(grep "^${key}=" "${ENV_FILE}" | head -n1 | cut -d '=' -f2- || true)"
  if [[ -z "${value}" ]]; then
    echo "${default_value}"
  else
    echo "${value}"
  fi
}

base64_no_wrap() {
  # GNU coreutils uses -w0, BSD/macOS uses plain base64.
  if base64 --help 2>/dev/null | grep -q -- "-w"; then
    printf '%s' "$1" | base64 -w0
  else
    printf '%s' "$1" | base64 | tr -d '\n'
  fi
}

api_url() {
  local port
  port="$(grep '^API_PORT=' "${ENV_FILE}" | cut -d '=' -f2 || true)"
  if [[ -z "${port}" ]]; then
    port="8000"
  fi
  echo "http://localhost:${port}"
}

om_url() {
  local port
  port="$(grep '^OPENMETADATA_PORT=' "${ENV_FILE}" | cut -d '=' -f2 || true)"
  if [[ -z "${port}" ]]; then
    port="8585"
  fi
  echo "http://localhost:${port}"
}

log_ok() {
  echo "[PASS] $1"
}

log_fail() {
  echo "[FAIL] $1"
  FAILED=1
}

FAILED=0
API_BASE="$(api_url)"
OM_BASE="$(om_url)"
DATE_UTC="$(date -u +%Y-%m-%d)"
TS_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PG_USER="$(env_get POSTGRES_USER otw)"
PG_DB="$(env_get POSTGRES_DB otw_dev)"
OM_ADMIN_EMAIL="$(env_get OM_ADMIN_EMAIL admin@open-metadata.org)"
OM_ADMIN_PASSWORD="$(env_get OM_ADMIN_PASSWORD admin)"
MANUAL_EXTERNAL_ID="ios-verify-$(date -u +%Y%m%d%H%M%S)"
CONNECTOR_EXTERNAL_ID="connector-verify-$(date -u +%Y%m%d%H%M%S)"

SERVICES=(postgres api-service connector-worker dbt-runner openmetadata-db openmetadata-search openmetadata-server)
for service in "${SERVICES[@]}"; do
  if compose ps --status running --services | grep -qx "${service}"; then
    log_ok "service running: ${service}"
  else
    log_fail "service not running: ${service}"
  fi
done

if curl -fsS "${API_BASE}/v1/health/live" >/dev/null; then
  log_ok "api live health"
else
  log_fail "api live health"
fi

manual_code="$(curl -sS -o /tmp/otw_manual_resp.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/ingest/manual-signal" \
  -H 'Content-Type: application/json' \
  -d "{\"source_id\":\"ios_manual\",\"external_id\":\"${MANUAL_EXTERNAL_ID}\",\"occurred_at\":\"${TS_UTC}\",\"payload\":{\"value\":66.6,\"note\":\"verify manual path\"}}")"
if [[ "${manual_code}" == "200" ]]; then
  log_ok "P1 manual ingest"
else
  log_fail "P1 manual ingest (status=${manual_code})"
fi

connector_code="$(curl -sS -o /tmp/otw_connector_resp.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/ingest/connector-signal" \
  -H 'Content-Type: application/json' \
  -d "{\"source_id\":\"signal_random_connector\",\"external_id\":\"${CONNECTOR_EXTERNAL_ID}\",\"occurred_at\":\"${TS_UTC}\",\"payload\":{\"value\":42.4,\"seed\":\"verify-seed\",\"generator_version\":\"v1\"}}")"
if [[ "${connector_code}" == "200" ]]; then
  log_ok "P2 connector ingest"
else
  log_fail "P2 connector ingest (status=${connector_code})"
fi

if compose exec -T dbt-runner dbt build --target dev >/tmp/otw_dbt_build.log 2>&1; then
  log_ok "dbt build"
else
  log_fail "dbt build"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from domain_poc_signal.signal_event" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "domain_poc_signal has data"
else
  log_fail "domain_poc_signal has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from mart_poc_signal.signal_daily_summary where stat_date='${DATE_UTC}'" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "mart_poc_signal daily summary has data"
else
  log_fail "mart_poc_signal daily summary has data"
fi

if curl -fsS "${API_BASE}/v1/health/connector" >/dev/null; then
  log_ok "connector health endpoint"
else
  log_fail "connector health endpoint"
fi

if curl -fsS "${OM_BASE}/api/v1/system/version" >/dev/null; then
  log_ok "openmetadata reachable"
else
  log_fail "openmetadata reachable"
fi

OM_TOKEN=""
if login_resp="$(curl -sS -X POST "${OM_BASE}/api/v1/users/login" -H 'Content-Type: application/json' -d "{\"email\":\"${OM_ADMIN_EMAIL}\",\"password\":\"$(base64_no_wrap "${OM_ADMIN_PASSWORD}")\"}")"; then
  OM_TOKEN="$(printf '%s' "${login_resp}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("accessToken",""))' || true)"
fi

if [[ -n "${OM_TOKEN}" ]]; then
  if curl -fsS -H "Authorization: Bearer ${OM_TOKEN}" "${OM_BASE}/api/v1/search/query?q=signal_daily_summary&index=table" | grep -q "signal_daily_summary"; then
    log_ok "openmetadata lineage/table visibility"
  else
    log_fail "openmetadata lineage/table visibility"
  fi
else
  if curl -fsS "${OM_BASE}/api/v1/search/query?q=signal_daily_summary&index=table" | grep -q "signal_daily_summary"; then
    log_ok "openmetadata lineage/table visibility"
  else
    log_fail "openmetadata lineage/table visibility"
  fi
fi

if [[ ${FAILED} -eq 0 ]]; then
  echo "[DONE] verify_v0_1_0 passed"
  exit 0
fi

echo "[DONE] verify_v0_1_0 failed"
exit 1
