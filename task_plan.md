# Task Plan: on_the_way v0.3.0 Implementation

## Goal
完成 `v0.3.0` 后端开发落地：新增健康连接器 API 契约实现、接入 Garmin 真实拉取逻辑（含容错/重试/配置）、更新运行配置与文档状态，并完成最小可执行校验。

## Current Phase
Completed

## Phases

### Phase 1: Gap Review
- [x] 对照 `docs/product/product_v0.3.0.md` 与当前代码识别缺口
- [x] 确认 API schema、路由、connector 运行配置改造点
- [x] 形成开发顺序与回归边界（v0.1.0 不破坏）
- **Status:** complete

### Phase 2: API Service Implementation
- [x] 新增健康连接器请求 schema 与校验
- [x] 新增 `POST /v1/ingest/connector-health` 路由
- [x] 复用既有入库能力并确保审计与错误处理一致
- **Status:** complete

### Phase 3: Connector Worker Implementation
- [x] 引入 `garminconnect` 依赖与配置项
- [x] 实现 Garmin 登录、数据集映射、日期窗口拉取
- [x] 实现容错策略（单项失败不中断、重试、health 回写）
- **Status:** complete

### Phase 4: Infra & Docs Alignment
- [x] 更新 compose 与环境变量映射
- [x] 同步 README / runbook 的“已实现”状态与运行说明
- [x] 若实现与文档契约冲突，征求用户确认后修订文档
- **Status:** complete

### Phase 5: Verification & Delivery
- [x] 执行语法/类型/单元级检查
- [x] 执行最小回归检查（至少 API 基础健康与旧接口可用）
- [x] 输出差异总结、风险与下一步建议
- **Status:** complete

### Phase 6: Final Cleanup & Docs Polish
- [x] 清理无效配置路径（死代码）
- [x] 修订 v0.3.0 产品/API/运行文档为最终口径
- [x] 执行最终编译与 compose 配置检查
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 延续单表 Raw 入库模型（`raw.raw_event`） | 兼容既有 ingest 幂等实现，降低迁移风险。 |
| Garmin 指标按 `metric_type` 契约驱动 | 避免强耦合 SDK 方法名，适配库版本差异。 |
| 连接器必须默认失败可观测 | 通过 `app.connector_health` 持续记录运行状态。 |
| Garmin 中国区账号使用 `GARMIN_IS_CN=true` | 实测 `is_cn=false` 会返回心率结构但关键值全空，`is_cn=true` 可拿到真实最近 7 日心率。 |
| v0.3.0 时间存储统一东8区 | 满足用户要求，避免 Raw/健康检查接口出现 UTC 与东8区混用。 |

## Open Questions for User Confirmation
| Question | Current Assumption |
|----------|--------------------|
| 缺少 Garmin 凭据时是否允许连接器进入“空转+告警”而非进程退出 | 默认允许空转并持续上报 error，方便本地开发不阻塞。 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `PYTHONPATH=services/api python3 -c 'from app.main import app'` 报 `ModuleNotFoundError: fastapi` | 1 | 当前宿主环境未安装 API 依赖；改为执行 `compileall` 与 schema 级校验，完整联调留给容器环境。 |
| 宿主侧 `curl http://localhost:8000` 持续 `connection refused` | 1 | 使用 `docker compose exec -T api-service` 在容器网络内执行 API 回归请求，验证接口行为。 |
| SQL 校验 `jsonb_array_length` 报 `cannot get array length of a scalar` | 1 | 先用 `jsonb_typeof` 判型，再仅对 array 分支计算长度。 |
| Docker 命令偶发 `permission denied ... docker.sock` | 1 | 改用提权执行 `require_escalated` 完成容器内健康与 SQL 校验。 |
