# 架构规划与实施文档索引

本目录用于存放架构规划、阶段实施方案与结构演进文档。

## 当前文档

- [Stage3 Trace Console Backend Query Contract](./stage3-trace-console-backend-query-contract.md)
  - Stage3 trace console 后端查询契约实施方案
- [Stage3 Trace Console Frontend Pages](./stage3-trace-console-frontend-pages.md)
  - Stage3 trace console 前端页面实施方案，当前重点是 Trace Detail 页面开发
- [Stage3 Trace Console Task Detail Linking](./stage3-trace-console-task-detail-linking.md)
  - Stage3 trace console Task Detail 页面与 Trace -> Task -> Trace 双向跳转闭环实施方案
- [Stage3 Trace Console Observability](./stage3-trace-console-console-observability.md)
  - Stage3 trace console 观测与监控面板实施方案，MVP 第一阶段仅接入 operations overview
- [Stage3 Trace Console Observability Advanced](./stage3-trace-console-observability-advanced.md)
  - Stage3 trace console 高级观测能力实施方案，增量接入 trace stats 与 alert stats
- [企业级完整版目录方案](./企业级完整版目录方案.md)
- [当前底座成熟度评估](./当前底座成熟度评估.md)
- [数据库表设计建议](./数据库表设计建议.md)
- [适合这个项目下一阶段落地的精简目录方案](./适合这个项目下一阶段落地的精简目录方案.md)
- [阶段1的详细开发计划清单](./阶段1的详细开发计划清单.md)

## 使用约定

- 实施类文档优先写清楚目标、范围、接口、文件、步骤、测试与验收标准。
- 同一子线程只保留一份主实施文档，避免同类文档重复分叉。
- 新增或更新实施文档后，应同步更新本索引。
