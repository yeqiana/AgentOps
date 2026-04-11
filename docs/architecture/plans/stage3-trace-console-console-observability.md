# Stage3 Trace Console Observability 实施方案

## 1. 背景

stage3-trace-console 已完成 Trace 列表、Trace Detail、Task Detail 与 Trace -> Task -> Trace 双向跳转闭环。当前前端已经具备从请求链路进入任务链路、再回到请求链路的基础观测路径。

下一步需要在已有 Trace + Task 基础上增加全局运行态视图，用于展示当前任务运行态、任务状态分布、最近任务、最近告警和路由统计，形成 Trace Console 的首版 Observability Dashboard。

## 2. 当前现状

当前仓库已建立前端工程：

- `frontend/trace-console/`

当前前端技术栈已稳定运行：

- React
- TypeScript
- Vite
- React Router

当前已完成页面：

- `/console/traces`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`

当前 Trace 列表页 `/console/traces` 已完成，支持筛选、分页、loading、empty、error、no permission 和 trace_id 跳转详情页。

当前 Trace Detail 页面 `/console/traces/:traceId` 已完成，并已接入：

- `GET /console/traces/{trace_id}/viewer`

Trace Detail 当前已具备：

- overview
- timeline
- console logs
- alerts
- graph 简版结构展示

当前 Task Detail 页面 `/console/tasks/:taskId` 已完成，并已接入：

- `GET /tasks/{task_id}/summary`

当前 Trace -> Task -> Trace 双向跳转闭环已完成：

- Trace Detail Linked Task 可跳转到 Task Detail。
- Task Detail Related Trace 可跳回 Trace Detail。

当前后端已提供以下观测相关接口：

- `GET /operations/overview`
- `GET /traces/stats`
- `GET /alerts/stats`
- `GET /tasks/stats`

本线程 MVP 第一阶段只接入：

- `GET /operations/overview`

## 3. 本线程目标

构建 Trace Console 的观测与监控面板（Observability Dashboard），在已有 Trace + Task 基础上提供全局运行态视图。

## 4. 当前已完成项

- `frontend/trace-console` 前端工程已建立。
- React + TypeScript + Vite 已稳定运行。
- `/console/traces` 列表页已完成。
- `/console/traces/:traceId` Trace Detail 已完成，并完成 viewer 联调。
- `/console/tasks/:taskId` Task Detail 已完成。
- Trace -> Task -> Trace 双向跳转闭环已完成。
- 前端已有通用 HTTP client、`PageStateView`、`StatusBadge`、`LinkButton`。
- 后端已提供 `GET /operations/overview` 聚合接口。
- 后端已提供 `GET /traces/stats`、`GET /alerts/stats`、`GET /tasks/stats`，但本线程 MVP 第一阶段不接入这些扩展接口。

## 5. 当前未完成项

- 尚未新增 `/console/observability` 页面路由。
- 尚未实现 Observability Dashboard 页面容器。
- 尚未封装前端 `getOperationsOverview()`。
- 尚未补齐 `OperationsOverviewResponse` 前端 DTO。
- 尚未展示 runtime 信息。
- 尚未展示 task status 分布。
- 尚未展示 recent tasks。
- 尚未展示 recent alerts。
- 尚未展示 route stats。
- 尚未在 Observability 页面接入 Task / Trace 跳转。

## 6. 范围边界

### 6.1 做什么（MVP 第一阶段）

- 新增 Observability 页面。
- 新增 `/console/observability` 前端路由。
- 接入 `GET /operations/overview`。
- 展示 runtime 信息，包括 active task count 和 workers。
- 展示 task status 分布。
- 展示 recent tasks。
- 展示 recent alerts。
- 展示 route stats。
- 支持 Task / Trace 跳转。
- 复用当前 trace console 的页面状态处理方式。
- 复用当前 trace viewer 与 task detail 的 UI 风格。

### 6.2 不做什么

- 不做成功率计算，成功率依赖后续接入 `GET /traces/stats`。
- 不做耗时统计，当前缺少 duration 聚合。
- 不做图表库，仅用列表和卡片。
- 不做自动刷新。
- 不做 SSE。
- 不做复杂筛选。
- 不做时间范围。
- 不做成本扩展。
- 不做配额扩展。
- 不做权限扩展。
- 不做策略扩展。
- 不新增后端接口。
- 不引入全局状态管理。

## 7. 页面路由设计

新增页面路由：

- `/console/observability`

路由职责：

- 展示 Trace Console 全局观测面板。
- 基于 `GET /operations/overview` 加载首版聚合数据。
- 提供 recent tasks 到 `/console/tasks/:taskId` 的跳转。
- 提供 recent alerts 中 trace_id 到 `/console/traces/:traceId` 的跳转。

现有路由保持不变：

- `/console/traces`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`

## 8. 页面拆分

### 8.1 ObservabilityDashboardPage（页面容器）

建议落位：

- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

职责：

- 读取 dashboard 所需数据。
- 调用 `getOperationsOverview()`。
- 管理 loading、error、no permission、empty、ready 状态。
- 组装 KPI、Task Status、Recent Activity、Alert Summary、Route Stats 模块。

### 8.2 ObservabilityKpiGrid

职责：

- 展示 runtime 总览。
- 展示 active task count。
- 展示 max workers。
- 展示 active task IDs 数量或简版列表。
- 展示 recent tasks 数量。
- 展示 recent alerts 数量。

数据来源：

- `summary.runtime`
- `summary.recent_tasks`
- `summary.recent_alerts`

### 8.3 TaskStatusSummaryPanel

职责：

- 展示任务状态分布。
- 使用列表或卡片展示各 status 的 task_count。

数据来源：

- `summary.task_stats`

### 8.4 RecentActivityPanel

职责：

- 展示 recent tasks。
- 每条 task 支持跳转到 `/console/tasks/:taskId`。
- 如 task 存在 trace_id，可提供跳转到 `/console/traces/:traceId`。

数据来源：

- `summary.recent_tasks`

### 8.5 AlertSummaryPanel

职责：

- 展示 recent alerts。
- 展示 severity、source_type、source_name、event_code、message、created_at。
- 如 alert 存在 trace_id，支持跳转到 `/console/traces/:traceId`。

数据来源：

- `summary.recent_alerts`

### 8.6 RouteStatsPanel

职责：

- 展示 route stats。
- 展示 route_name、route_source、decision_count、last_task_id、last_trace_id、last_decided_at。
- 如 last_task_id 存在，支持跳转到 `/console/tasks/:taskId`。
- 如 last_trace_id 存在，支持跳转到 `/console/traces/:traceId`。

数据来源：

- `summary.route_stats`

## 9. 组件拆分

建议新增组件：

- `frontend/trace-console/src/features/trace-console/components/ObservabilityKpiGrid.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskStatusSummaryPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/RecentActivityPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/AlertSummaryPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/RouteStatsPanel.tsx`

建议复用组件：

- `frontend/trace-console/src/components/PageStateView.tsx`
- `frontend/trace-console/src/components/StatusBadge.tsx`
- `frontend/trace-console/src/components/LinkButton.tsx`

建议复用样式：

- `panel`
- `detail-panel`
- `detail-panel-header`
- `detail-panel-kicker`
- `detail-kv-grid`
- `detail-kv-item`
- `muted-text`
- `button`

如现有样式不足，只允许在 `frontend/trace-console/src/app/styles.css` 中补充少量 observability 页面样式。

## 10. 前端工程落位方案

页面层新增：

- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

路由层修改：

- `frontend/trace-console/src/app/router.tsx`

API 层修改：

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`

类型层修改：

- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

组件层新增：

- `frontend/trace-console/src/features/trace-console/components/ObservabilityKpiGrid.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskStatusSummaryPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/RecentActivityPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/AlertSummaryPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/RouteStatsPanel.tsx`

样式层可选修改：

- `frontend/trace-console/src/app/styles.css`

## 11. 当前接口依赖

### 11.1 MVP 第一阶段（只允许一个接口）

接口：

- `GET /operations/overview`

第一阶段约束：

- 第一阶段禁止同时接 `GET /traces/stats` 和 `GET /alerts/stats`。
- 所有面板数据优先从 `operations/overview` 聚合结果中获取。
- 若某些指标无法从 `operations/overview` 获取，则第一阶段不展示，不在前端推导伪指标。

数据结构：

- `summary.task_stats`
- `summary.runtime`
- `summary.recent_tasks`
- `summary.route_stats`
- `summary.recent_alerts`

MVP 字段清单：

- `summary.runtime.max_workers`
- `summary.runtime.active_task_count`
- `summary.runtime.active_task_ids`
- `summary.task_stats[].status`
- `summary.task_stats[].task_count`
- `summary.task_stats[].last_updated_at`
- `summary.recent_tasks[].id`
- `summary.recent_tasks[].trace_id`
- `summary.recent_tasks[].status`
- `summary.recent_tasks[].route_name`
- `summary.recent_tasks[].route_source`
- `summary.recent_tasks[].review_status`
- `summary.recent_tasks[].updated_at`
- `summary.route_stats[].route_name`
- `summary.route_stats[].route_source`
- `summary.route_stats[].decision_count`
- `summary.route_stats[].last_trace_id`
- `summary.route_stats[].last_task_id`
- `summary.route_stats[].last_decided_at`
- `summary.recent_alerts[].id`
- `summary.recent_alerts[].trace_id`
- `summary.recent_alerts[].source_type`
- `summary.recent_alerts[].source_name`
- `summary.recent_alerts[].severity`
- `summary.recent_alerts[].event_code`
- `summary.recent_alerts[].message`
- `summary.recent_alerts[].created_at`

### 11.2 后续阶段（只作为扩展说明）

后续接口：

- `GET /traces/stats`
- `GET /alerts/stats`
- `GET /tasks/stats`

后续用途：

- `GET /traces/stats`：用于成功率、请求流量、状态码分布、路径/方法维度统计。
- `GET /alerts/stats`：用于告警 severity/source_type 分布统计。
- `GET /tasks/stats`：用于独立刷新任务状态统计，或在 operations overview 之外按 session 扩展统计。

本线程 MVP 第一阶段不接入上述扩展接口。

## 12. 实施步骤

1. API + 类型封装（operations/overview）

完成内容：

- 在 `traceConsoleApi.ts` 增加 `getOperationsOverview()`。
- 在 `traceConsole.ts` 增加 `OperationsOverviewResponse` 及相关 DTO。

可验证结果：

- 前端可通过统一 HTTP client 请求 `GET /operations/overview`。
- TypeScript 能识别 dashboard 所需 DTO。

2. 页面骨架（/console/observability）

完成内容：

- 新增 `ObservabilityDashboardPage`。
- 新增 `/console/observability` 路由。
- 实现 loading、error、no permission、empty、ready 状态。

可验证结果：

- 浏览器可访问 `/console/observability`。
- 接口异常和权限异常有明确状态页。

3. KPI 卡片

完成内容：

- 新增 `ObservabilityKpiGrid`。
- 展示 active task count、max workers、active task IDs、recent task count、recent alert count。

可验证结果：

- KPI 数据来自 `GET /operations/overview`。

4. Task Status Summary

完成内容：

- 新增 `TaskStatusSummaryPanel`。
- 展示 `summary.task_stats`。

可验证结果：

- 各任务状态和数量可正常展示。

5. Recent Activity

完成内容：

- 新增 `RecentActivityPanel`。
- 展示 `summary.recent_tasks`。

可验证结果：

- recent tasks 可展示。
- task_id 可跳转到 `/console/tasks/:taskId`。
- trace_id 可跳转到 `/console/traces/:traceId`。

6. Alert Summary

完成内容：

- 新增 `AlertSummaryPanel`。
- 展示 `summary.recent_alerts`。

可验证结果：

- recent alerts 可展示。
- alert 中 trace_id 可跳转到 `/console/traces/:traceId`。

7. Route Stats

完成内容：

- 新增 `RouteStatsPanel`。
- 展示 `summary.route_stats`。

可验证结果：

- route stats 可展示。
- last_task_id 可跳转到 `/console/tasks/:taskId`。
- last_trace_id 可跳转到 `/console/traces/:traceId`。

8. 跳转接入

完成内容：

- 统一检查 Observability 页面内所有 Task / Trace 链接。
- 确认跳转不破坏已有 Trace -> Task -> Trace 闭环。

可验证结果：

- 从 Observability 页面进入 Task Detail 后可跳回 Trace Detail。
- 从 Observability 页面进入 Trace Detail 后可继续跳转 Task Detail。

## 13. 测试计划

### 13.1 页面是否可访问

验证内容：

- 打开 `/console/observability`。

通过标准：

- 页面正常渲染。
- 路由不影响 `/console/traces`、`/console/traces/:traceId`、`/console/tasks/:taskId`。

### 13.2 operations/overview 是否正常返回

验证内容：

- 页面加载时调用 `GET /operations/overview`。

通过标准：

- 请求路径正确。
- 返回数据可被前端 DTO 正常消费。
- 不额外调用 `GET /traces/stats`、`GET /alerts/stats`、`GET /tasks/stats`。

### 13.3 KPI / recent tasks / alerts / route stats 是否正确渲染

验证内容：

- KPI 展示 runtime。
- Task Status 展示 task_stats。
- Recent Activity 展示 recent_tasks。
- Alert Summary 展示 recent_alerts。
- Route Stats 展示 route_stats。

通过标准：

- 所有模块数据均来自 `operations/overview`。
- 空数据时显示空态，不出现运行时错误。

### 13.4 Task / Trace 跳转是否正常

验证内容：

- recent tasks 跳转到 `/console/tasks/:taskId`。
- recent tasks 或 recent alerts 的 trace_id 跳转到 `/console/traces/:traceId`。
- route stats 的 last_task_id、last_trace_id 可跳转。

通过标准：

- Task / Trace 页面正常打开。
- 已有 Trace -> Task -> Trace 闭环不被破坏。

### 13.5 loading / error / no permission 是否正常

验证内容：

- 请求中显示 loading。
- 接口错误显示 error。
- 401 或 403 显示 no permission。

通过标准：

- 状态页完整。
- 不出现空白页。
- 不出现未捕获异常。

## 14. 验收标准

- `/console/observability` 页面可访问。
- `GET /operations/overview` 联调成功。
- KPI 模块可正常展示。
- Task Status Summary 模块可正常展示。
- Recent Activity 模块可正常展示。
- Alert Summary 模块可正常展示。
- Route Stats 模块可正常展示。
- Task / Trace 跳转正常。
- 跳转不破坏 Trace / Task 闭环。
- loading、error、no permission 状态页完整。
- MVP 第一阶段未接入 `GET /traces/stats`。
- MVP 第一阶段未接入 `GET /alerts/stats`。
- MVP 第一阶段未接入 `GET /tasks/stats`。
- 未新增后端接口。
- 未引入全局状态管理。
- 未引入图表库。

## 15. 下一线程衔接

下一线程：

- `stage3-trace-console-observability-advanced`

衔接目标：

- 后续接入 `GET /traces/stats`、`GET /alerts/stats`。
- 扩展成功率、请求流量、告警分布等高级观测能力。
- 评估是否引入图表化展示、时间范围筛选、自动刷新或更细粒度统计接口。
