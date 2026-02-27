# API 说明 v0.3.1

Base URL: `http://localhost:8000`
状态: `已验收（已完成）`（2026-02-27）

版本目标：
- 保留健康连接器写入能力
- 支撑数据链路 `raw -> canonical -> domain_health -> mart`
- 退役 `poc_signal` 相关写入与查询接口
- 保留 annotation（目标切换到 health 对象）

---

## 1. 兼容性声明

v0.3.1 可用接口：
- `POST /v1/ingest/connector-health`
- `POST /v1/annotation`
- `GET /v1/health/connector`
- `GET /v1/health/live`

v0.3.1 已退役接口（应返回 `404`）：
- `POST /v1/ingest/manual-signal`
- `POST /v1/ingest/connector-signal`
- `GET /v1/poc/signals`
- `GET /v1/poc/daily-summary`

---

## 2. 统一响应

成功:

```json
{"status":"ok", "...":"..."}
```

失败:

```json
{"status":"error","code":"...","message":"...","request_id":"..."}
```

---

## 3. 错误码

- `INVALID_ARGUMENT`
- `DUPLICATE_IDEMPOTENCY_KEY`
- `RAW_WRITE_FAILED`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

---

## 4. Endpoint 详情

### 4.1 `POST /v1/ingest/connector-health`

用途：Garmin 健康连接器写入 Raw。

请求示例：

```json
{
  "source_id": "garmin_connect_health",
  "external_id": "garmin::9f20d8a3a1f2::sleep::2026-02-27::7d9e12af4c8a309b",
  "occurred_at": "2026-02-27T00:00:00+08:00",
  "payload": {
    "connector": "garmin_connect",
    "connector_version": "v0.3.1",
    "account_ref": "9f20d8a3a1f2",
    "metric_type": "sleep",
    "metric_date": "2026-02-27",
    "timezone": "Asia/Shanghai",
    "fetched_at": "2026-02-27T10:10:05+08:00",
    "api_method": "get_sleep_data",
    "data": {
      "sleepTimeSeconds": 25200
    }
  }
}
```

字段约束：
- `source_id`: 固定 `garmin_connect_health`
- `occurred_at`: 必须带时区，且必须等于 `metric_date 00:00:00+08:00`
- `payload.metric_type`: 必须在 32 项枚举中
- `payload.account_ref`: 必须为 12 位小写十六进制；若 API 配置了 `GARMIN_EMAIL`，则必须匹配该邮箱推导的脱敏值
- `payload.timezone`: 固定 `Asia/Shanghai`
- `payload.fetched_at`: 必须为东八区偏移

成功响应：

```json
{
  "status": "ok",
  "raw_id": "f6b7a3de-7f74-4c5f-a38c-45a1b2a91a42",
  "ingested_at": "2026-02-27T10:10:06+08:00",
  "idempotent": false
}
```

幂等规则：
- 幂等键：`source_id + external_id`
- 同键同 payload：`200` + `idempotent=true`
- 同键不同 payload：`409` + `DUPLICATE_IDEMPOTENCY_KEY`

### 4.2 `POST /v1/annotation`

用途：对健康对象写人工标注。

请求示例（健康事件）：

```json
{
  "target_type": "health_event",
  "target_id": "f6b7a3de-7f74-4c5f-a38c-45a1b2a91a42",
  "label": "quality_tag",
  "value": "suspect_outlier"
}
```

请求示例（活动事件）：

```json
{
  "target_type": "health_activity_event",
  "target_id": "8f4d2f7cc0e3a9a2f7a7a77cc8e7e333",
  "label": "activity_tag",
  "value": "commute"
}
```

字段约束：
- `target_type`: `health_event` 或 `health_activity_event`
- `target_id`: 必须在对应 Canonical 表存在
- `label`: 1-64 字符
- `value`: 1-256 字符

成功响应：

```json
{
  "status": "ok",
  "annotation_id": "c8ee3e9d-1d8b-4f90-aef7-15fd0f340fe1",
  "created_at": "2026-02-27T10:31:00+08:00"
}
```

### 4.3 `GET /v1/health/connector`

返回连接器最近执行状态与累计成功/失败计数。

### 4.4 `GET /v1/health/live`

容器健康检查接口。

---

## 5. 版本文档关系

- 产品范围：`docs/product/product_v0.3.1.md`
- 启动与验收：`docs/run/交付物启动与验收说明_v0.3.1.md`
- v0.3.0 API（历史）：`docs/api/api_v0.3.0.md`
