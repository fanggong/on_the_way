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

log_ok() {
  echo "[PASS] $1"
}

log_fail() {
  echo "[FAIL] $1"
  FAILED=1
}

FAILED=0
API_BASE="http://localhost:$(env_get API_PORT 8000)"
WEB_BASE="http://localhost:$(env_get WEB_PORT 3000)"
PG_USER="$(env_get POSTGRES_USER otw)"
PG_DB="$(env_get POSTGRES_DB otw_dev)"

SERVICES=(postgres api-service connector-worker dbt-runner web-client)
for service in "${SERVICES[@]}"; do
  if compose ps --status running --services | grep -qx "${service}"; then
    log_ok "service running: ${service}"
  else
    log_fail "service not running: ${service}"
  fi
done

if curl -fsS "${API_BASE}/v1/health/live" >/dev/null; then
  log_ok "api health/live"
else
  log_fail "api health/live"
fi

if curl -fsS "${WEB_BASE}" >/dev/null; then
  log_ok "web homepage reachable"
else
  log_fail "web homepage reachable"
fi

TEST_EMAIL="v040_$(date +%s)@example.com"
TEST_PASSWORD="Passw0rd123"
COOKIE_JAR="/tmp/otw_v040_cookies.txt"

register_status="$(curl -sS -o /tmp/otw_v040_register.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")"
if [[ "${register_status}" == "200" ]]; then
  log_ok "auth/register"
else
  log_fail "auth/register (status=${register_status})"
fi

login_status="$(curl -sS -c "${COOKIE_JAR}" -o /tmp/otw_v040_login.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")"
if [[ "${login_status}" == "200" ]]; then
  log_ok "auth/login"
else
  log_fail "auth/login (status=${login_status})"
fi

ACCESS_TOKEN="$(python3 - <<'PY'
import json
with open('/tmp/otw_v040_login.json','r',encoding='utf-8') as f:
    body=json.load(f)
print((body.get('data') or {}).get('access_token',''))
PY
)"

if [[ -n "${ACCESS_TOKEN}" ]]; then
  log_ok "access token issued"
else
  log_fail "access token issued"
fi

if python3 - <<'PY'
import json
with open('/tmp/otw_v040_login.json','r',encoding='utf-8') as f:
    body=json.load(f)
assert (body.get('data') or {}).get('profile_completed') is False
PY
then
  log_ok "first login profile_completed=false"
else
  log_fail "first login profile_completed=false"
fi

profile_status="$(curl -sS -o /tmp/otw_v040_profile_put.json -w '%{http_code}' \
  -X PUT "${API_BASE}/v1/profile/me" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{"display_name":"v0.4 tester","timezone":"Asia/Shanghai","gender":"other"}')"
if [[ "${profile_status}" == "200" ]]; then
  log_ok "profile/me update"
else
  log_fail "profile/me update (status=${profile_status})"
fi

me_status="$(curl -sS -o /tmp/otw_v040_me.json -w '%{http_code}' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${API_BASE}/v1/auth/me")"
if [[ "${me_status}" == "200" ]] \
  && python3 - <<'PY'
import json
with open('/tmp/otw_v040_me.json','r',encoding='utf-8') as f:
    body=json.load(f)
assert (body.get('data') or {}).get('profile_completed') is True
PY
then
  log_ok "auth/me profile_completed=true"
else
  log_fail "auth/me profile_completed=true"
fi

refresh_status="$(curl -sS -b "${COOKIE_JAR}" -o /tmp/otw_v040_refresh.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/auth/refresh")"
if [[ "${refresh_status}" == "200" ]]; then
  log_ok "auth/refresh"
else
  log_fail "auth/refresh (status=${refresh_status})"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "insert into app.rbac_user_role (user_id, role_code) select user_id, 'admin' from app.user_account where email='${TEST_EMAIL}' on conflict (user_id, role_code) do nothing;" >/dev/null; then
  log_ok "grant admin role to verification user"
else
  log_fail "grant admin role to verification user"
fi

login_status="$(curl -sS -c "${COOKIE_JAR}" -o /tmp/otw_v040_login.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")"
if [[ "${login_status}" == "200" ]]; then
  log_ok "auth/login after role grant"
else
  log_fail "auth/login after role grant (status=${login_status})"
fi

ACCESS_TOKEN="$(python3 - <<'PY'
import json
with open('/tmp/otw_v040_login.json','r',encoding='utf-8') as f:
    body=json.load(f)
print((body.get('data') or {}).get('access_token',''))
PY
)"

if [[ -n "${ACCESS_TOKEN}" ]]; then
  log_ok "access token refreshed after role grant"
else
  log_fail "access token refreshed after role grant"
fi

system_sources_status="$(curl -sS -o /tmp/otw_v040_system_sources.json -w '%{http_code}' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${API_BASE}/v1/system-sources")"
if [[ "${system_sources_status}" == "200" ]] \
  && python3 - <<'PY'
import json
with open('/tmp/otw_v040_system_sources.json','r',encoding='utf-8') as f:
    body=json.load(f)
items=(body.get('data') or {}).get('items') or []
assert len(items)==8
health=[x for x in items if x.get('system_code')=='health']
assert len(health)==1
opts=health[0].get('available_connectors') or []
assert any(opt.get('connector_code')=='garmin_connect' for opt in opts)
PY
then
  log_ok "system-sources returns 8 systems"
else
  log_fail "system-sources returns 8 systems"
fi

core_status="$(curl -sS -o /tmp/otw_v040_core_source.json -w '%{http_code}' \
  -X PUT "${API_BASE}/v1/system-sources/health/core-source" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{"connector_code":"garmin_connect"}')"
if [[ "${core_status}" == "200" ]]; then
  log_ok "set health core source"
else
  log_fail "set health core source (status=${core_status})"
fi

policy_status="$(curl -sS -o /tmp/otw_v040_sync_policy.json -w '%{http_code}' \
  -X PUT "${API_BASE}/v1/system-sources/health/sync-policy" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{"auto_sync_enabled":false,"auto_sync_interval_minutes":60}')"
if [[ "${policy_status}" == "200" ]]; then
  log_ok "update sync policy"
else
  log_fail "update sync policy (status=${policy_status})"
fi

NOW_SHANGHAI="$(TZ=Asia/Shanghai date +%Y-%m-%dT%H:%M:%S+08:00)"
START_SHANGHAI="$(TZ=Asia/Shanghai date -v-1d +%Y-%m-%dT00:00:00+08:00 2>/dev/null || date -d '1 day ago' +%Y-%m-%dT00:00:00+08:00)"

job_status="$(curl -sS -o /tmp/otw_v040_sync_job.json -w '%{http_code}' \
  -X POST "${API_BASE}/v1/system-sources/health/sync-jobs" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{\"job_type\":\"backfill_once\",\"backfill_start_at\":\"${START_SHANGHAI}\",\"backfill_end_at\":\"${NOW_SHANGHAI}\"}")"
if [[ "${job_status}" == "200" ]]; then
  log_ok "create backfill_once job"
else
  log_fail "create backfill_once job (status=${job_status})"
fi

jobs_status="$(curl -sS -o /tmp/otw_v040_jobs.json -w '%{http_code}' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${API_BASE}/v1/system-sources/health/sync-jobs")"
if [[ "${jobs_status}" == "200" ]] \
  && python3 - <<'PY'
import json
with open('/tmp/otw_v040_jobs.json','r',encoding='utf-8') as f:
    body=json.load(f)
items=(body.get('data') or {}).get('items') or []
assert len(items)>=1
assert any(item.get('job_type') in ('backfill_once','auto_sync') for item in items)
PY
then
  log_ok "sync-jobs query"
else
  log_fail "sync-jobs query"
fi

mart_status="$(curl -sS -o /tmp/otw_v040_mart.json -w '%{http_code}' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${API_BASE}/v1/health/mart/overview?page=1&page_size=10")"
if [[ "${mart_status}" == "200" ]]; then
  log_ok "health mart overview endpoint"
else
  log_fail "health mart overview endpoint (status=${mart_status})"
fi

domain_status="$(curl -sS -o /tmp/otw_v040_domain.json -w '%{http_code}' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${API_BASE}/v1/health/domain/metrics?start_date=$(date +%Y-%m-01)&end_date=$(date +%Y-%m-%d)&page=1&page_size=10")"
if [[ "${domain_status}" == "200" ]]; then
  log_ok "health domain metrics endpoint"
else
  log_fail "health domain metrics endpoint (status=${domain_status})"
fi

if compose exec -T postgres psql -U "${PG_USER}" -d "${PG_DB}" -Atc "select case when password_hash <> '${TEST_PASSWORD}' then 1 else 0 end from app.user_account where email='${TEST_EMAIL}' limit 1" | grep -q '^1$'; then
  log_ok "password stored as hash"
else
  log_fail "password stored as hash"
fi

if [[ ${FAILED} -ne 0 ]]; then
  echo "[SUMMARY] v0.4.0 verification FAILED"
  exit 1
fi

echo "[SUMMARY] v0.4.0 verification PASSED"
