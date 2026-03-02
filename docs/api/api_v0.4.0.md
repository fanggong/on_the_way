# API 说明 v0.4.0

Base URL: `http://localhost:8000`  
状态: `已验收（已完成）`（2026-03-02）

版本目标：
- 新增 Web 鉴权闭环（注册/登录/刷新/登出/当前用户）
- 新增首次登录资料维护流程
- 新增 RBAC 与系统数据源治理接口
- 新增同步策略与单次回填任务接口
- 新增健康模块配置与查询接口
- 保留 v0.3.1 健康接入接口 `POST /v1/ingest/connector-health`

---

## 1. 统一响应

成功：

```json
{"status":"ok","data":{}}
```

失败：

```json
{"status":"error","code":"...","message":"...","request_id":"..."}
```

新增常用错误码：
- `UNAUTHORIZED`
- `FORBIDDEN`
- `EMAIL_ALREADY_EXISTS`
- `TOO_MANY_REQUESTS`
- `CONFLICT`
- `NOT_FOUND`

---

## 2. 鉴权与资料接口

- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `GET /v1/auth/me`
- `GET /v1/profile/me`
- `PUT /v1/profile/me`

说明：
1. 首个注册用户自动分配 `super_admin`。
2. refresh token 存于 HttpOnly Cookie，access token 由客户端持有并用于 `Authorization: Bearer ...`。
3. `PUT /v1/profile/me` 成功后置 `profile_completed=true`。

---

## 3. RBAC 接口

- `GET /v1/rbac/me-permissions`
- `GET /v1/rbac/users`（需 `rbac.user_role.write`）
- `PUT /v1/rbac/users/{user_id}/roles`（需 `rbac.user_role.write`）

角色：
- `super_admin`
- `admin`
- `analyst`
- `viewer`

核心权限：
- `profile.write`
- `health.connector.write`
- `health.domain.read`
- `health.mart.read`
- `system_source.write`
- `rbac.user_role.write`

---

## 4. 系统数据源管理接口

- `GET /v1/system-sources`
- `PUT /v1/system-sources/{system_code}/core-source`
- `PUT /v1/system-sources/{system_code}/connectors/{connector_code}`
- `GET /v1/system-sources/{system_code}/sync-policy`
- `PUT /v1/system-sources/{system_code}/sync-policy`
- `POST /v1/system-sources/{system_code}/sync-jobs`
- `GET /v1/system-sources/{system_code}/sync-jobs`

约束：
1. 每系统仅一个核心连接器。
2. 同步策略仅对核心连接器生效。
3. 回填任务仅支持 `job_type=backfill_once`。
4. 同系统有运行中任务时，提交新回填任务返回 `409 CONFLICT`。
5. 回填时间范围默认上限 30 天。
6. 写接口（`PUT/POST`）需 `system_source.write`；读接口（`GET`）需登录态。

---

## 5. 健康模块接口

保留：
- `POST /v1/ingest/connector-health`
- `GET /v1/health/connector`
- `GET /v1/health/live`

新增：
- `GET /v1/health/connectors/config`
- `PUT /v1/health/connectors/config`
- `GET /v1/health/domain/metrics`
- `GET /v1/health/mart/overview`
- `GET /v1/health/mart/metric-summary`
- `GET /v1/health/mart/activity-topics`

说明：
1. `health/connectors/config` 仅维护连接器白名单字段，不维护自动同步频率。
2. Domain 与 Mart 查询在无数据时返回空集合，不返回 5xx。

---

## 6. 数据模型（app schema）

新增核心表：
- `app.user_account`
- `app.user_profile`
- `app.user_session`
- `app.rbac_role`
- `app.rbac_permission`
- `app.rbac_role_permission`
- `app.rbac_user_role`
- `app.system_connector_option`
- `app.system_core_source`
- `app.connector_sync_job`

---

## 7. 历史版本关系

- 产品文档：`docs/product/product_v0.4.0.md`
- 启动与验收：`docs/run/交付物启动与验收说明_v0.4.0.md`
- v0.3.1 API（历史）：`docs/api/api_v0.3.1.md`

---

## 8. 验收记录（2026-03-02）

- 验收结论：`通过`
- 验收覆盖：
  1. 鉴权、资料维护、RBAC、系统数据源、同步任务、健康查询接口可用。
  2. 接口权限符合预期：读接口按登录态，写接口按权限控制。
  3. `scripts/dev/verify_v0_4_0.sh` 执行通过。
