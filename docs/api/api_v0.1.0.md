# API 说明 v0.1.0

Base URL: `http://localhost:8000`

## 统一响应

成功:

```json
{"status":"ok", "...":"..."}
```

失败:

```json
{"status":"error","code":"...","message":"...","request_id":"..."}
```

## 错误码

- `INVALID_ARGUMENT`
- `DUPLICATE_IDEMPOTENCY_KEY`
- `RAW_WRITE_FAILED`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

## Endpoint 列表

### `POST /v1/ingest/manual-signal`

请求:

```json
{
  "source_id": "ios_manual",
  "external_id": "ios-20260225-000001",
  "occurred_at": "2026-02-25T10:30:00Z",
  "payload": {
    "value": 73.5,
    "note": "manual input from ios"
  }
}
```

响应:

```json
{
  "status": "ok",
  "raw_id": "uuid",
  "ingested_at": "2026-02-25T10:30:01Z",
  "idempotent": false
}
```

### `POST /v1/ingest/connector-signal`

请求:

```json
{
  "source_id": "signal_random_connector",
  "external_id": "connector-20260225-103000",
  "occurred_at": "2026-02-25T10:30:00Z",
  "payload": {
    "value": 41.2,
    "seed": "20260225-1030",
    "generator_version": "v1"
  }
}
```

响应:

```json
{
  "status": "ok",
  "raw_id": "uuid",
  "ingested_at": "2026-02-25T10:30:01Z",
  "idempotent": false
}
```

### `POST /v1/annotation`

请求:

```json
{
  "target_type": "signal_event",
  "target_id": "uuid",
  "label": "quality_tag",
  "value": "suspect_outlier"
}
```

响应:

```json
{
  "status": "ok",
  "annotation_id": "uuid",
  "created_at": "2026-02-25T10:31:00Z"
}
```

### `GET /v1/poc/signals?limit=50`

返回 Domain 明细。

响应:

```json
{
  "status": "ok",
  "items": [
    {
      "signal_event_id": "uuid",
      "event_id": "uuid",
      "source_type": "manual",
      "value_num": 73.5,
      "occurred_at": "2026-02-25T10:30:00Z",
      "is_valid": true,
      "tags_json": {}
    }
  ]
}
```

### `GET /v1/poc/daily-summary?date=YYYY-MM-DD`

返回 Mart 聚合。

响应:

```json
{
  "status": "ok",
  "stat_date": "2026-02-25",
  "event_count": 289,
  "manual_count": 37,
  "connector_count": 252,
  "avg_value": 49.37,
  "min_value": 1.2,
  "max_value": 98.8
}
```

### `GET /v1/health/connector`

返回连接器最近执行状态与累计成功/失败计数。

响应:

```json
{
  "status": "ok",
  "last_run_at": "2026-02-25T10:35:00Z",
  "last_status": "ok",
  "success_count": 120,
  "failure_count": 1
}
```

### `GET /v1/health/live`

容器健康检查接口。

响应:

```json
{
  "status": "ok",
  "service": "api-service",
  "time": "2026-02-25T10:35:02Z"
}
```
