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
  if base64 --help 2>/dev/null | grep -q -- "-w"; then
    printf '%s' "$1" | base64 -w0
  else
    printf '%s' "$1" | base64 | tr -d '\n'
  fi
}

compute_account_ref() {
  local email="$1"
  python3 - "$email" <<'PY'
import hashlib
import sys

email = sys.argv[1].strip().lower()
if not email:
    print("")
else:
    print(hashlib.sha256(email.encode("utf-8")).hexdigest()[:12])
PY
}

api_url() {
  local port
  port="$(env_get API_PORT 8000)"
  echo "http://localhost:${port}"
}

om_url() {
  local port
  port="$(env_get OPENMETADATA_PORT 8585)"
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
PG_USER="$(env_get POSTGRES_USER otw)"
PG_DB="$(env_get POSTGRES_DB otw_dev)"
OM_ADMIN_EMAIL="$(env_get OM_ADMIN_EMAIL admin@open-metadata.org)"
OM_ADMIN_PASSWORD="$(env_get OM_ADMIN_PASSWORD admin)"
GARMIN_EMAIL="$(env_get GARMIN_EMAIL "")"
METRIC_DATE="$(TZ=Asia/Shanghai date +%Y-%m-%d)"
OCCURRED_AT="${METRIC_DATE}T00:00:00+08:00"
FETCHED_AT="$(TZ=Asia/Shanghai date +%Y-%m-%dT%H:%M:%S+08:00)"
EXTERNAL_ID="garmin::verify::sleep::${METRIC_DATE}::$(date +%s)"
ACCOUNT_REF="$(compute_account_ref "${GARMIN_EMAIL}")"
if [[ -z "${ACCOUNT_REF}" ]]; then
  ACCOUNT_REF="$(compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select payload_json->>'account_ref' as account_ref from raw.raw_event where source_id='garmin_connect_health' and coalesce(payload_json->>'account_ref','') ~ '^[0-9a-f]{12}$' group by 1 order by count(*) desc limit 1;" 2>/dev/null || true)"
fi
if [[ -z "${ACCOUNT_REF}" ]]; then
  ACCOUNT_REF="000000000000"
fi

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

if curl -fsS "${API_BASE}/v1/health/connector" >/dev/null; then
  log_ok "connector health endpoint"
else
  log_fail "connector health endpoint"
fi

manual_status="$(curl -sS -o /tmp/otw_v031_manual_retired.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/ingest/manual-signal" \
  -H 'Content-Type: application/json' \
  -d '{"source_id":"ios_manual","external_id":"retired-check","occurred_at":"2026-02-27T00:00:00+08:00","payload":{"value":50,"note":"retired-check"}}')"
if [[ "${manual_status}" == "404" ]]; then
  log_ok "manual-signal retired"
else
  log_fail "manual-signal retired (status=${manual_status})"
fi

poc_status="$(curl -sS -o /tmp/otw_v031_poc_retired.json -w '%{http_code}' \
  "${API_BASE}/v1/poc/daily-summary?date=${METRIC_DATE}")"
if [[ "${poc_status}" == "404" ]]; then
  log_ok "poc daily-summary retired"
else
  log_fail "poc daily-summary retired (status=${poc_status})"
fi

health_payload="$(cat <<JSON
{
  "source_id": "garmin_connect_health",
  "external_id": "${EXTERNAL_ID}",
  "occurred_at": "${OCCURRED_AT}",
  "payload": {
    "connector": "garmin_connect",
    "connector_version": "v0.3.1",
    "account_ref": "${ACCOUNT_REF}",
    "metric_type": "sleep",
    "metric_date": "${METRIC_DATE}",
    "timezone": "Asia/Shanghai",
    "fetched_at": "${FETCHED_AT}",
    "api_method": "verify_method",
    "data": {
      "sleepTimeSeconds": 25200,
      "restingHeartRate": 60,
      "avgStressLevel": 22,
      "bodyBatteryAverage": 71,
      "totalSteps": 8888,
      "activeKilocalories": 503
    }
  }
}
JSON
)"

status_code="$(curl -sS -o /tmp/otw_v031_ingest_1.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/ingest/connector-health" \
  -H 'Content-Type: application/json' \
  -d "${health_payload}")"
if [[ "${status_code}" == "200" ]]; then
  log_ok "connector-health ingest"
else
  log_fail "connector-health ingest (status=${status_code})"
fi

status_code="$(curl -sS -o /tmp/otw_v031_ingest_2.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/ingest/connector-health" \
  -H 'Content-Type: application/json' \
  -d "${health_payload}")"
if [[ "${status_code}" == "200" ]] \
  && python3 - <<'PY'
import json
with open('/tmp/otw_v031_ingest_2.json','r',encoding='utf-8') as f:
    body=json.load(f)
assert body.get('idempotent') is True
PY
then
  log_ok "connector-health idempotent replay"
else
  log_fail "connector-health idempotent replay"
fi

if compose exec -T dbt-runner dbt build --target dev >/tmp/otw_dbt_build_v031.log 2>&1; then
  log_ok "dbt build"
else
  log_fail "dbt build"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from canonical.health_event" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "canonical.health_event has data"
else
  log_fail "canonical.health_event has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from canonical.health_metric_daily" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "canonical.health_metric_daily has data"
else
  log_fail "canonical.health_metric_daily has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from domain_health.health_metric_daily_fact" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "domain_health.health_metric_daily_fact has data"
else
  log_fail "domain_health.health_metric_daily_fact has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from domain_health.health_activity_event_fact" | grep -Eq '^[0-9]+$'; then
  log_ok "domain_health.health_activity_event_fact queryable"
else
  log_fail "domain_health.health_activity_event_fact queryable"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(distinct payload_json->>'account_ref') from raw.raw_event where source_id='garmin_connect_health'" | grep -q '^1$'; then
  log_ok "raw account_ref single value"
else
  log_fail "raw account_ref single value"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(distinct account_ref) from canonical.health_event" | grep -q '^1$'; then
  log_ok "canonical.health_event account_ref single value"
else
  log_fail "canonical.health_event account_ref single value"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from mart.health_metric_daily_summary" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "mart.health_metric_daily_summary has data"
else
  log_fail "mart.health_metric_daily_summary has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(distinct account_ref) from mart.health_metric_daily_summary" | grep -q '^1$'; then
  log_ok "mart.health_metric_daily_summary account_ref single value"
else
  log_fail "mart.health_metric_daily_summary account_ref single value"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from mart.health_daily_overview" | grep -Eq '^[1-9][0-9]*$'; then
  log_ok "mart.health_daily_overview has data"
else
  log_fail "mart.health_daily_overview has data"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(distinct account_ref) from mart.health_daily_overview" | grep -q '^1$'; then
  log_ok "mart.health_daily_overview account_ref single value"
else
  log_fail "mart.health_daily_overview account_ref single value"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from mart.health_activity_topic_daily" | grep -Eq '^[0-9]+$'; then
  log_ok "mart.health_activity_topic_daily queryable"
else
  log_fail "mart.health_activity_topic_daily queryable"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from information_schema.schemata where schema_name in ('domain_poc_signal','mart_poc_signal')" | grep -q '^0$'; then
  log_ok "POC schemas removed"
else
  log_fail "POC schemas removed"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from raw.raw_event where source_id in ('ios_manual','signal_random_connector')" | grep -q '^0$'; then
  log_ok "POC raw data cleaned"
else
  log_fail "POC raw data cleaned"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from app.request_audit where source_id in ('ios_manual','signal_random_connector')" | grep -q '^0$'; then
  log_ok "POC audit data cleaned"
else
  log_fail "POC audit data cleaned"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select count(*) from annotation.annotation where target_type='signal_event'" | grep -q '^0$'; then
  log_ok "POC annotation data cleaned"
else
  log_fail "POC annotation data cleaned"
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

om_search_table() {
  local query="$1"
  if [[ -n "${OM_TOKEN}" ]]; then
    curl -fsS -H "Authorization: Bearer ${OM_TOKEN}" "${OM_BASE}/api/v1/search/query?q=${query}&index=table"
  else
    curl -fsS "${OM_BASE}/api/v1/search/query?q=${query}&index=table"
  fi
}

check_openmetadata_visibility() {
  om_search_table "health_metric_daily_summary" | python3 -c '
import json
import sys

target_fqn = "otw_postgres.otw_dev.mart.health_metric_daily_summary"
hits = json.load(sys.stdin).get("hits", {}).get("hits", [])
found = any((item.get("_source") or {}).get("fullyQualifiedName") == target_fqn for item in hits)
sys.exit(0 if found else 1)
'
}

check_openmetadata_legacy_keyword_absent() {
  local keyword="$1"
  om_search_table "${keyword}" | python3 -c '
import json
import sys

keyword = sys.argv[1].lower()
hits = json.load(sys.stdin).get("hits", {}).get("hits", [])
matches = []
for item in hits:
    fqn = ((item.get("_source") or {}).get("fullyQualifiedName") or "").lower()
    if keyword in fqn:
        matches.append(fqn)

if matches:
    for fqn in sorted(set(matches)):
        print(fqn)
    sys.exit(1)
sys.exit(0)
' "${keyword}"
}

check_openmetadata_no_legacy_entities() {
  local keyword
  for keyword in domain_poc_signal mart_poc_signal mart_health; do
    if ! check_openmetadata_legacy_keyword_absent "${keyword}"; then
      return 1
    fi
  done
  return 0
}

OM_REFRESHED=0
refresh_openmetadata_once() {
  if [[ "${OM_REFRESHED}" -eq 1 ]]; then
    return 0
  fi
  echo "[INFO] refreshing OpenMetadata ingestion..."
  if bash "${ROOT_DIR}/scripts/dev/run_openmetadata_ingestion.sh" >/tmp/otw_v031_om_refresh.log 2>&1; then
    OM_REFRESHED=1
    return 0
  fi
  return 1
}

if check_openmetadata_visibility; then
  log_ok "openmetadata mart visibility"
else
  echo "[INFO] openmetadata visibility miss."
  if refresh_openmetadata_once && check_openmetadata_visibility; then
    log_ok "openmetadata mart visibility"
  else
    log_fail "openmetadata mart visibility"
  fi
fi

if check_openmetadata_no_legacy_entities; then
  log_ok "openmetadata legacy metadata removed"
else
  echo "[INFO] openmetadata legacy metadata found."
  if refresh_openmetadata_once && check_openmetadata_no_legacy_entities; then
    log_ok "openmetadata legacy metadata removed"
  else
    log_fail "openmetadata legacy metadata removed"
  fi
fi

if [[ ${FAILED} -eq 0 ]]; then
  echo "[DONE] verify_v0_3_1 passed"
  exit 0
fi

echo "[DONE] verify_v0_3_1 failed"
exit 1
