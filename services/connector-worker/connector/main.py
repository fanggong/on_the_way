from __future__ import annotations

import logging
import random
import time
from datetime import UTC, datetime

import httpx
import psycopg

from connector.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [connector] %(message)s",
)
logger = logging.getLogger(__name__)



def update_connector_health(status: str) -> None:
    with psycopg.connect(settings.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into app.connector_health (
                  id, last_run_at, last_status, success_count, failure_count, updated_at
                ) values (
                  1, now(), %s,
                  case when %s = 'ok' then 1 else 0 end,
                  case when %s = 'error' then 1 else 0 end,
                  now()
                )
                on conflict (id) do update
                set
                  last_run_at = excluded.last_run_at,
                  last_status = excluded.last_status,
                  success_count = app.connector_health.success_count +
                    case when excluded.last_status = 'ok' then 1 else 0 end,
                  failure_count = app.connector_health.failure_count +
                    case when excluded.last_status = 'error' then 1 else 0 end,
                  updated_at = excluded.updated_at;
                """,
                (status, status, status),
            )
        conn.commit()



def build_payload(now_utc: datetime) -> dict:
    slot_epoch = int(now_utc.timestamp())
    slot_epoch = slot_epoch - (slot_epoch % settings.interval_seconds)
    occurred_at = datetime.fromtimestamp(slot_epoch, UTC)
    seed = occurred_at.strftime("%Y%m%d-%H%M")

    value = round(
        random.Random(f"{seed}:{settings.generator_version}").uniform(0, 100),
        2,
    )
    external_id = f"connector-{occurred_at.strftime('%Y%m%d-%H%M%S')}"

    return {
        "source_id": settings.source_id,
        "external_id": external_id,
        "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
        "payload": {
            "value": value,
            "seed": seed,
            "generator_version": settings.generator_version,
        },
    }



def send_once(client: httpx.Client) -> bool:
    payload = build_payload(datetime.now(UTC))
    url = f"{settings.api_base_url.rstrip('/')}{settings.ingest_path}"

    for attempt in range(1, settings.retry_attempts + 1):
        try:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                body = response.json()
                logger.info(
                    "ingested connector signal external_id=%s raw_id=%s idempotent=%s",
                    payload["external_id"],
                    body.get("raw_id"),
                    body.get("idempotent"),
                )
                update_connector_health("ok")
                return True

            logger.warning(
                "ingest failed status=%s body=%s attempt=%s",
                response.status_code,
                response.text,
                attempt,
            )
        except Exception as exc:
            logger.warning("ingest exception attempt=%s err=%s", attempt, exc)

        if attempt < settings.retry_attempts:
            time.sleep(2 ** (attempt - 1))

    update_connector_health("error")
    return False



def main() -> None:
    logger.info(
        "connector started interval_seconds=%s source_id=%s",
        settings.interval_seconds,
        settings.source_id,
    )

    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        while True:
            start = time.time()
            send_once(client)
            elapsed = time.time() - start
            sleep_time = max(settings.interval_seconds - elapsed, 0)
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
