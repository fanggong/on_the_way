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

cleanup_legacy_metadata() {
  local openmetadata_base="$1"
  local openmetadata_jwt_token="$2"
  python3 - "${openmetadata_base}" "${openmetadata_jwt_token}" <<'PY'
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

base = sys.argv[1].rstrip("/")
token = sys.argv[2]
keywords = ("domain_poc_signal", "mart_poc_signal", "mart_health")
entity_endpoints = {
    "table": "tables",
    "databaseSchema": "databaseSchemas",
}


def request_json(url: str, method: str = "GET") -> dict:
    req = urllib.request.Request(
        url=url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


to_delete = {}
for keyword in keywords:
    for index in ("table", "databaseSchema"):
        search_url = (
            f"{base}/api/v1/search/query?q={urllib.parse.quote(keyword)}"
            f"&index={index}&from=0&size=200"
        )
        payload = request_json(search_url)
        hits = payload.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source") or {}
            entity_type = source.get("entityType")
            entity_id = source.get("id")
            fqn = (source.get("fullyQualifiedName") or "").lower()
            if entity_type not in entity_endpoints or not entity_id:
                continue
            if keyword not in fqn:
                continue
            to_delete[(entity_type, entity_id)] = source.get("fullyQualifiedName") or entity_id

if not to_delete:
    print("[INFO] legacy metadata cleanup: no stale entities found")
    sys.exit(0)

print(f"[INFO] legacy metadata cleanup: hard deleting {len(to_delete)} entities")
for (entity_type, entity_id), fqn in sorted(to_delete.items()):
    endpoint = entity_endpoints[entity_type]
    delete_url = f"{base}/api/v1/{endpoint}/{entity_id}?hardDelete=true&recursive=true"
    try:
        request_json(delete_url, method="DELETE")
        print(f"[INFO] hard deleted {entity_type}: {fqn}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"[INFO] already removed {entity_type}: {fqn}")
            continue
        raise
PY
}

openmetadata_port="$(env_get OPENMETADATA_PORT 8585)"
openmetadata_base="http://localhost:${openmetadata_port}"
openmetadata_admin_email="$(env_get OM_ADMIN_EMAIL admin@open-metadata.org)"
openmetadata_admin_password="$(env_get OM_ADMIN_PASSWORD admin)"
openmetadata_admin_password_b64="$(base64_no_wrap "${openmetadata_admin_password}")"

login_payload="$(printf '{"email":"%s","password":"%s"}' "${openmetadata_admin_email}" "${openmetadata_admin_password_b64}")"

echo "[0/4] Fetch OpenMetadata JWT token..."
login_response="$(curl -fsS -X POST "${openmetadata_base}/api/v1/users/login" -H 'Content-Type: application/json' -d "${login_payload}")"
openmetadata_jwt_token="$(printf '%s' "${login_response}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("accessToken",""))')"

if [[ -z "${openmetadata_jwt_token}" ]]; then
  echo "[ERROR] failed to fetch OpenMetadata access token"
  exit 1
fi

echo "[1/4] Ingest postgres metadata..."
compose run --rm \
  -e "OPENMETADATA_JWT_TOKEN=${openmetadata_jwt_token}" \
  --entrypoint /bin/bash \
  openmetadata-ingestion \
  -lc 'metadata ingest -c /opt/airflow/ingestion/postgres_ingestion.yml'

echo "[2/4] Generate dbt docs artifacts..."
compose run --rm dbt-runner dbt docs generate --target dev

echo "[3/4] Ingest dbt metadata + lineage..."
compose run --rm \
  -e "OPENMETADATA_JWT_TOKEN=${openmetadata_jwt_token}" \
  --entrypoint /bin/bash \
  openmetadata-ingestion \
  -lc 'metadata ingest -c /opt/airflow/ingestion/dbt_ingestion.yml'

echo "[4/4] Hard-delete legacy metadata entities..."
cleanup_legacy_metadata "${openmetadata_base}" "${openmetadata_jwt_token}"

echo "[DONE] OpenMetadata ingestion complete"
