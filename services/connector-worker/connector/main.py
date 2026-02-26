from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, time as time_value, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import httpx
import psycopg

from connector.config import DEFAULT_METRICS, settings

try:
    from garminconnect import Garmin
except Exception as exc:  # pragma: no cover - handled at runtime
    Garmin = None
    GARMIN_IMPORT_ERROR = str(exc)
else:  # pragma: no cover - import branch depends on runtime image
    GARMIN_IMPORT_ERROR = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [connector] %(message)s",
)
logger = logging.getLogger(__name__)

MethodMode = Literal["date", "range", "none"]


@dataclass(frozen=True)
class MetricMethod:
    name: str
    mode: MethodMode


@dataclass
class CycleStats:
    ingested: int = 0
    no_data: int = 0
    not_supported: int = 0
    errors: int = 0


METRIC_METHODS: dict[str, tuple[MetricMethod, ...]] = {
    "user_summary": (MetricMethod("get_user_summary", "date"),),
    "sleep": (MetricMethod("get_sleep_data", "date"),),
    "heart_rate": (
        MetricMethod("get_heart_rates", "date"),
        MetricMethod("get_heart_rate", "date"),
    ),
    "resting_heart_rate": (
        MetricMethod("get_rhr_day", "date"),
        MetricMethod("get_resting_heart_rate", "date"),
    ),
    "stress": (MetricMethod("get_stress_data", "date"),),
    "body_battery": (MetricMethod("get_body_battery", "range"),),
    "respiration": (MetricMethod("get_respiration_data", "date"),),
    "spo2": (MetricMethod("get_spo2_data", "date"),),
    "hrv": (
        MetricMethod("get_hrv_data", "date"),
        MetricMethod("get_hrv_summary", "date"),
    ),
    "intensity_minutes": (
        MetricMethod("get_intensity_minutes_data", "date"),
        MetricMethod("get_intensity_minutes", "date"),
    ),
    "weight": (
        MetricMethod("get_weigh_ins", "date"),
        MetricMethod("get_body_composition", "date"),
    ),
    "body_composition": (
        MetricMethod("get_body_composition", "date"),
        MetricMethod("get_body_composition_by_date", "date"),
    ),
    "hydration": (
        MetricMethod("get_hydration_data", "date"),
        MetricMethod("get_hydration", "date"),
    ),
    "blood_pressure": (
        MetricMethod("get_blood_pressure", "date"),
        MetricMethod("get_blood_pressure_data", "date"),
    ),
    "menstrual": (
        MetricMethod("get_menstrual_data", "date"),
        MetricMethod("get_cycle_tracking_data", "date"),
    ),
    "pregnancy": (MetricMethod("get_pregnancy_data", "date"),),
    "activities": (
        MetricMethod("get_activities_by_date", "date"),
        MetricMethod("get_activities", "date"),
    ),
    "training_status": (MetricMethod("get_training_status", "date"),),
    "training_readiness": (MetricMethod("get_training_readiness", "date"),),
    "recovery_time": (
        MetricMethod("get_recovery_time_data", "date"),
        MetricMethod("get_recovery_time", "date"),
    ),
    "max_metrics_vo2": (
        MetricMethod("get_max_metrics", "date"),
        MetricMethod("get_vo2_max_data", "date"),
    ),
    "race_prediction": (
        MetricMethod("get_race_predictions", "none"),
        MetricMethod("get_race_prediction", "date"),
    ),
    "hill_score": (MetricMethod("get_hill_score", "date"),),
    "endurance_score": (MetricMethod("get_endurance_score", "date"),),
    "lactate_threshold": (MetricMethod("get_lactate_threshold", "date"),),
    "workouts": (MetricMethod("get_workouts", "none"),),
    "training_plans": (MetricMethod("get_training_plans", "none"),),
    "devices": (MetricMethod("get_devices", "none"),),
    "gear": (MetricMethod("get_gear", "none"),),
    "goals": (MetricMethod("get_goals", "none"),),
    "badges": (MetricMethod("get_badges", "none"),),
    "challenges": (MetricMethod("get_challenges", "none"),),
}

SNAPSHOT_METRICS = {
    "workouts",
    "training_plans",
    "devices",
    "gear",
    "goals",
    "badges",
    "challenges",
}


def update_connector_health(status: str) -> None:
    with psycopg.connect(
        settings.db_url,
        options="-c timezone=Asia/Shanghai",
    ) as conn:
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


def _hash_payload(payload: dict[str, Any]) -> str:
    payload_bytes = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(payload_bytes).hexdigest()


def _build_account_ref(email: str) -> str:
    return sha256(email.strip().lower().encode("utf-8")).hexdigest()[:12]


def _backfill_marker_path() -> Path:
    return Path(settings.garmin_token_dir) / ".backfill_done"


def _is_backfill_done() -> bool:
    return _backfill_marker_path().exists()


def _mark_backfill_done() -> None:
    marker = _backfill_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)


def _resolve_metric_list() -> tuple[str, ...]:
    allowed = set(DEFAULT_METRICS)
    valid = tuple(metric for metric in settings.garmin_metrics if metric in allowed)
    invalid = [metric for metric in settings.garmin_metrics if metric not in allowed]

    if invalid:
        logger.warning("ignore unsupported metrics from GARMIN_METRICS=%s", ",".join(invalid))

    if valid:
        return valid

    logger.warning("no valid metrics provided, fallback to full metric list")
    return tuple(DEFAULT_METRICS)


def _resolve_metric_dates(now_local_date: date, *, backfill: bool) -> list[date]:
    days = settings.garmin_fetch_window_days
    if backfill:
        days = max(days, settings.garmin_backfill_days)

    start_date = now_local_date - timedelta(days=days - 1)
    return [start_date + timedelta(days=index) for index in range(days)]


def _resolve_target_dates(metric_type: str, window_dates: list[date]) -> list[date]:
    if metric_type in SNAPSHOT_METRICS:
        return [window_dates[-1]]
    return window_dates


def _build_occurred_at(metric_date: date, timezone: ZoneInfo) -> datetime:
    return datetime.combine(metric_date, time_value.min, tzinfo=timezone)


def _normalize_data(raw_data: Any) -> dict[str, Any]:
    if isinstance(raw_data, dict):
        return raw_data
    return {"value": raw_data}


def _build_ingest_request(
    *,
    metric_type: str,
    metric_date: date,
    timezone: ZoneInfo,
    account_ref: str,
    api_method: str | None,
    raw_data: Any,
) -> dict[str, Any]:
    fetched_at = datetime.now(timezone)
    payload = {
        "connector": "garmin_connect",
        "connector_version": settings.connector_version,
        "account_ref": account_ref,
        "metric_type": metric_type,
        "metric_date": metric_date.isoformat(),
        "timezone": settings.garmin_timezone,
        "fetched_at": fetched_at.isoformat(),
        "api_method": api_method,
        "data": _normalize_data(raw_data),
    }

    payload_digest = _hash_payload(payload)[:16]
    external_id = (
        f"garmin::{account_ref}::{metric_type}::{metric_date.isoformat()}::{payload_digest}"
    )
    occurred_at = _build_occurred_at(metric_date, timezone)

    return {
        "source_id": settings.source_id,
        "external_id": external_id,
        "occurred_at": occurred_at.isoformat(),
        "payload": payload,
    }


def _invoke_method(method: Any, *, mode: MethodMode, metric_date: date) -> tuple[str, Any, str | None]:
    day_value = metric_date.isoformat()

    if mode == "date":
        attempts = [
            ((day_value,), {}),
            ((metric_date,), {}),
            ((), {"cdate": day_value}),
            ((), {"date": day_value}),
        ]
    elif mode == "range":
        attempts = [
            ((day_value, day_value), {}),
            ((metric_date, metric_date), {}),
            ((), {"startdate": day_value, "enddate": day_value}),
            ((), {"start": day_value, "end": day_value}),
        ]
    else:
        attempts = [
            ((), {}),
        ]

    signature_error: str | None = None
    for args, kwargs in attempts:
        try:
            return "ok", method(*args, **kwargs), None
        except TypeError as exc:
            signature_error = str(exc)
            continue
        except Exception as exc:  # pragma: no cover - depends on Garmin account/runtime
            return "error", None, str(exc)

    return "not_supported", None, signature_error or "no compatible method signature"


def _is_no_data(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, set, dict)):
        return len(value) == 0
    return False


def _has_metric_signal(metric_type: str, data: Any) -> bool:
    if not isinstance(data, dict):
        return True

    if metric_type == "heart_rate":
        heart_rate_values = data.get("heartRateValues")
        if isinstance(heart_rate_values, (list, dict)) and len(heart_rate_values) > 0:
            return True
        for key in (
            "restingHeartRate",
            "maxHeartRate",
            "minHeartRate",
            "lastSevenDaysAvgRestingHeartRate",
        ):
            value = data.get(key)
            if value not in (None, "", 0):
                return True
        return False

    if metric_type == "resting_heart_rate":
        metrics_map = (data.get("allMetrics") or {}).get("metricsMap")
        if isinstance(metrics_map, dict) and len(metrics_map) > 0:
            return True
        grouped_metrics = data.get("groupedMetrics")
        if isinstance(grouped_metrics, dict) and len(grouped_metrics) > 0:
            return True
        return False

    return True


def _fetch_metric(
    garmin_client: Any,
    *,
    metric_type: str,
    metric_date: date,
) -> tuple[str, Any, str | None, str | None]:
    methods = METRIC_METHODS.get(metric_type, ())
    if not methods:
        return "not_supported", None, None, "metric mapping missing"

    has_callable_method = False
    errors: list[str] = []
    for metric_method in methods:
        method = getattr(garmin_client, metric_method.name, None)
        if not callable(method):
            continue

        has_callable_method = True
        status, data, err = _invoke_method(
            method,
            mode=metric_method.mode,
            metric_date=metric_date,
        )
        if status == "ok":
            if _is_no_data(data) or not _has_metric_signal(metric_type, data):
                return "no_data", None, metric_method.name, None
            return "ok", data, metric_method.name, None

        if status == "not_supported":
            continue

        errors.append(f"{metric_method.name}: {err}")

    if not has_callable_method:
        return "not_supported", None, None, "no callable SDK method found"

    if errors:
        return "error", None, None, "; ".join(errors[-3:])

    return "not_supported", None, None, "all mapped methods unsupported"


def _try_resume_mfa(garmin_client: Any, mfa_code: str) -> bool:
    candidates = (
        "resume_login",
        "submit_mfa_code",
        "validate_mfa",
    )

    for method_name in candidates:
        method = getattr(garmin_client, method_name, None)
        if not callable(method):
            continue

        attempts = [
            ((mfa_code,), {}),
            ((), {"code": mfa_code}),
            ((), {"mfa_code": mfa_code}),
        ]
        for args, kwargs in attempts:
            try:
                method(*args, **kwargs)
                return True
            except TypeError:
                continue
            except Exception as exc:  # pragma: no cover - runtime behavior
                logger.warning("MFA resume failed method=%s err=%s", method_name, exc)
                return False

    return False


def _build_garmin_client() -> Any:
    if Garmin is None:
        raise RuntimeError(f"garminconnect import failed: {GARMIN_IMPORT_ERROR}")

    configured_is_cn = settings.garmin_is_cn
    fallback_is_cn = not configured_is_cn
    constructors = [
        lambda: Garmin(
            settings.garmin_email,
            settings.garmin_password,
            is_cn=configured_is_cn,
        ),
        lambda: Garmin(email=settings.garmin_email, password=settings.garmin_password),
        lambda: Garmin(
            settings.garmin_email,
            settings.garmin_password,
            is_cn=fallback_is_cn,
        ),
        lambda: Garmin(
            email=settings.garmin_email,
            password=settings.garmin_password,
            is_cn=configured_is_cn,
            tokenstore_basepath=settings.garmin_token_dir,
        ),
    ]

    last_error: Exception | None = None
    for constructor in constructors:
        try:
            return constructor()
        except TypeError as exc:
            last_error = exc
            continue

    raise RuntimeError(f"unable to construct Garmin client: {last_error}")


def _login_garmin(garmin_client: Any) -> None:
    Path(settings.garmin_token_dir).mkdir(parents=True, exist_ok=True)

    login_method = getattr(garmin_client, "login", None)
    if not callable(login_method):
        raise RuntimeError("Garmin client has no login method")

    attempts = [
        ((), {"tokenstore_basepath": settings.garmin_token_dir}),
        ((), {"tokenstore": settings.garmin_token_dir}),
        ((), {"token_store": settings.garmin_token_dir}),
        ((settings.garmin_token_dir,), {}),
        ((), {}),
    ]

    last_error: Exception | None = None
    for args, kwargs in attempts:
        try:
            login_method(*args, **kwargs)
            return
        except TypeError:
            continue
        except Exception as exc:  # pragma: no cover - runtime behavior
            if settings.garmin_mfa_code and _try_resume_mfa(
                garmin_client,
                settings.garmin_mfa_code,
            ):
                return
            last_error = exc
            continue

    if last_error is not None:
        raise RuntimeError(f"garmin login failed: {last_error}") from last_error
    raise RuntimeError("garmin login signature is incompatible with current client")


def _send_ingest(
    http_client: httpx.Client,
    *,
    ingest_body: dict[str, Any],
    metric_type: str,
    metric_date: date,
) -> bool:
    url = f"{settings.api_base_url.rstrip('/')}{settings.ingest_path}"

    for attempt in range(1, settings.retry_attempts + 1):
        try:
            response = http_client.post(url, json=ingest_body)
            if response.status_code == 200:
                body = response.json()
                logger.info(
                    "ingested metric_type=%s metric_date=%s external_id=%s raw_id=%s idempotent=%s",
                    metric_type,
                    metric_date.isoformat(),
                    ingest_body["external_id"],
                    body.get("raw_id"),
                    body.get("idempotent"),
                )
                return True

            logger.warning(
                "ingest failed metric_type=%s metric_date=%s status=%s attempt=%s body=%s",
                metric_type,
                metric_date.isoformat(),
                response.status_code,
                attempt,
                response.text,
            )
        except Exception as exc:  # pragma: no cover - network/runtime behavior
            logger.warning(
                "ingest exception metric_type=%s metric_date=%s attempt=%s err=%s",
                metric_type,
                metric_date.isoformat(),
                attempt,
                exc,
            )

        if attempt < settings.retry_attempts:
            time.sleep(2 ** (attempt - 1))

    return False


def _run_cycle(http_client: httpx.Client, *, timezone: ZoneInfo, metrics: tuple[str, ...]) -> CycleStats:
    stats = CycleStats()

    if not settings.garmin_email or not settings.garmin_password:
        logger.error("GARMIN_EMAIL/GARMIN_PASSWORD not configured; skip cycle")
        stats.errors += 1
        return stats

    try:
        garmin_client = _build_garmin_client()
        _login_garmin(garmin_client)
    except Exception as exc:
        logger.error("garmin auth failed: %s", exc)
        stats.errors += 1
        return stats

    now_local_date = datetime.now(timezone).date()
    backfill = not _is_backfill_done()
    metric_dates = _resolve_metric_dates(now_local_date, backfill=backfill)
    account_ref = _build_account_ref(settings.garmin_email)

    if backfill:
        logger.info(
            "backfill mode enabled days=%s date_range=%s..%s",
            len(metric_dates),
            metric_dates[0].isoformat(),
            metric_dates[-1].isoformat(),
        )

    for metric_type in metrics:
        target_dates = _resolve_target_dates(metric_type, metric_dates)
        for metric_date in target_dates:
            status, data, api_method, err = _fetch_metric(
                garmin_client,
                metric_type=metric_type,
                metric_date=metric_date,
            )

            if status == "ok":
                ingest_body = _build_ingest_request(
                    metric_type=metric_type,
                    metric_date=metric_date,
                    timezone=timezone,
                    account_ref=account_ref,
                    api_method=api_method,
                    raw_data=data,
                )
                if _send_ingest(
                    http_client,
                    ingest_body=ingest_body,
                    metric_type=metric_type,
                    metric_date=metric_date,
                ):
                    stats.ingested += 1
                else:
                    stats.errors += 1
                continue

            if status == "no_data":
                stats.no_data += 1
                logger.info(
                    "no_data metric_type=%s metric_date=%s",
                    metric_type,
                    metric_date.isoformat(),
                )
                continue

            if status == "not_supported":
                stats.not_supported += 1
                logger.info(
                    "not_supported metric_type=%s metric_date=%s detail=%s",
                    metric_type,
                    metric_date.isoformat(),
                    err,
                )
                continue

            stats.not_supported += 1
            logger.warning(
                "metric_error_nonfatal metric_type=%s metric_date=%s detail=%s",
                metric_type,
                metric_date.isoformat(),
                err,
            )

    if backfill and stats.errors == 0:
        _mark_backfill_done()

    return stats


def main() -> None:
    metrics = _resolve_metric_list()

    try:
        timezone = ZoneInfo(settings.garmin_timezone)
    except Exception as exc:
        logger.error("invalid GARMIN_TIMEZONE=%s err=%s", settings.garmin_timezone, exc)
        timezone = ZoneInfo("UTC")

    logger.info(
        "connector started interval_seconds=%s source_id=%s metrics=%s",
        settings.interval_seconds,
        settings.source_id,
        len(metrics),
    )

    with httpx.Client(timeout=settings.request_timeout_seconds) as http_client:
        while True:
            start = time.time()
            try:
                stats = _run_cycle(http_client, timezone=timezone, metrics=metrics)
                status = "ok" if stats.errors == 0 else "error"
                update_connector_health(status)
                logger.info(
                    "cycle finished status=%s ingested=%s no_data=%s not_supported=%s errors=%s",
                    status,
                    stats.ingested,
                    stats.no_data,
                    stats.not_supported,
                    stats.errors,
                )
            except Exception as exc:  # pragma: no cover - safety net
                logger.exception("cycle crashed err=%s", exc)
                update_connector_health("error")

            elapsed = time.time() - start
            sleep_time = max(settings.interval_seconds - elapsed, 0)
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
