# Stage3 Trace Console Task Detail Linking 实施方案

## 1. 背景

stage3-trace-console 已完成前端 trace console 基础页面建设，并完成 Trace Detail viewer 联调。当前 trace 视角已经可以从 `/console/traces` 进入 `/console/traces/:traceId`，并查看 trace overview、timeline、console logs、alerts 和简版 graph。

当前缺口是 task 视角尚未进入 trace console 前端闭环。后端已经提供 `GET /tasks/{task_id}/summary`，可直接支撑 Task Detail MVP。本线程用于补齐 Trace 与 Task 的双向跳转能力。

## 2. 当前现状

当前仓库已建立前端工程：

- `frontend/trace-console/`

当前前端技术栈已落地并稳定运行：

- React
- TypeScript
- Vite
- React Router

当前已存在路由：

- `/`
- `/console/traces`
- `/console/traces/:traceId`

当前关键前端文件：

- `frontend/trace-console/src/app/router.tsx`
- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`
- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`
- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`
- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`
- `frontend/trace-console/src/features/trace-console/components/TraceOverviewPanel.tsx`
- `frontend/trace-console/src/app/styles.css`

当前 Trace 列表页 `/console/traces` 已完成，并支持：

- 筛选栏
- 分页
- loading 状态
- empty 状态
- error 状态
- no permission 状态
- `trace_id` 跳转详情页入口

当前 Trace Detail 页面 `/console/traces/:traceId` 已完成，并已接入 viewer：

- `GET /console/traces/{trace_id}/viewer`

当前 Trace Detail 已具备：

- overview
- timeline
- console logs
- alerts
- graph 简版结构展示

当前尚未实现：

- `/console/tasks/:taskId`
- Task Detail 页面
- Trace Detail 中 Linked Task 到 Task Detail 的跳转
- Task Detail 中 Related Trace 到 Trace Detail 的跳转

后端当前已提供：

- `GET /tasks/{task_id}/summary`

相关后端契约位置：

- `app/presentation/api/app.py`
- `app/presentation/api/schemas.py`

## 3. 本线程目标

实现 Trace -> Task -> Trace 双向跳转闭环。

## 4. 当前已完成项

- `frontend/trace-console` 前端工程已建立。
- React + TypeScript + Vite 已稳定运行。
- `/console/traces` 列表页已完成。
- `/console/traces/:traceId` Trace Detail 已完成。
- Trace Detail 已完成 viewer 接入。
- Trace Detail 已展示 overview、timeline、console logs、alerts、graph 简版。
- 后端已提供 `GET /tasks/{task_id}/summary`。
- 前端已有通用 `PageStateView`、`StatusBadge`、`LinkButton`、HTTP client，可复用到 Task Detail。

## 5. 当前未完成项

- 未新增 `/console/tasks/:taskId` 路由。
- 未实现 Task Detail 页面容器。
- 未实现 Task Overview、Task Status、Task Events、Related Trace 组件。
- 前端 API 层未封装 `getTaskSummary(taskId)`。
- 前端类型层未补齐 `TaskSummaryResponse` 对应 DTO。
- Trace Detail 的 Linked Task 当前仅展示 task 摘要，不支持跳转到 Task Detail。
- Task Detail 尚不能跳回 Related Trace。

## 6. 范围边界

### 6.1 做什么

- 新增 Task Detail 页面。
- 新增 `/console/tasks/:taskId` 前端路由。
- 接入 task summary。
- 从 Trace Detail 跳转 Task。
- 从 Task Detail 跳回 Trace。
- 复用当前 trace viewer 的 UI 风格。
- 复用当前前端本地页面状态管理模式。

### 6.2 不做什么

- 不新增后端接口。
- 不实现任务操作，包括取消和重试。
- 不实现复杂筛选或分页。
- 不做图谱扩展。
- 不做成本扩展。
- 不做权限治理扩展。
- 不做策略扩展。
- 不引入全局状态管理。
- 不引入复杂交互。

## 7. 页面路由设计

新增路由：

- `/console/tasks/:taskId`

路由职责：

- 从 URL 读取 `taskId`。
- 调用 `GET /tasks/{task_id}/summary`。
- 展示 Task Detail MVP。
- 提供 Related Trace 跳转到 `/console/traces/:traceId`。

现有路由保持不变：

- `/console/traces`
- `/console/traces/:traceId`

跳转关系：

- Trace Detail -> Task Detail：`/console/traces/:traceId` 页面中的 Linked Task 跳转到 `/console/tasks/:taskId`。
- Task Detail -> Trace Detail：`/console/tasks/:taskId` 页面中的 Related Trace 跳转到 `/console/traces/:traceId`。

## 8. 页面拆分

### 8.1 TaskDetailPage

页面容器，建议落位：

- `frontend/trace-console/src/pages/tasks/TaskDetailPage.tsx`

职责：

- 读取路由参数 `taskId`。
- 调用 `getTaskSummary(taskId)`。
- 管理页面状态。
- 组装 Task Overview、Task Status、Task Events、Related Trace。
- 提供返回 Trace List 的入口。

页面状态：

- loading
- error
- no permission
- empty 或 not found
- ready

### 8.2 TaskOverview

展示任务基础信息。

建议字段：

- task id
- session id
- turn id
- trace id
- user input
- answer
- created at
- updated at

### 8.3 TaskStatus

展示任务执行与路由状态。

建议字段：

- status
- execution mode
- route name
- route source
- review status
- tool count
- error message

### 8.4 TaskEvents

展示任务事件，数据来自：

- `summary.task_events`

首版展示规则：

- 按接口返回顺序展示。
- 展示 event type、event message、created at。
- `event_payload_json` 只做简版文本展示。
- 不做分页。
- 不做筛选。

### 8.5 RelatedTrace

展示关联 Trace 信息，并提供跳转。

数据来源优先级：

- 优先使用 `summary.trace.trace_id`。
- 如果 `summary.trace` 为空，则使用 `summary.task.trace_id`。

跳转目标：

- `/console/traces/:traceId`

无关联 trace 时：

- 展示无关联 trace 的空态文案。

## 9. 组件拆分

建议新增组件：

- `frontend/trace-console/src/features/trace-console/components/TaskOverview.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskStatus.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskEvents.tsx`
- `frontend/trace-console/src/features/trace-console/components/RelatedTrace.tsx`

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

如现有样式无法覆盖 Task Detail 局部布局，只允许在 `frontend/trace-console/src/app/styles.css` 中补充少量 task detail 样式。

## 10. 前端工程落位方案

页面层新增：

- `frontend/trace-console/src/pages/tasks/TaskDetailPage.tsx`

路由层修改：

- `frontend/trace-console/src/app/router.tsx`

API 层修改：

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`

类型层修改：

- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

组件层新增：

- `frontend/trace-console/src/features/trace-console/components/TaskOverview.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskStatus.tsx`
- `frontend/trace-console/src/features/trace-console/components/TaskEvents.tsx`
- `frontend/trace-console/src/features/trace-console/components/RelatedTrace.tsx`

Trace Detail 跳转接入修改：

- `frontend/trace-console/src/features/trace-console/components/TraceOverviewPanel.tsx`

可选优化：

- `frontend/trace-console/src/features/trace-console/components/TraceTable.tsx`

可选优化说明：

- Trace 列表页 task_id 也可以跳转到 `/console/tasks/:taskId`。
- 本线程核心验收不依赖该优化。
- 若为最小闭环，应优先完成 Trace Detail 中 Linked Task 跳转。

## 11. 当前接口依赖

### 11.1 Task Summary

接口：

- `GET /tasks/{task_id}/summary`

前端调用建议：

- `getTaskSummary(taskId)`

返回结构：

- `summary.task`
- `summary.trace`
- `summary.task_events`
- `summary.tool_results`
- `summary.route_decisions`
- `summary.alerts`

MVP 必用字段：

- `summary.task.id`
- `summary.task.trace_id`
- `summary.task.status`
- `summary.task.session_id`
- `summary.task.turn_id`
- `summary.task.execution_mode`
- `summary.task.route_name`
- `summary.task.route_source`
- `summary.task.review_status`
- `summary.task.tool_count`
- `summary.task.error_message`
- `summary.task.user_input`
- `summary.task.answer`
- `summary.task.created_at`
- `summary.task.updated_at`
- `summary.trace.trace_id`
- `summary.trace.method`
- `summary.trace.path`
- `summary.trace.status_code`
- `summary.task_events`

首版可暂不展示或仅简版展示：

- `summary.tool_results`
- `summary.route_decisions`
- `summary.alerts`

### 11.2 Trace Viewer

接口：

- `GET /console/traces/{trace_id}/viewer`

本线程不修改该接口。

本线程只在 Trace Detail 的 Linked Task UI 中使用 viewer 已返回的 `summary.task.id` 生成跳转。

## 12. 实施步骤

1. API + 类型

完成内容：

- 在 `traceConsoleApi.ts` 增加 `getTaskSummary(taskId)`。
- 在 `traceConsole.ts` 增加 `TaskSummaryResponse`、`TaskSummary`、完整 `TaskPayload` 等类型。

可验证结果：

- 前端可以通过统一 HTTP client 请求 `/tasks/{task_id}/summary`。
- TypeScript 能识别 Task Detail 所需 DTO。

2. 页面骨架

完成内容：

- 新增 `TaskDetailPage.tsx`。
- 读取 `taskId`。
- 接入 `getTaskSummary(taskId)`。
- 实现 loading、error、no permission、empty 基础状态。

可验证结果：

- `/console/tasks/:taskId` 页面可以访问。
- 请求异常时页面有明确状态反馈。

3. 组件拆分

完成内容：

- 新增 `TaskOverview`。
- 新增 `TaskStatus`。
- 新增 `TaskEvents`。
- 新增 `RelatedTrace`。

可验证结果：

- Task Detail 页面可以展示 summary 中的 task、status、events 和 related trace。
- 页面视觉风格与 Trace Detail 保持一致。

4. 路由接入

完成内容：

- 在 `router.tsx` 增加 `/console/tasks/:taskId`。

可验证结果：

- 浏览器直接访问 `/console/tasks/{taskId}` 可以进入 Task Detail。

5. Trace -> Task 跳转接入

完成内容：

- 在 `TraceOverviewPanel.tsx` 的 Linked Task 中增加到 `/console/tasks/:taskId` 的跳转。

可验证结果：

- 从 Trace Detail 点击 Linked Task 可以进入 Task Detail。

6. Task -> Trace 跳转接入

完成内容：

- 在 `RelatedTrace` 中增加到 `/console/traces/:traceId` 的跳转。

可验证结果：

- 从 Task Detail 点击 Related Trace 可以回到 Trace Detail。

7. 最小联调验证

完成内容：

- 用真实 trace/task 数据验证跳转闭环。
- 验证无 trace、无 events、接口错误、403 场景。

可验证结果：

- Trace -> Task -> Trace 双向跳转闭环成立。
- 页面状态符合现有 trace console 交互方式。

## 13. 测试计划

### 13.1 Trace -> Task 跳转

验证内容：

- 打开 `/console/traces/:traceId`。
- Trace Detail 中存在 Linked Task 时显示跳转入口。
- 点击 Linked Task 后进入 `/console/tasks/:taskId`。

通过标准：

- URL 正确变化。
- Task Detail 页面正常发起 task summary 请求。
- 页面正常渲染任务摘要。

### 13.2 Task -> Trace 跳转

验证内容：

- 打开 `/console/tasks/:taskId`。
- Related Trace 区域显示关联 trace。
- 点击 Related Trace 后进入 `/console/traces/:traceId`。

通过标准：

- URL 正确变化。
- Trace Detail viewer 正常加载。
- trace 信息与关联 task 对应。

### 13.3 summary 数据渲染

验证内容：

- Task Overview 显示基础 task 字段。
- Task Status 显示状态、路由、审核状态、工具数量、错误信息。
- Task Events 显示 task events。
- Related Trace 显示 trace 摘要或空态。

通过标准：

- 页面字段来自 `GET /tasks/{task_id}/summary`。
- 空字段显示为 `-` 或明确空态，不出现运行时错误。

### 13.4 loading / error / no permission

验证内容：

- 请求中显示 loading。
- 404 或普通错误显示 error。
- 401 或 403 显示 no permission。
- 缺失 taskId 时显示错误状态。

通过标准：

- 状态表现与 Trace Detail 页面一致。
- 不出现空白页。
- 不出现未捕获异常。

## 14. 验收标准

- `/console/tasks/:taskId` 页面可访问。
- 页面能调用 `GET /tasks/{task_id}/summary`。
- Task Overview 正确渲染。
- Task Status 正确渲染。
- Task Events 正确渲染。
- Related Trace 可跳转到 `/console/traces/:traceId`。
- Trace Detail Linked Task 可跳转到 `/console/tasks/:taskId`。
- Trace -> Task -> Trace 双向跳转成立。
- loading、error、no permission 状态可用。
- 未新增后端接口。
- 未引入全局状态管理。
- 未实现任务取消、重试等复杂操作。

## 15. 下一线程衔接

下一线程：

- `stage3-trace-console-console-observability`

衔接目标：

- 在 Trace 与 Task 双向详情闭环稳定后，继续扩展 trace console 的监控面板与统计能力。
- 后续可以基于已有 trace list、trace detail、task detail 页面，补充观测总览、统计卡片、趋势视图和异常聚合入口。
