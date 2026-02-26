#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"
ENV_FILE="${ROOT_DIR}/infra/docker/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
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

openmetadata_port="$(env_get OPENMETADATA_PORT 8585)"
openmetadata_base="http://localhost:${openmetadata_port}"
openmetadata_admin_email="$(env_get OM_ADMIN_EMAIL admin@open-metadata.org)"
openmetadata_admin_password="$(env_get OM_ADMIN_PASSWORD admin)"
openmetadata_admin_password_b64="$(base64_no_wrap "${openmetadata_admin_password}")"

login_payload="$(printf '{"email":"%s","password":"%s"}' "${openmetadata_admin_email}" "${openmetadata_admin_password_b64}")"

echo "[0/3] Fetch OpenMetadata JWT token..."
login_response="$(curl -fsS -X POST "${openmetadata_base}/api/v1/users/login" -H 'Content-Type: application/json' -d "${login_payload}")"
openmetadata_jwt_token="$(printf '%s' "${login_response}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("accessToken",""))')"

if [[ -z "${openmetadata_jwt_token}" ]]; then
  echo "[ERROR] failed to fetch OpenMetadata access token"
  exit 1
fi

echo "[1/3] Ingest postgres metadata..."
compose run --rm \
  -e "OPENMETADATA_JWT_TOKEN=${openmetadata_jwt_token}" \
  --entrypoint /bin/bash \
  openmetadata-ingestion \
  -lc 'metadata ingest -c /opt/airflow/ingestion/postgres_ingestion.yml'

echo "[2/3] Generate dbt docs artifacts..."
compose run --rm dbt-runner dbt docs generate --target dev

echo "[3/3] Ingest dbt metadata + lineage..."
compose run --rm \
  -e "OPENMETADATA_JWT_TOKEN=${openmetadata_jwt_token}" \
  --entrypoint /bin/bash \
  openmetadata-ingestion \
  -lc 'metadata ingest -c /opt/airflow/ingestion/dbt_ingestion.yml'

echo "[DONE] OpenMetadata ingestion complete"
