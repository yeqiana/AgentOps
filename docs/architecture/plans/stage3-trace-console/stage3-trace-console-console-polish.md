# Stage3 Trace Console Console Polish 实施方案

## 1. 背景

`stage3-trace-console-observability-advanced` 已完成验收，当前 Trace Console 已具备以下页面与能力：

- `/console/traces`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`
- `/console/observability`
- `GET /console/traces`
- `GET /console/traces/{trace_id}/viewer`
- `GET /tasks/{task_id}/summary`
- `GET /operations/overview`
- `GET /traces/stats`
- `GET /alerts/stats`

当前已发现但不属于前端实现范围的问题：

- `route_stats.last_trace_id` 指向的 trace 可能在 viewer 接口返回 `404 Trace missing`。
- `recent_alerts.trace_id` 指向的 trace 可能在 viewer 接口返回 `404 Trace missing`。
- `task summary` 中可能存在 trace 不存在的情况。

本线程不修复上述后端数据一致性问题，只在前端交互层做容错、文案、入口和视觉层级收口。

## 2. 本线程目标

完成 Trace Console 首版控制台体验打磨。

重点目标：

- 统一页面导航入口。
- 统一中文文案。
- 统一按钮、链接、空态、错误态和无权限态。
- 优化 trace / task 缺失时的前端容错提示。
- 收口页面视觉层级，减少重复样式。
- 保持现有 API 契约不变。

## 3. 范围边界

### 3.1 做什么

- 优化 Trace Console 顶部导航。
- 在 Trace List、Trace Detail、Task Detail、Observability 之间补齐清晰入口。
- 对缺失 trace 的跳转增加前端容错提示。
- 统一页面标题、副标题、按钮与状态文案。
- 统一 loading、empty、error、no permission 的展示方式。
- 清理明显重复或不一致的 CSS 类。
- 保持现有 React Router 路由稳定。

### 3.2 不做什么

- 不新增后端接口。
- 不修改数据库结构。
- 不修复后端数据一致性问题。
- 不接入图表库。
- 不引入全局状态管理。
- 不实现自动刷新或 SSE。
- 不做登录页或权限管理页。
- 不做完整设计系统。
- 不修改 `.env` 或本地密钥配置。

## 4. 涉及文件

预计修改：

- `frontend/trace-console/src/app/App.tsx`
- `frontend/trace-console/src/app/router.tsx`
- `frontend/trace-console/src/app/styles.css`
- `frontend/trace-console/src/constants/uiText.ts`
- `frontend/trace-console/src/components/LinkButton.tsx`
- `frontend/trace-console/src/components/PageStateView.tsx`
- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`
- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`
- `frontend/trace-console/src/pages/tasks/TaskDetailPage.tsx`
- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

按需修改：

- `frontend/trace-console/src/features/trace-console/components/*.tsx`
- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`
- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

## 5. 实施步骤

1. 导航入口收口

完成内容：

- 增加或优化控制台级导航。
- 保证 Trace、Task、Observability 页面之间入口清晰。
- 当前没有 task_id 时，不展示无效 Task 跳转。

验收标准：

- `/console/traces` 可进入 Trace Detail。
- Trace Detail 可进入 Task Detail。
- Task Detail 可回到 Trace Detail。
- Observability 中有效 trace / task 链接可跳转。
- 无效 trace / task 不造成页面空白。

2. 文案统一

完成内容：

- 将页面标题、按钮、空态、错误态、无权限态集中到 `uiText.ts` 或现有文案结构中。
- 移除明显混用的中英文提示。
- 对 `Trace missing` 场景给出用户可理解的中文提示。

验收标准：

- 用户可见文案口径一致。
- 404 trace 缺失时说明是数据链路缺失或记录已不可用。
- 不出现内部实现描述或调试口吻。

3. 状态展示统一

完成内容：

- 复用 `PageStateView`。
- 统一 loading / empty / error / no permission。
- 为 stats panel 空数据保留稳定布局。

验收标准：

- 页面加载、错误、空数据、无权限状态都能稳定显示。
- 状态变化不造成布局明显跳动。

4. 样式收口

完成内容：

- 清理重复样式。
- 保持按钮、表格、面板、状态 badge 的视觉层级一致。
- 避免新增与当前样式体系无关的大块样式。

验收标准：

- `npm run build` 通过。
- 主要页面在桌面宽度下无明显文字溢出。
- 页面主操作入口可识别。

## 6. 测试计划

### 6.1 构建验证

命令：

```bash
npm run build
```

通过标准：

- TypeScript 构建通过。
- Vite build 通过。

### 6.2 页面人工验证

验证页面：

- `/console/traces`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`
- `/console/observability`

通过标准：

- 页面可访问。
- 导航入口可用。
- 空态、错误态、无权限态可理解。
- 缺失 trace 的跳转不会导致用户无上下文地停在错误页。

## 7. 验收标准

- Trace Console 导航入口完成收口。
- 中文文案口径统一。
- 缺失 trace / task 的前端容错提示完成。
- 状态展示统一。
- 主要页面视觉层级一致。
- 不新增后端接口。
- 不提交 `.env.local`、`dist`、`node_modules`、`*.tsbuildinfo`。
- `npm run build` 通过。

## 8. 后续衔接

本线程完成后，再单独评估后端数据一致性问题：

- `route_stats.last_trace_id` 与 trace viewer 数据一致性。
- `recent_alerts.trace_id` 与 trace viewer 数据一致性。
- `task summary` 中 trace 缺失的生成与清理策略。
