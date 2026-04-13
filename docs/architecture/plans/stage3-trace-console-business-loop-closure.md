# Stage3 Trace Console Business Loop Closure 实施方案

## 1. 背景

Stage3 Trace Console 已完成 Trace List、Trace Detail、Task Detail 与 Observability Dashboard 的主要页面建设，前端也已完成认证与权限骨架冻结。当前控制台已经具备 Trace / Task 的基础查看、跳转与观测能力，但 Alert 仍主要散落在 Trace Detail 与 Observability 中，尚未形成独立页面入口。

下一阶段不应继续把所有入口和告警信息堆叠到 Observability 页面，而应补齐 Trace / Task / Alert 控制台业务闭环，先冻结页面地图、入口边界、跳转关系与容错策略，再进入具体页面实现。

## 2. 当前现状

当前仓库真实状态：

- `frontend/trace-console` 前端工程已建立，并已形成 React + TypeScript + Vite 控制台工程。
- `/console/traces` Trace List 已完成。
- `/console/traces/:traceId` Trace Detail 已完成。
- `/console/tasks/:taskId` Task Detail 已完成。
- `/console/observability` Observability 已完成基础版与 advanced，已接入 operations overview、trace stats、alert stats 等能力。
- Alert 当前仍主要散落在 Trace Detail / Observability 中，例如 Trace Detail 的 alert 面板、Observability 的 recent alerts 与 alert stats。
- 当前缺少独立 Alert Center 页面。
- 当前 Trace / Task / Alert 页面关系与容错边界尚未冻结。
- 当前认证与权限骨架已冻结，不应在本线程中继续扩展认证、权限或 SSO。

## 3. 本线程目标

补齐 Trace / Task / Alert 控制台业务闭环，冻结页面地图、入口边界、跳转关系与容错策略。

## 4. 当前已完成项

- Trace List 页面已完成，支持 trace 列表查看、筛选、分页与进入 Trace Detail。
- Trace Detail 页面已完成，支持 overview、timeline、console logs、alerts、graph 简版结构展示。
- Task Detail 页面已完成，支持 Task Overview、Task Status、Task Events 与 Related Trace 跳转。
- Observability Dashboard 已完成基础版与 advanced，包含 KPI、任务状态、近期活动、告警摘要、route stats、trace traffic stats、alert stats 等模块。
- Trace -> Task -> Trace 双向跳转闭环已完成。
- 前端认证与权限骨架已完成并冻结，包括 `AuthProvider`、`RequireAuth`、`usePermission`、菜单权限过滤、路由权限控制。

## 5. 当前未完成项

- 缺少独立 `/console/alerts` Alert Center 页面。
- 缺少 Alert List / Alert Center 入口边界定义。
- Trace / Alert 之间的跳转规则尚未冻结。
- Task / Alert 是否存在直接关联入口尚未冻结。
- Observability 中 Alert 信息与未来 Alert Center 的职责边界尚未冻结。
- trace 缺失、task 缺失、alert 关联 trace 缺失等容错策略尚未统一。
- Alert 相关状态页、空态、错误态、无权限态尚未统一。

## 6. 范围边界

### 做什么

- 冻结 Trace / Task / Alert 页面地图。
- 新增独立页面规划：`/console/alerts`。
- 明确 Alert Center MVP 契约。
- 明确 Trace / Task / Alert 跳转关系。
- 明确缺失数据与无权限的前端容错策略。
- 明确前端工程落位方案与实施顺序。

### 不做什么

- 不改认证与权限骨架。
- 不做 SSO。
- 不做 panel-level 权限。
- 不做动态菜单。
- 不引入复杂图表。
- 不做自动刷新。
- 不新增后端接口。
- 不改数据库结构。
- 不重构现有 Trace / Task / Observability 页面。
- 不做按钮级权限。

## 7. 页面地图设计

本线程冻结后的控制台页面地图：

```text
/console/observability
  - 控制台运行态总览
  - 提供 recent tasks / recent alerts / route stats / trace stats 的概览入口
  - 不承载完整 Alert 管理职责

/console/traces
  - Trace List
  - 进入 /console/traces/:traceId

/console/traces/:traceId
  - Trace Detail
  - 展示 trace overview / timeline / console logs / alerts / graph
  - 可跳转到相关 task
  - 可跳转到相关 alert 或 Alert Center 过滤视图

/console/tasks/:taskId
  - Task Detail
  - 展示 task overview / status / events / related trace
  - 可跳回相关 trace

/console/alerts
  - Alert Center MVP
  - 展示 alert 列表与基础筛选
  - 可跳转到关联 trace
```

## 8. 页面职责边界

### Observability

职责：

- 展示全局运行态总览。
- 展示近期任务、近期告警与统计摘要。
- 提供进入 Trace、Task、Alert 相关页面的入口。

不负责：

- 不承载完整告警列表。
- 不承载告警详情深度分析。
- 不承载复杂筛选与分页。

### Trace List

职责：

- 提供 trace 列表、筛选、分页。
- 支持进入 Trace Detail。

不负责：

- 不展示完整任务事件详情。
- 不展示完整告警中心能力。

### Trace Detail

职责：

- 展示单条 trace 的核心详情。
- 展示与 trace 关联的 alerts。
- 支持跳转到 Task Detail。
- 支持跳转到 Alert Center 或后续 Alert Detail。

不负责：

- 不承载 alert 全局列表。
- 不承载 task 全量管理。

### Task Detail

职责：

- 展示单个 task 的概要、状态、事件和 related trace。
- 支持跳回 Trace Detail。

不负责：

- 不承载 alert 全局能力。
- 不承载 task 列表管理。

### Alert Center

职责：

- 展示告警列表。
- 支持基础筛选。
- 支持跳转到关联 trace。
- 与 Observability 的 recent alerts 形成入口衔接。

不负责：

- 不做复杂图表。
- 不做自动刷新。
- 不做告警处理工作流。
- 不做告警规则配置。

## 9. 跳转关系设计

MVP 跳转关系：

```text
Observability -> Trace Detail
Observability -> Task Detail
Observability -> Alert Center

Trace List -> Trace Detail

Trace Detail -> Task Detail
Trace Detail -> Alert Center

Task Detail -> Trace Detail

Alert Center -> Trace Detail
```

跳转规则：

- 如果 `trace_id` 存在，跳转 `/console/traces/:traceId`。
- 如果 `task_id` 存在，跳转 `/console/tasks/:taskId`。
- 如果 alert 只有 `trace_id`，优先跳转 Trace Detail。
- 如果 alert 没有关联 trace，则展示不可跳转状态，不生成无效链接。
- 如果跳转后的 trace 不存在，Trace Detail 应展示稳定错误态，而不是空白页。

## 10. Alert Center MVP 契约

新增页面：

```text
/console/alerts
```

MVP 页面能力：

- 展示告警列表。
- 展示告警基础字段：`alert_id`、`severity`、`source_type`、`source_name`、`event_code`、`message`、`trace_id`、`created_at`。
- 支持基础筛选：`severity`、`source_type`、`trace_id`。
- 支持分页：`limit`、`offset` 或沿用后端当前 alert list 查询参数。
- 支持跳转到关联 Trace Detail。
- 支持 loading / empty / error / no permission。

接口依赖：

- 优先复用现有 `GET /alerts`。
- 不新增后端接口。
- 不新增 Alert Detail 页面。

权限口径：

- Alert Center 页面核心权限建议为 `alert.read`。
- 本线程不修改认证权限骨架，但实现 Alert Center 时应同步评估 `PERMISSIONS`、`ROUTE_PERMISSION_MAP` 与菜单 `permissionCodes` 的最小增量。

## 11. 状态与容错规范

### Loading

- 页面初次加载使用现有状态展示组件或当前页面一致的 loading 文案。
- 不新增复杂骨架屏。

### Empty

- Alert Center 无告警时展示空态，说明当前没有匹配告警。
- Trace / Task 缺少关联数据时不展示无效跳转链接。

### Error

- 接口失败时展示稳定错误态，并提供重试入口。
- 不直接暴露后端异常堆栈。

### No Permission

- 401 / 403 维持现有无权限处理口径。
- 本线程不新增完整 403 页面。

### Missing Trace

- alert 或 route stats 指向的 `trace_id` 可能在 Trace Viewer 中返回 404。
- 前端应展示“关联 Trace 不可用或已缺失”的可理解提示。
- 不应让用户停留在空白页面。

### Missing Task

- Task Detail 如果查不到 task，应展示稳定错误态。
- Trace Detail 中如果没有 linked task，不展示无效 Task 跳转。

### Missing Alert Link

- 如果 alert 没有 `trace_id`，Alert Center 中不生成 Trace 跳转。
- 如果后续有 Alert Detail，再单独定义 alert 自身详情跳转。

## 12. 前端工程落位方案

建议新增或修改位置：

```text
frontend/trace-console/src/pages/alerts/AlertCenterPage.tsx
frontend/trace-console/src/features/trace-console/components/AlertTable.tsx
frontend/trace-console/src/features/trace-console/components/AlertFilterBar.tsx
frontend/trace-console/src/features/trace-console/components/AlertPagination.tsx
frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts
frontend/trace-console/src/features/trace-console/types/traceConsole.ts
frontend/trace-console/src/app/router.tsx
frontend/trace-console/src/config/navigation.config.ts
frontend/trace-console/src/features/auth/permissions.ts
```

落位原则：

- 页面容器放在 `pages/alerts/`。
- Alert 领域展示组件继续放在 `features/trace-console/components/`。
- API 与 DTO 继续复用 `traceConsoleApi.ts` 与 `traceConsole.ts`。
- 只做最小路由与菜单增量，不重构 router。
- 不改认证与权限骨架，只按既有契约增量补充 Alert Center 所需权限映射。

## 13. 实施步骤

首个子任务：

```text
trace-console-page-map-and-alert-center-contract
```

推荐工程实施顺序：

1. 冻结页面地图与 Alert Center 契约。
2. 补充 Alert DTO 与 `GET /alerts` 前端 API 封装。
3. 新增 `/console/alerts` 页面骨架。
4. 新增 Alert Filter / Table / Pagination 最小组件。
5. 接入 Alert Center loading / empty / error / no permission。
6. 接入 Alert -> Trace Detail 跳转。
7. 在 Observability / Trace Detail 中补充进入 Alert Center 的入口。
8. 最小联调与构建验证。

## 14. 测试计划

构建验证：

```bash
npm run build
```

手工验证：

- `/console/alerts` 可访问。
- Alert Center 能调用 `GET /alerts`。
- 有数据时可展示 alert 列表。
- 无数据时展示 empty。
- 接口失败时展示 error。
- 401 / 403 时展示 no permission 或现有无权限状态。
- 有 `trace_id` 的 alert 可跳转 Trace Detail。
- 无 `trace_id` 的 alert 不生成无效链接。
- Trace Detail 中已有 alerts 不受影响。
- Observability 中 recent alerts 不受影响。

回归验证：

- `/console/traces` 可访问。
- `/console/traces/:traceId` 可访问。
- `/console/tasks/:taskId` 可访问。
- `/console/observability` 可访问。
- Trace -> Task -> Trace 闭环不被破坏。

## 15. 验收标准

- 页面地图已冻结，并明确 Observability / Trace / Task / Alert 职责边界。
- 新增页面 `/console/alerts` 的 MVP 契约清晰。
- Alert Center 可基于现有 `GET /alerts` 落地，不需要新增后端接口。
- Trace / Task / Alert 跳转关系清晰。
- trace 缺失、task 缺失、alert trace 缺失等容错策略明确。
- 不改认证与权限骨架。
- 不做 SSO。
- 不做 panel-level 权限。
- 不做动态菜单。
- 不引入复杂图表。
- 不做自动刷新。

## 16. 下一线程衔接

本线程完成后，建议进入：

```text
stage3-trace-console-alert-center-mvp
```

用于实际实现 `/console/alerts` 页面、Alert 列表、基础筛选、分页与 Alert -> Trace 跳转。

不建议直接进入 panel-level 权限或 SSO，除非页面地图与 Alert Center MVP 已完成验收。
