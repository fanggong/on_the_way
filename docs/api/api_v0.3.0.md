# API 说明 v0.3.0

Base URL: `http://localhost:8000`

版本目标：在保留 `v0.1.0` 全部接口兼容的前提下，新增健康连接器写入接口，承载 Garmin Connect 原始健康数据入 Raw。

---

## 1. 兼容性声明

- 保留并继续支持：
  - `POST /v1/ingest/manual-signal`
  - `POST /v1/ingest/connector-signal`
  - `POST /v1/annotation`
  - `GET /v1/poc/signals`
  - `GET /v1/poc/daily-summary`
  - `GET /v1/health/connector`
  - `GET /v1/health/live`
- v0.3.0 新增：
  - `POST /v1/ingest/connector-health`

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

沿用 v0.1.0 基线：
- `INVALID_ARGUMENT`
- `DUPLICATE_IDEMPOTENCY_KEY`
- `RAW_WRITE_FAILED`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

建议补充（可选）：
- `UNSUPPORTED_METRIC_TYPE`
- `INVALID_TIMEZONE`

> 若暂不新增错误码，以上两类错误可先统一归入 `INVALID_ARGUMENT`。

---

## 4. 新增 Endpoint

### `POST /v1/ingest/connector-health`

用途：健康系统连接器写 Raw 入口（Garmin Connect 数据）。

#### 4.1 请求体

```json
{
  "source_id": "garmin_connect_health",
  "external_id": "garmin::9f20d8a3a1f2::sleep::2026-02-26::7d9e12af4c8a309b",
  "occurred_at": "2026-02-26T00:00:00+08:00",
  "payload": {
    "connector": "garmin_connect",
    "connector_version": "v0.3.0",
    "account_ref": "9f20d8a3a1f2",
    "metric_type": "sleep",
    "metric_date": "2026-02-26",
    "timezone": "Asia/Shanghai",
    "fetched_at": "2026-02-26T10:10:05+08:00",
    "api_method": "get_sleep_data",
    "data": {
      "...": "garmin raw response"
    }
  }
}
```

#### 4.2 字段约束

顶层字段：
- `source_id`: 固定 `garmin_connect_health`
- `external_id`: 非空，建议最大长度 `128`
- `occurred_at`: ISO 8601 + 时区
- `payload`: object，结构见下

`payload` 字段：
- `connector`: 固定 `garmin_connect`
- `connector_version`: 非空字符串
- `account_ref`: 脱敏账号标识（建议 `sha256(email)` 前 12 位）
- `metric_type`: 枚举（见 4.3）
- `metric_date`: `YYYY-MM-DD`
- `timezone`: 固定 `Asia/Shanghai`
- `fetched_at`: ISO 8601 + 时区
- `api_method`: 选填，记录 SDK 实际调用方法名
- `data`: Garmin 原始返回对象（json object）

#### 4.3 `metric_type` 枚举（v0.3.0）

- `user_summary`
- `sleep`
- `heart_rate`
- `resting_heart_rate`
- `stress`
- `body_battery`
- `respiration`
- `spo2`
- `hrv`
- `intensity_minutes`
- `weight`
- `body_composition`
- `hydration`
- `blood_pressure`
- `menstrual`
- `pregnancy`
- `activities`
- `training_status`
- `training_readiness`
- `recovery_time`
- `max_metrics_vo2`
- `race_prediction`
- `hill_score`
- `endurance_score`
- `lactate_threshold`
- `workouts`
- `training_plans`
- `devices`
- `gear`
- `goals`
- `badges`
- `challenges`

#### 4.4 成功响应

```json
{
  "status": "ok",
  "raw_id": "f6b7a3de-7f74-4c5f-a38c-45a1b2a91a42",
  "ingested_at": "2026-02-26T10:10:06+08:00",
  "idempotent": false
}
```

#### 4.5 幂等行为

幂等键：`source_id + external_id`

- 同键且 payload 一致：
  - HTTP `200`
  - `idempotent=true`
- 同键但 payload 不一致：
  - HTTP `409`
  - `code=DUPLICATE_IDEMPOTENCY_KEY`

---

## 5. 存储契约（Raw）

写入表：`raw.raw_event`

- `source_id` = `garmin_connect_health`
- `external_id` = `garmin::<account_ref>::<metric_type>::<metric_date>::<payload_digest16>`
- `occurred_at` = `metric_date` 零点（`Asia/Shanghai`，`+08:00`）
- `payload_json` = 完整 payload envelope

---

## 6. 连接器调用建议

### 6.1 成功写入 cURL（联调用）

```bash
curl -sS -X POST "http://localhost:8000/v1/ingest/connector-health" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "garmin_connect_health",
    "external_id": "garmin::9f20d8a3a1f2::sleep::2026-02-26::7d9e12af4c8a309b",
    "occurred_at": "2026-02-26T00:00:00+08:00",
    "payload": {
      "connector": "garmin_connect",
      "connector_version": "v0.3.0",
      "account_ref": "9f20d8a3a1f2",
      "metric_type": "sleep",
      "metric_date": "2026-02-26",
      "timezone": "Asia/Shanghai",
      "fetched_at": "2026-02-26T10:10:05+08:00",
      "api_method": "get_sleep_data",
      "data": {"sample": true}
    }
  }'
```

### 6.2 再次发送同 payload（幂等）

- 返回 `status=ok`
- `idempotent=true`

---

## 7. 安全约束

- `GARMIN_EMAIL/GARMIN_PASSWORD` 不得出现在 API 请求日志。
- API 层禁止回写任何明文凭据到 `payload_json`。
- `account_ref` 必须为脱敏值，不可写邮箱原文。

---

## 8. 版本文档关系

- 产品范围：`docs/product/product_v0.3.0.md`
- 启动与验收：`docs/run/交付物启动与验收说明_v0.3.0.md`
- v0.1.0 基线 API：`docs/api/api_v0.1.0.md`
