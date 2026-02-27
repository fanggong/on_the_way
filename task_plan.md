# Task Plan: on_the_way v0.3.1 Implementation

## Goal
基于 `docs/product/product_v0.3.1.md` 完成完整落地开发：
- 健康链路 `raw -> canonical -> domain_health -> mart` 建模
- POC (`poc_signal`) 代码与数据库对象退役
- 表/字段注释与 OpenMetadata 采集范围改造
- 文档同步到 `v0.3.1` 可验收状态

## Current Phase
Completed (Closure Finished)

## Phases

### Phase 1: Gap Analysis & Design Lock
- [x] 对齐 `product_v0.3.1` 与当前代码差距
- [x] 识别 POC 遗留点（API/dbt/iOS/DB/OpenMetadata）
- [x] 确定实施顺序与默认假设（annotation 保留并改面向 health）
- **Status:** complete

### Phase 2: Data Layer Implementation
- [x] 新增 health Canonical 模型（event/metric/activity）
- [x] 新增 health Domain 模型（metric/activity fact）
- [x] 新增 health Mart 模型（daily summary/overview/activity topic）
- [x] 删除 POC dbt 模型、测试与项目配置
- [x] 补齐 dbt `schema.yml` 描述并启用 `persist_docs`
- **Status:** complete

### Phase 3: API / DB / iOS Cleanup
- [x] 下线 POC ingest/query API
- [x] annotation 从 `signal_event` 切换到 health 目标
- [x] 数据库初始化 SQL 执行 POC 退役清理并补 COMMENT
- [x] iOS 删除调试入口与 POC 页面/调用
- **Status:** complete

### Phase 4: Metadata & Docs Alignment
- [x] OpenMetadata ingestion schema 白名单更新
- [x] 新增/更新 v0.3.1 API 与运行验收文档
- [x] README / 模块 README 状态与范围同步
- **Status:** complete

### Phase 5: Verification
- [x] Python 代码编译检查
- [x] iOS lint/test/type-check（可执行时）
- [x] dbt 配置静态检查（可执行时）
- [x] 产出变更总结与后续风险
- **Status:** complete

### Phase 6: Version Closure
- [x] 清理本版本确认死代码（未使用配置字段）
- [x] 文档状态统一为已验收完成
- [x] 收尾记录补齐（含 OpenMetadata 遗留元数据清理结果）
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 优先做 dbt + API/DB 的“退役与替换” | POC 删除会影响接口、注释、OpenMetadata 范围，需要一体化改造。 |
| annotation 不下线，切换到 health 目标对象 | 保留框架中“人工标注”能力，避免接口成为死功能。 |
| iOS 仅保留 v0.2.0 首页 | 符合 v0.3.1 “删除 POC 调试能力”要求。 |

## Open Questions for User Confirmation
| Question | Current Assumption |
|----------|--------------------|
| None | - |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| None | - | - |
