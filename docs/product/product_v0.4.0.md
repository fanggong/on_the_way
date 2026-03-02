# On The Way 产品文档 v0.4.0

版本: `v0.4.0`  
日期: `2026-02-27`  
状态: `已验收（已完成）`（2026-03-02）  
面向角色: 产品、Web 前端、后端研发、数据研发、UI/UX、测试、运维

---

## 1. 版本定位与当前进度

### 1.1 当前项目进度（截至 2026-03-02）
- `v0.1.0` 已完成并验证基础链路（POC 形态）。
- `v0.2.0` 已完成 iOS 首页 UI/UX 改造。
- `v0.3.0` 已完成 Garmin 健康连接器入 Raw。
- `v0.3.1` 已完成健康链路 `raw -> canonical -> domain_health -> mart`。
- `v0.4.0` 已完成并通过验收（Web + 账号体系 + RBAC + 系统数据源治理）。

### 1.2 v0.4.0 核心目标
1. 新增 **Web 客户端**（React），并纳入 Docker 一键启动体系。
2. 实现账号体系闭环：`邮箱 + 密码` 的注册/登录。
3. 首次登录后，强制进入个人基本信息维护流程。
4. 登录后提供后台式管理页面：8 个系统主模块 + 子模块导航。
5. 支持维护每个系统的可选连接器，并选择核心数据源（每系统唯一）。
6. 支持针对核心连接器配置自动同步频率。
7. 支持手动选择回填时间并触发单次同步任务。
8. 实现 RBAC（基于角色的访问控制）。
9. 增加“开发环境历史数据清空”一次性任务，避免旧结构数据影响联调与验收。
10. 本版本开发完成后，通过客户端“手动同步（单次回填）”恢复开发环境数据，不做自动历史迁移。
11. 基于当前数据现状，仅实现 **健康模块**可用功能；其余 7 个系统模块统一展示 `开发中`。

### 1.3 版本成功标准
- `docker compose up` 后可访问 Web 客户端并完成注册/登录。
- 首次登录用户会被引导到个人资料完善页，保存后才可进入业务页。
- 登录后可见 8 个系统模块入口与统一后台布局。
- 健康模块可完成：连接器配置查看/更新、Domain 数据查询、Mart 数据展示。
- 可在“系统数据源管理”页面维护每系统可选连接器并设置核心数据源（当前仅 `health/garmin_connect` 可选）。
- 可针对核心连接器设置自动同步频率（如每 60 分钟），并生效到调度层。
- 可手动提交“回填时间范围”触发单次同步（`job_type=backfill_once`），并可查看任务状态。
- RBAC 生效：不同角色对页面与接口权限隔离正确。

---

## 2. 范围与非目标

### 2.1 In Scope
1. `apps/web` React Web 客户端工程初始化与页面实现。
2. Web 客户端 Docker 化并接入现有 `infra/docker/docker-compose.yml`。
3. 后端新增鉴权能力（注册/登录/刷新/登出/当前用户信息）。
4. 首次登录个人资料维护流程。
5. 登录后后台主框架（顶部栏 + 左侧系统导航 + 主内容区）。
6. 系统连接器与核心数据源管理（8 系统统一入口）。
7. 核心连接器自动同步频率配置与生效。
8. 手动回填时间范围单次同步（One-off backfill sync）。
9. RBAC（角色、权限、接口鉴权、前端路由鉴权）。
10. 开发环境历史数据清空任务（一次性）。
11. 健康模块 MVP 子模块：
   - 连接器配置（Connector Config）
   - Domain 数据查询（Domain Query）
   - Mart 数据展示（Mart View）
12. 其他 7 个系统模块占位页（开发中）。

### 2.2 Out of Scope
1. 移动端客户端功能开发（本版本后置）。
2. 第三方登录（微信/Apple/Google/SSO）。
3. 邮箱验证码、找回密码。
4. 字段级/行级细粒度数据权限（本版仅到角色级接口权限）。
5. 新数据源接入或 dbt 模型大改（沿用 v0.3.1 数据底座）。
6. 7 个非健康系统的真实业务页面开发。

### 2.3 版本边界约束
1. 本版本业务数据查询以健康系统为唯一可用系统。
2. 7 个占位系统必须可见、可点击，但统一展示 `开发中`。
3. 文档中所有接口、页面命名必须避免 `poc_signal` 旧口径。
4. 每个系统只能配置一个核心数据源。
5. 仅允许对“核心连接器”配置自动同步频率与触发回填单次同步。
6. 因底层数据结构变化，开发环境必须先执行历史数据清空，再开展 v0.4.0 联调。
7. v0.4.0 开发完成后，数据恢复仅通过客户端手动同步功能触发，不走自动迁移。
8. 必须前后端分离：客户端代码放在 `apps/*`；所有后端代码（API/任务/调度/数据服务）放在 `apps` 目录之外，便于后续 iOS/Android 复用。
9. 自动同步频率的唯一配置入口为 `system-sources/sync-policy`，不得与连接器配置页面重复配置。

---

## 3. 总体架构（Web-first）

```text
Browser
  -> web-client (React + Semi Design)
  -> api-service (FastAPI: auth + profile + rbac + source-config + query)
  -> PostgreSQL (app/raw/canonical/domain_health/mart)
  -> dbt-runner (维持数据转换)
```

### 3.1 架构分工
- Web 客户端：鉴权流程、个人资料流程、RBAC 路由保护、后台页面交互。
- API 服务：鉴权、会话校验、RBAC 判权、系统数据源配置、健康模块查询与配置接口。
- PostgreSQL/dbt：沿用 v0.3.1 作为健康数据事实来源。

### 3.2 与既有架构关系
- 保持 `raw -> canonical -> domain_health -> mart` 数据链路不变。
- v0.4.0 是客户端与权限治理能力新增，不重做数据治理主干。
- iOS 不删除，但本版本不新增其功能。

### 3.3 代码组织约束（跨端复用）
1. 前后端必须物理隔离：
   - 前端代码：`apps/web`（及后续 `apps/ios`、`apps/android`）
   - 后端代码：统一放在 `apps` 目录之外（如 `services/*`、`data/*`、`infra/*`）
2. Web 不得内嵌后端业务实现代码（仅通过 API 调用后端）。
3. 后端能力需以通用 API 形式提供，供 Web、iOS、Android 复用，不做客户端专用分叉实现。

---

## 4. 用户、鉴权、个人资料与 RBAC 模型

## 4.1 账号模型
- 账号唯一标识：`email`（小写规范化）。
- 登录凭据：`email + password`。
- 账号状态：`active / disabled`。
- 新增字段：`profile_completed`（是否完成首次资料维护）。

## 4.2 密码策略
- 长度至少 8 位。
- 必须包含字母与数字。
- 后端只存储哈希值（推荐 `argon2id`，备选 `bcrypt`）。
- 严禁回传或日志打印明文密码。

## 4.3 会话策略
- Access Token（JWT）: 默认 30 分钟。
- Refresh Token: 默认 7 天。
- Web 端默认使用 HttpOnly Cookie 存放 refresh token（推荐）；access token 放内存态。

## 4.4 首次登录个人资料流程
- 注册成功后首次登录，若 `profile_completed=false`，强制跳转 `/app/profile/setup`。
- 资料必填项：
  - `display_name`
  - `timezone`（默认 `Asia/Shanghai`）
  - `gender`（可选）
  - `birth_date`（可选）
  - `height_cm`（可选）
  - `weight_kg`（可选）
- 保存成功后置 `profile_completed=true`，再进入 `/app/health/overview`。

## 4.5 RBAC 模型（v0.4.0）

角色定义：
- `super_admin`：全量权限，含角色分配与系统数据源治理。
- `admin`：业务管理权限（系统数据源、健康配置、健康查询），无角色分配权限。
- `analyst`：健康查询权限（Domain/Mart），无配置修改权限。
- `viewer`：只读查看权限（Mart/基础状态）。

核心权限点（示例）：
- `profile.write`
- `health.connector.write`
- `health.domain.read`
- `health.mart.read`
- `system_source.write`
- `rbac.user_role.write`

RBAC 执行规则：
1. 前端按权限渲染菜单与按钮（隐藏无权限动作）。
2. 后端接口必须二次鉴权，前端隐藏不等于授权。
3. 首个注册用户默认赋予 `super_admin`。

---

## 5. Web 页面信息架构（IA）

## 5.1 路由结构
- `/auth/login`：登录页
- `/auth/register`：注册页
- `/app/profile/setup`：首次登录资料维护页
- `/app`：登录后主框架（重定向到 `/app/health/overview`）
- `/app/system-sources`：系统数据源管理页
- `/app/health/overview`
- `/app/health/connectors`
- `/app/health/domain`
- `/app/health/mart`
- `/app/time`
- `/app/income`
- `/app/finance`
- `/app/ability`
- `/app/relationship`
- `/app/life`
- `/app/security`

## 5.2 登录页
功能要求：
1. 提供邮箱输入、密码输入、登录按钮。
2. 提供“去注册”入口跳转注册页。
3. 提供错误提示区（密码错误/邮箱未注册/服务异常）。

交互规则：
- 邮箱格式非法时不可提交。
- 提交中按钮进入 loading 状态，防重复提交。
- 登录成功后：
  - `profile_completed=false` -> `/app/profile/setup`
  - `profile_completed=true` -> `/app/health/overview`

## 5.3 注册页
功能要求：
1. 提供邮箱、密码、确认密码。
2. 提供“去登录”入口。
3. 注册成功后可自动登录并进入首次资料维护流程。

校验规则：
- 邮箱格式校验。
- 密码强度校验。
- 两次密码一致性校验。
- 邮箱重复返回明确错误信息。

## 5.4 首次资料维护页
功能要求：
1. 展示个人基本信息表单（见 4.4）。
2. 提供保存按钮。
3. 保存成功后跳转业务首页。

交互规则：
- 必填项未填不可提交。
- 提交中不可重复提交。
- 仅 `profile_completed=false` 时展示该页。

## 5.5 登录后后台主框架
布局要求：
1. 左侧导航：8 个系统主模块 + `系统数据源管理`。
2. 顶部栏：当前系统名、用户邮箱、角色、退出登录。
3. 主内容区：展示对应页面。

8 系统模块定义（v0.4.0）：
- 健康 `health`（可用）
- 时间 `time`（开发中）
- 收入 `income`（开发中）
- 财务 `finance`（开发中）
- 能力 `ability`（开发中）
- 关系 `relationship`（开发中）
- 生活 `life`（开发中）
- 保障 `security`（开发中）

## 5.6 健康模块子模块
1. `连接器配置`（`/app/health/connectors`）
- 展示健康连接器关键配置（只读 + 可编辑白名单字段）。
- 支持保存更新。
- 展示最近运行状态（成功/失败、最近执行时间、累计成功/失败）。
- 不承载自动同步频率配置（频率由系统数据源管理页统一维护）。

2. `Domain 数据查询`（`/app/health/domain`）
- 支持按 `account_ref`、日期范围、`metric_name` 查询。
- 至少展示：`metric_date`、`metric_name`、`metric_value_num`、`quality_flag`。
- 支持分页。

3. `Mart 数据展示`（`/app/health/mart`）
- 展示日级概览（`health_daily_overview`）。
- 展示指标汇总（`health_metric_daily_summary`）。
- 展示活动主题聚合（`health_activity_topic_daily`）。

## 5.7 系统数据源管理页（新增）
页面目标：维护每个系统的可选连接器，并指定核心数据源。

展示规则：
1. 8 个系统都展示一行配置。
2. 每个系统显示：可选连接器列表、当前核心数据源、自动同步频率、最后更新时间。
3. 每个系统核心数据源仅允许 1 个。
4. 仅有 `system_source.write` 权限角色可修改。
5. 仅核心连接器支持配置自动同步频率。
6. 支持“手动回填单次同步”入口：选择回填时间范围并触发任务。
7. 支持查看最近同步任务状态（running/success/failed）。

v0.4.0 初始数据：
- `health`：可选连接器 `garmin_connect`（可设为核心）
- 其他 7 系统：暂无可选连接器（显示“暂无可选连接器”）

手动回填单次同步规则：
1. 仅允许对已设置核心连接器的系统触发。
2. 回填时间需为闭区间（`backfill_start_at` 到 `backfill_end_at`）。
3. 同一系统同一时刻仅允许一个运行中回填任务。
4. 回填任务只执行一次，不改变自动同步频率。
5. v0.4.0 开发完成后的首次数据恢复，统一通过该入口手动触发。
6. 本文档中的“手动同步”统一指触发 `job_type=backfill_once` 的单次同步任务。

## 5.8 其他 7 系统占位页规范
- 页面标题显示系统名称。
- 页面主体固定展示：`开发中` + 简短说明（本版本仅开放健康系统）。
- 不发起后端业务查询请求。

---

## 6. API 契约（v0.4.0 新增与复用）

## 6.1 统一响应
成功：
```json
{"status":"ok","data":{}}
```

失败：
```json
{"status":"error","code":"...","message":"...","request_id":"..."}
```

## 6.2 鉴权与个人资料接口

### A. `POST /v1/auth/register`
请求：
```json
{
  "email": "user@example.com",
  "password": "Passw0rd!"
}
```
响应：
```json
{
  "status": "ok",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com"
  }
}
```

### B. `POST /v1/auth/login`
请求：
```json
{
  "email": "user@example.com",
  "password": "Passw0rd!"
}
```
响应：
```json
{
  "status": "ok",
  "data": {
    "access_token": "jwt",
    "expires_in": 1800,
    "profile_completed": false,
    "user": {
      "user_id": "uuid",
      "email": "user@example.com",
      "roles": ["super_admin"]
    }
  }
}
```

### C. `POST /v1/auth/refresh`
- 使用 refresh token 换取新 access token。

### D. `POST /v1/auth/logout`
- 使当前 refresh token 失效。

### E. `GET /v1/auth/me`
- 获取当前登录用户、角色、权限与 `profile_completed`。

### F. `GET /v1/profile/me`
- 获取当前用户个人资料。

### G. `PUT /v1/profile/me`
- 更新当前用户个人资料；首次提交成功后将 `profile_completed=true`。

## 6.3 RBAC 接口

### A. `GET /v1/rbac/me-permissions`
- 返回当前用户权限列表（用于前端菜单与按钮控制）。

### B. `GET /v1/rbac/users`
- 返回用户与角色列表（需要 `rbac.user_role.write`）。

### C. `PUT /v1/rbac/users/{user_id}/roles`
- 更新目标用户角色（需要 `rbac.user_role.write`）。

## 6.4 系统数据源管理接口

### A. `GET /v1/system-sources`
- 返回 8 系统的可选连接器与当前核心数据源。

### B. `PUT /v1/system-sources/{system_code}/core-source`
请求：
```json
{
  "connector_code": "garmin_connect"
}
```
- 设置指定系统核心数据源。
- 约束：`connector_code` 必须在该系统可选连接器名单内。

### C. `PUT /v1/system-sources/{system_code}/connectors/{connector_code}`
请求：
```json
{
  "enabled": true
}
```
- 启用/停用系统可选连接器（当前仅健康系统有实际连接器）。

### D. `GET /v1/system-sources/{system_code}/sync-policy`
- 获取核心连接器同步策略（自动频率配置）。

### E. `PUT /v1/system-sources/{system_code}/sync-policy`
请求：
```json
{
  "auto_sync_enabled": false,
  "auto_sync_interval_minutes": 60
}
```
- 更新核心连接器自动同步策略。
- 约束：
  - `auto_sync_interval_minutes` 建议范围 `15 ~ 1440`。
  - 仅核心连接器可配置。
  - v0.4.0 开发与联调阶段建议默认 `auto_sync_enabled=false`；完成首次手动同步恢复后再按需开启。

### F. `POST /v1/system-sources/{system_code}/sync-jobs`
请求：
```json
{
  "job_type": "backfill_once",
  "backfill_start_at": "2026-02-01T00:00:00+08:00",
  "backfill_end_at": "2026-02-07T23:59:59+08:00"
}
```
- 触发手动回填单次同步任务。
- 说明：本接口即“客户端手动同步”实现入口。
- 约束：
  - `backfill_start_at <= backfill_end_at`
  - 仅核心连接器可触发
  - 有运行中任务时返回冲突错误

### G. `GET /v1/system-sources/{system_code}/sync-jobs`
- 查询该系统最近同步任务列表与状态（含 backfill 任务）。

## 6.5 健康模块接口

### A. `GET /v1/health/connector`
- 复用现有接口，返回运行健康状态。

### B. `GET /v1/health/connectors/config`
- 返回健康连接器配置白名单：
  - `GARMIN_FETCH_WINDOW_DAYS`
  - `GARMIN_BACKFILL_DAYS`
  - `GARMIN_TIMEZONE`
  - `GARMIN_IS_CN`

### C. `PUT /v1/health/connectors/config`
- 更新上述白名单字段（需 `health.connector.write` 权限）。
- 说明：自动同步频率不在此接口维护，统一由 `sync-policy` 接口维护。

### D. `GET /v1/health/domain/metrics`
查询参数：
- `start_date`
- `end_date`
- `metric_name`（可选）
- `account_ref`（可选）
- `page`
- `page_size`

数据来源：`domain_health.health_metric_daily_fact`

### E. `GET /v1/health/mart/overview`
数据来源：`mart.health_daily_overview`

### F. `GET /v1/health/mart/metric-summary`
数据来源：`mart.health_metric_daily_summary`

### G. `GET /v1/health/mart/activity-topics`
数据来源：`mart.health_activity_topic_daily`

---

## 7. 数据库与后端改造要求

## 7.1 新增表（建议）

### A. `app.user_account`
- `user_id uuid pk`
- `email text unique not null`
- `password_hash text not null`
- `status text not null default 'active'`
- `profile_completed boolean not null default false`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

### B. `app.user_profile`
- `user_id uuid pk`
- `display_name text not null`
- `timezone text not null default 'Asia/Shanghai'`
- `gender text`
- `birth_date date`
- `height_cm numeric(6,2)`
- `weight_kg numeric(6,2)`
- `updated_at timestamptz not null default now()`

### C. `app.user_session`
- `session_id uuid pk`
- `user_id uuid not null`
- `refresh_token_hash text not null`
- `expires_at timestamptz not null`
- `revoked_at timestamptz`
- `created_at timestamptz not null default now()`

### D. RBAC 相关表
- `app.rbac_role`
- `app.rbac_permission`
- `app.rbac_role_permission`
- `app.rbac_user_role`

### E. 系统数据源相关表
- `app.system_connector_option`
  - `system_code` / `connector_code` / `enabled` / `display_name` / `updated_at`
- `app.system_core_source`
  - `system_code` / `connector_code` / `auto_sync_enabled` / `auto_sync_interval_minutes` / `updated_by` / `updated_at`
- `app.connector_sync_job`
  - `job_id` / `system_code` / `connector_code` / `job_type` / `backfill_start_at` / `backfill_end_at` / `status` / `triggered_by` / `triggered_at` / `finished_at` / `error_message`

约束要求：
1. `app.system_core_source.system_code` 唯一（每系统仅一个核心数据源）。
2. 核心数据源必须来自该系统已启用连接器。
3. 自动同步频率仅作用于核心连接器。
4. 回填单次同步任务必须记录触发人与时间范围。
5. 回填任务时间范围必须满足 `backfill_start_at <= backfill_end_at`。

## 7.2 开发环境历史数据清空任务（新增）

触发时机：
1. v0.4.0 开发启动前执行一次。
2. 如开发期间再次发生破坏性结构调整，可再次执行并记录。

清空范围（开发环境）：
1. `raw` / `canonical` / `domain_health` / `mart` 下业务数据表。
2. `annotation.annotation`。
3. `app.request_audit`、`app.connector_health`、`app.connector_sync_job`。

保留范围（开发环境）：
1. 鉴权与权限基础配置（如 `app.user_account`、`app.rbac_*`）可按联调需要保留。
2. 系统连接器基础配置（`app.system_connector_option`、`app.system_core_source`）建议保留。

执行方式（建议）：
1. 提供 `scripts/dev/reset_dev_data_v0_4_0.sql` 或等价脚本。
2. 采用可审计方式执行（记录执行人、时间、目标环境）。

执行后校验：
1. 目标业务表计数为 `0`。
2. 健康查询接口返回空集合而非错误。
3. 客户端可通过手动同步功能重新拉起数据。

## 7.3 安全与权限要求
1. `email` 入库前统一小写与 trim。
2. `password_hash` 使用强哈希，不可逆。
3. 鉴权相关错误日志不得输出密码、token 原文。
4. API 需加基础限流（至少对登录/注册接口）。
5. 所有业务接口必须执行 RBAC 权限校验。

## 7.4 兼容性要求
- 保留现有健康接入接口：`POST /v1/ingest/connector-health`。
- 不破坏现有 v0.3.1 验收链路与数据模型。

---

## 8. Web 客户端实现要求（React）

## 8.1 技术栈建议（落地优先）
- React + TypeScript
- Vite
- React Router
- TanStack Query（服务端状态）
- 组件库：**Semi Design（必选）**，参考: [Semi Design 中文文档](https://semi.design/zh-CN/)

## 8.2 建议目录结构
```text
apps/web/
  src/
    app/
    pages/
      auth/
      profile/
      dashboard/
      health/
      system-sources/
      placeholder/
    components/
    services/
    store/
    types/
    routes/
```

后端目录约束（必须）：
```text
services/        # API、任务、调度、共享后端逻辑
data/            # dbt 与数据建模
infra/           # docker 与部署编排
```
说明：后端代码不得放在 `apps/` 下，确保后续 iOS/Android 复用同一后端能力。

## 8.3 页面实现清单
1. `LoginPage`
2. `RegisterPage`
3. `ProfileSetupPage`
4. `AppLayout`（侧边导航 + 顶栏）
5. `SystemSourceManagementPage`
6. `HealthConnectorConfigPage`
7. `HealthDomainQueryPage`
8. `HealthMartPage`
9. `ComingSoonPage`（复用 7 个非健康系统）

## 8.4 可用性要求
- 桌面端宽度 `>= 1280px` 体验优先。
- 平板宽度 `>= 768px` 可正常使用。
- 首屏渲染不出现白屏闪烁与布局抖动。
- Semi Design 主题令牌（色彩/间距/字体）需与 UI 规范统一。

---

## 9. Docker 与部署要求

## 9.1 新增服务
在 `infra/docker/docker-compose.yml` 新增 `web-client` 服务：
- 构建目录：`apps/web`
- 暴露端口：默认 `3000`
- 环境变量：`WEB_API_BASE_URL=http://localhost:8000`
- 依赖：`api-service` healthy 后启动

## 9.2 推荐启动命令
```bash
cd /Users/fangyongchao/Projects/on_the_way
cp infra/docker/.env.example infra/docker/.env

docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build
```

## 9.3 环境变量新增（建议）
| 变量名 | 默认值 | 说明 |
|---|---|---|
| `WEB_PORT` | `3000` | Web 服务端口 |
| `WEB_API_BASE_URL` | `http://localhost:8000` | Web 调用 API 基地址 |
| `AUTH_JWT_SECRET` | 无 | JWT 签名密钥（必填） |
| `AUTH_ACCESS_EXPIRES_MINUTES` | `30` | Access token 过期分钟 |
| `AUTH_REFRESH_EXPIRES_DAYS` | `7` | Refresh token 过期天数 |

---

## 10. 验收标准（v0.4.0）

## 10.1 功能验收
1. 注册成功后可登录。
2. 首次登录必须进入资料维护页，保存后才能进入业务页。
3. 登录成功后进入后台首页，显示 8 个系统模块。
4. 健康模块三个子模块均可访问并返回真实数据。
5. 系统数据源管理页可展示 8 系统数据源状态，并可设置健康核心数据源为 `garmin_connect`。
6. 可配置健康核心连接器自动同步频率，并在刷新后保持一致。
7. 可手动选择回填时间范围并触发单次同步，任务状态可查询。
8. 其他 7 模块显示 `开发中` 且不报错。
9. 未登录访问业务页会被重定向到登录页。
10. 开发环境历史数据清空任务已执行且校验通过。
11. v0.4.0 开发完成后，可通过客户端手动同步恢复开发环境数据。
12. 仓库结构符合前后端分离约束：后端代码未进入 `apps/` 目录。
13. 开发与联调阶段默认关闭自动同步（`auto_sync_enabled=false`），避免与“手动恢复数据”策略冲突。

## 10.2 接口验收
- `POST /v1/auth/register`、`/login`、`/refresh`、`/logout`、`/me` 全部可用。
- `GET/PUT /v1/profile/me` 可用。
- `GET /v1/system-sources` 与核心数据源设置接口可用。
- 同步策略接口 `GET/PUT /v1/system-sources/{system_code}/sync-policy` 可用。
- 单次回填接口 `POST /v1/system-sources/{system_code}/sync-jobs` 与任务查询接口可用。
- 健康查询接口在有数据时返回非空，在无数据时返回空集合而非 5xx。

## 10.3 RBAC 验收
- 不同角色登录后菜单可见项符合权限。
- 无权限用户调用受限接口返回 `403`。
- 角色变更后权限即时生效（新 token 周期内）。

## 10.4 安全验收
- 数据库中不存在明文密码。
- 日志中不存在密码与 token 明文。
- 登出后 refresh token 不可继续使用。

## 10.5 运行验收
- `docker compose up` 后 Web 与 API 可联通。
- 浏览器访问 Web 地址可完成“注册 -> 登录 -> 完善资料 -> 健康页面”闭环。
- 在已清空历史数据的开发环境中，手动触发同步后可恢复健康链路展示数据。

---

## 11. 任务拆分建议（可直接排期）

## 11.1 UI/UX
1. 登录/注册/资料维护页面视觉稿（桌面优先）。
2. 后台主框架与导航规范。
3. 健康模块三子页的信息层级与组件规范。
4. 系统数据源管理页交互规范（含自动同步频率配置）。
5. 回填时间选择与单次同步任务反馈交互规范。
6. 基于 Semi Design 的设计令牌与组件规范。

## 11.2 前端
1. 初始化 `apps/web` 与路由框架。
2. 集成 Semi Design 并落地基础布局组件。
3. 实现鉴权页面与会话管理。
4. 实现首次资料维护流程。
5. 实现 RBAC 路由与按钮级权限控制。
6. 实现系统数据源管理页面。
7. 实现核心连接器自动同步频率配置交互。
8. 实现回填时间选择与单次同步任务触发/状态查询交互。
9. 实现健康模块 3 个子模块页面。
10. 实现 7 模块占位页。
11. 对接 Docker 运行与环境变量。

## 11.3 后端
1. 落地 `auth/profile` 数据模型与接口。
2. 落地 RBAC 表结构、权限校验中间件与角色分配接口。
3. 落地系统数据源管理接口与约束。
4. 落地核心连接器自动同步策略接口与调度生效机制。
5. 落地回填时间范围单次同步任务接口与任务状态管理。
6. 新增健康模块查询与配置接口。
7. 交付开发环境历史数据清空脚本与执行说明。
8. 编写接口测试与错误码规范。
9. 自检并保证所有后端增量代码位于 `apps` 目录之外。

## 11.4 数据研发
1. 校验 `domain_health` 与 `mart` 在查询场景下索引与性能。
2. 提供健康页面查询所需字段口径说明。
3. 输出必要的查询视图或 SQL 优化建议。

## 11.5 测试
1. 登录注册流程测试（正/逆向）。
2. 首次资料维护流程测试。
3. RBAC 权限矩阵测试（页面 + 接口）。
4. 系统数据源配置与核心源切换测试。
5. 自动同步频率生效测试（调度周期变更）。
6. 回填时间范围单次同步任务测试（提交、运行、完成/失败）。
7. 开发环境历史数据清空任务测试（清空范围与校验 SQL）。
8. 开发完成后客户端手动同步恢复数据测试。
9. 健康模块数据正确性与空数据处理测试。
10. Docker 一键启动与回归测试。

---

## 12. 默认假设与待确认项

为避免阻塞研发，v0.4.0 先采用以下默认假设：
1. 不做邮箱验证码激活。
2. 不做找回密码。
3. 首个注册用户自动授予 `super_admin`。
4. v0.4.0 预置 8 系统编码，连接器初始仅 `health/garmin_connect` 可用。
5. 当开启自动同步时，核心连接器默认频率为 `60` 分钟。
6. 单次回填时间范围默认上限为 `30` 天（可在后续版本调整）。
7. 开发环境在 v0.4.0 开发前已完成一次历史数据清空。
8. 开发完成后的数据恢复由客户端手动同步触发。
9. v0.4.0 开发与联调阶段 `auto_sync_enabled` 默认 `false`；如需开启自动同步，由 `super_admin` 在首次手动恢复后操作。

建议产品负责人确认以下问题（不影响先行开发）：
1. v0.5.0 是否引入邮箱验证码与找回密码。
2. RBAC 角色命名与权限矩阵是否需要进一步细化。
3. 非健康模块优先落地顺序（时间/收入/财务等）。
4. 自动同步频率允许区间是否调整（当前建议 `15~1440` 分钟）。
5. 单次回填最大时间范围是否调整（当前默认 `30` 天）。
6. Web 是否需要多语言（当前默认中文）。

---

## 13. 关联文档
- 框架文档：`docs/frame/frame_v1.1.md`
- 产品历史版本：`docs/product/product_v0.3.1.md`
- API 历史版本：`docs/api/api_v0.3.1.md`
- 运行与验收历史：`docs/run/交付物启动与验收说明_v0.3.1.md`

---

## 14. 验收结论（2026-03-02）

- 验收结论：`通过`
- 核心结论：
  1. Web 端“注册 -> 登录 -> 首次资料维护 -> 业务页”闭环通过。
  2. 系统数据源管理、核心源设置、同步策略、单次回填任务链路通过。
  3. 健康模块连接器配置、Domain 查询、Mart 展示通过。
  4. RBAC 生效（无权限写操作返回 `403`，有权限账号可完成管理动作）。
  5. Docker 一键启动与 `scripts/dev/verify_v0_4_0.sh` 验收脚本通过。
