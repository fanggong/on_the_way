# Task Plan: on_the_way v0.4.0 Implementation

## Goal
基于 `docs/` 中 v0.4.0 相关文档，完成可运行、可验证、可交付的 `v0.4.0` 版本开发；
若开发落地与产品文档冲突，先整理冲突点并向用户确认后再更新文档。

## Current Phase
Phase 4 - Docs & Closure (complete)

## Phases

### Phase 1: Requirement & Gap Analysis
- [x] 读取 `docs/product/product_v0.4.0.md` 与关联 API/run/frame 文档
- [x] 盘点代码现状与文档差距
- [x] 输出可执行实施清单与风险点
- **Status:** complete

### Phase 2: Core Implementation
- [x] 完成 API 鉴权/RBAC/系统数据源/同步任务/健康查询核心改造
- [x] 完成 connector-worker 调度改造（核心策略 + job 队列驱动）
- [x] 完成 Web 客户端 `apps/web` 与 Docker 接入
- [x] 补充必要配置与迁移脚本
- [x] 保持向后兼容边界在文档约束范围内
- **Status:** complete

### Phase 3: Verification
- [x] 运行静态检查与关键测试
- [x] 运行 v0.4.0 关键链路验收命令
- [x] 记录失败项、修复与复验结果
- **Status:** complete

### Phase 4: Docs & Closure
- [x] 同步 README / run / api 等文档到 v0.4.0 现状
- [x] 如与 product 文档冲突，先征求用户确认后修改对应文档
- [x] 形成交付总结与后续建议
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 先锁定 v0.4.0 文档边界，再编码 | 避免在高耦合模块中返工。 |
| 先收敛冲突点再改 product 文档 | 符合“先征求确认”的协作约束。 |

## Open Questions for User Confirmation
| Question | Current Assumption |
|----------|--------------------|
| 当前无 | 先按文档实现，发现冲突后即时提出。 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `web-client` 启动时报 `@douyinfe/semi-ui/dist/css/semi.min.css` 未导出 | 1 | 将 `apps/web/src/main.tsx` 改为导入 `@douyinfe/semi-ui/lib/es/_base/base.css`。 |
| 沙箱内部分 Docker socket 调用被拒绝 | 1 | 按权限流程提权执行关键验收命令。 |
| `verify_v0_4_0.sh` 在非空库中出现 RBAC 403 | 1 | 脚本自动为测试账号授予 `admin` 后重新登录，复验通过。 |
| 需求复核发现连接器配置状态展示与系统源只读体验不完整 | 1 | 增加健康连接器状态展示、放开系统源读接口、补齐前端只读/禁用逻辑。 |
