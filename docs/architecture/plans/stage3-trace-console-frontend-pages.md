# Stage3 Trace Console Frontend Pages 实施方案

## 1. 背景

stage3-trace-console 已完成后端查询契约子线程，后端已提供 trace console 首版页面所需的核心 API：

- `GET /console/traces`
- `GET /console/traces/{trace_id}/viewer`
- `GET /tasks/{task_id}/summary`

当前前端工程已经开始落地，列表页 API 代理链路已修复并验证通过：

- `/api/console/traces` 正常
- 分页筛选正常
- Vite 前端代理链路正常

本实施文档基于当前仓库真实实现状态更新，后续重点从“前端工程与列表页搭建”转向“Trace Detail 页面开发”。

## 2. 当前现状

### 2.1 前端工程现状

当前仓库已经建立前端工程：

- `frontend/trace-console/`

技术栈已经落地：

- React
- TypeScript
- Vite
- React Router

关键文件：

- `frontend/trace-console/package.json`
- `frontend/trace-console/vite.config.ts`
- `frontend/trace-console/src/main.tsx`
- `frontend/trace-console/src/app/App.tsx`
- `frontend/trace-console/src/app/router.tsx`
- `frontend/trace-console/src/app/styles.css`

当前 Vite 代理已配置：

- 前端请求 `/api`
- 代理到后端 `http://127.0.0.1:8011`
- 通过 rewrite 去掉 `/api` 前缀

### 2.2 当前路由现状

当前已存在路由：

- `/`
  - 重定向到 `/console/traces`
- `/console/traces`
  - Trace 列表页
- `/console/traces/:traceId`
  - Trace 详情页入口

相关文件：

- `frontend/trace-console/src/app/router.tsx`
- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`
- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`

### 2.3 Trace 列表页现状

`/console/traces` 已落地并运行成功。

当前已支持：

- 筛选栏
- 分页
- loading 状态
- empty 状态
- error 状态
- no permission 状态
- `trace_id` 跳转详情页入口

相关文件：

- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`
- `frontend/trace-console/src/features/trace-console/components/TraceFilterBar.tsx`
- `frontend/trace-console/src/features/trace-console/components/TracePagination.tsx`
- `frontend/trace-console/src/features/trace-console/components/TraceTable.tsx`
- `frontend/trace-console/src/components/PageStateView.tsx`
- `frontend/trace-console/src/components/StatusBadge.tsx`

### 2.4 Trace 详情页现状

`/console/traces/:traceId` 当前仍是占位页。

当前行为：

- 从 URL 读取 `traceId`
- 显示当前 `traceId`
- 显示占位说明
- 提供返回 `/console/traces` 的按钮

相关文件：

- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`

### 2.5 API Client 与类型现状

当前已有列表页 API client：

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`

当前已有列表类型：

- `ConsoleTraceListItem`
- `ConsoleTraceListResponse`
- `TraceListFilters`

相关文件：

- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

当前尚未补齐：

- `TraceConsoleViewerResponse`
- `TracePayload`
- `TraceSummaryPayload`
- `TraceTimelineEvent`
- `TraceGraphNode`
- `TraceGraphEdge`
- `AlertEvent`
- `TaskPayload`
- `ToolResult`
- `TaskEvent`
- `getTraceConsoleViewer(traceId)`

## 3. 本线程目标

本线程当前目标是：

在已完成 `/console/traces` 列表页与 API 代理链路验证的基础上，进入 `stage3-trace-console-trace-detail`，实现 Trace Detail 页面首版。

## 4. 当前已完成项

当前已完成：

- `frontend/trace-console` 前端工程已建立
- React + TypeScript + Vite 已落地
- React Router 已落地
- `/console/traces` 列表页已落地并运行成功
- 列表页已接入 `GET /console/traces`
- 列表页已支持筛选栏
- 列表页已支持分页
- 列表页已支持 loading / empty / error / no permission 状态
- 列表页已支持 `trace_id` 跳转详情页入口
- 前端 HTTP client 已统一处理 `/api` base path
- 联调问题已定位并修复：使用 `/api` 代理模式
- Vite proxy 已能将 `/api/console/traces` 转发到后端 `/console/traces`

## 5. 当前未完成项

当前未完成：

- Trace Detail 页面仍为占位页
- 尚未接入 `GET /console/traces/{trace_id}/viewer`
- 尚未定义 viewer 相关前端 DTO
- 尚未实现 trace overview
- 尚未实现 timeline 面板
- 尚未实现 console logs / diagnostic records 面板
- 尚未实现 alerts 面板
- 尚未实现 graph 简版结构展示
- 尚未实现 Trace Detail 页面 loading / error / no permission 的完整状态处理
- 尚未实现 Task Detail 页面
- 尚未实现 Trace -> Task / Task -> Trace 完整跳转闭环

## 6. 范围边界

### 6.1 本阶段要做

下一阶段进入：

- `stage3-trace-console-trace-detail`

本阶段重点：

- 将 `TraceDetailEntryPage` 从占位页升级为详情页容器
- 新增 viewer API client
- 新增 viewer DTO 类型
- 展示 overview
- 展示 timeline
- 展示 console logs
- 展示 alerts
- graph 暂时只做简版结构展示
- 完成详情页 loading / error / no permission 状态处理

### 6.2 本阶段不做

本阶段不做：

- 不新增后端接口
- 不修改后端查询契约
- 不实现完整 Task Detail 页面
- 不实现复杂图谱画布
- 不实现实时刷新
- 不实现 timeline 与 graph 联动
- 不实现多 trace 对比
- 不扩展权限、多租户、成本配额、模型策略

### 6.3 MVP 与后续增强

MVP 必做：

- `GET /console/traces/{trace_id}/viewer` 数据加载
- overview
- timeline
- console logs
- alerts
- graph 简版结构展示
- 返回列表
- 基础状态处理

后续增强：

- 完整 Task Detail 页面
- Trace -> Task / Task -> Trace 双向跳转闭环
- graph canvas 可视化
- timeline / logs / graph 联动
- 自动刷新
- 详情页分区折叠状态记忆

## 7. 页面路由设计

当前已存在：

- `/console/traces`
- `/console/traces/:traceId`

下一阶段继续沿用：

- `/console/traces/:traceId`

暂不新增路由。

后续增强可补：

- `/console/tasks/:taskId`

## 8. 页面拆分

### 8.1 Trace 列表页

当前状态：

- 已完成首版
- 已运行成功
- 当前不是下一阶段主目标

后续可能增强：

- task_id 行内跳转
- 自动刷新
- 高级筛选
- 顶部 overview 摘要

### 8.2 Trace 详情页

下一阶段主目标。

页面数据来源：

- `GET /console/traces/{trace_id}/viewer`

页面结构：

- 顶部：返回列表、trace 标题、核心状态
- Overview：trace 与 task 核心信息
- Timeline：`viewer.timeline`
- Console logs：由 `viewer.summary.task_events`、`viewer.summary.tool_results`、`viewer.alerts` 组成诊断视图
- Alerts：`viewer.alerts`
- Graph：`viewer.graph_nodes` 与 `viewer.graph_edges` 的简版结构展示

### 8.3 Trace -> Task / Task -> Trace 跳转

当前状态：

- 列表页已有 trace_id -> trace detail 跳转
- Task Detail 页面尚未实现

本阶段处理策略：

- Trace Detail 页面中可以展示 `task_id`
- 若保守控制范围，本阶段先不启用 Task Detail 路由
- 后续进入 Task Detail 子线程时，再实现 `/console/tasks/:taskId`

后续跳转规则：

- Trace -> Task：
  - 从 `viewer.summary.task.id` 获取 task id
  - 跳转 `/console/tasks/:taskId`
- Task -> Trace：
  - 从 `task.trace_id` 获取 trace id
  - 跳转 `/console/traces/:traceId`

## 9. 组件拆分

### 9.1 已有组件

当前已有通用组件：

- `PageStateView`
- `StatusBadge`
- `LinkButton`

当前已有列表页组件：

- `TraceFilterBar`
- `TracePagination`
- `TraceTable`

### 9.2 下一阶段建议新增组件

建议新增：

- `TraceOverviewPanel`
  - 展示 trace 与 task 概览
- `TraceTimelinePanel`
  - 展示 timeline events
- `TraceConsoleLogsPanel`
  - 展示 task events、tool results、alerts 的诊断日志视图
- `TraceAlertsPanel`
  - 展示 alerts
- `TraceGraphPanel`
  - 展示 graph nodes / graph edges 简版结构

### 9.3 暂不新增的组件

暂不新增：

- `TaskDetailPage`
- `GraphCanvas`
- `TimelineGraphConnector`
- `AutoRefreshControl`

## 10. 前端工程落位方案

当前前端工程已经落位：

- `frontend/trace-console`

当前目录结构：

- `src/app`
  - 应用壳、路由、全局样式
- `src/components`
  - 通用组件
- `src/features/trace-console`
  - trace console 业务 API、组件、类型
- `src/lib/http`
  - HTTP client
- `src/pages/traces`
  - trace 页面

下一阶段继续沿用该结构。

建议落位：

- Trace Detail 容器页：
  - `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`
- Trace Detail 业务组件：
  - `frontend/trace-console/src/features/trace-console/components/TraceOverviewPanel.tsx`
  - `frontend/trace-console/src/features/trace-console/components/TraceTimelinePanel.tsx`
  - `frontend/trace-console/src/features/trace-console/components/TraceConsoleLogsPanel.tsx`
  - `frontend/trace-console/src/features/trace-console/components/TraceAlertsPanel.tsx`
  - `frontend/trace-console/src/features/trace-console/components/TraceGraphPanel.tsx`
- Viewer API:
  - `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`
- Viewer types:
  - `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

## 11. 当前接口依赖

### 11.1 已接入接口

当前已接入：

- `GET /console/traces`

前端调用：

- `getConsoleTraces(...)`

### 11.2 下一阶段需要接入接口

下一阶段接入：

- `GET /console/traces/{trace_id}/viewer`

建议前端方法：

- `getTraceConsoleViewer(traceId)`

### 11.3 暂不新增接口

本阶段不新增：

- `/console/traces/{trace_id}/logs`
- `/console/tasks/{task_id}`
- `/console/tasks/{task_id}/trace-link`

Console logs 面板首版直接基于 viewer 聚合数据渲染。

## 12. 下一阶段开发重点：Trace Detail

下一步进入：

- `stage3-trace-console-trace-detail`

Trace Detail MVP 必须实现：

- 使用 `GET /console/traces/{trace_id}/viewer`
- 展示 overview
- 展示 timeline
- 展示 console logs
- 展示 alerts
- graph 暂时只做简版结构展示

### 12.1 Overview

来源：

- `viewer.trace`
- `viewer.summary.task`

展示：

- `trace_id`
- `request_id`
- `method`
- `path`
- `status_code`
- `error_code`
- `rate_limited`
- `started_at`
- `updated_at`
- `task.id`
- `task.status`
- `task.route_name`
- `task.execution_mode`
- `task.review_status`

### 12.2 Timeline

来源：

- `viewer.timeline`

展示：

- `happened_at`
- `event_type`
- `source_type`
- `source_name`
- `title`
- `details`

### 12.3 Console logs

来源：

- `viewer.summary.task_events`
- `viewer.summary.tool_results`
- `viewer.alerts`

说明：

- 当前后端没有独立 console logs 接口
- 本阶段将 task events、tool results、alerts 作为诊断日志视图的数据来源
- 该面板是前端展示命名，不代表新增后端接口

### 12.4 Alerts

来源：

- `viewer.alerts`

展示：

- `severity`
- `source_type`
- `source_name`
- `event_code`
- `message`
- `created_at`

### 12.5 Graph

来源：

- `viewer.graph_nodes`
- `viewer.graph_edges`

MVP 展示方式：

- 简版结构展示
- 可以先用节点列表 + 边列表
- 不做复杂画布、不做拖拽、不做缩放

## 13. 实施步骤

### 步骤 1：补 viewer DTO 类型

修改：

- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

完成后可验证：

- TypeScript 能识别 viewer 响应结构
- 后续组件可按类型开发

### 步骤 2：补 viewer API client

修改：

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`

新增：

- `getTraceConsoleViewer(traceId)`

完成后可验证：

- 前端可请求 `/api/console/traces/{traceId}/viewer`

### 步骤 3：改造 TraceDetailEntryPage 为容器页

修改：

- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`

完成后可验证：

- 页面进入时能读取 `traceId`
- 能加载 viewer 数据
- 能处理 loading / error / no permission

### 步骤 4：实现 overview 面板

新增：

- `TraceOverviewPanel`

完成后可验证：

- 详情页展示 trace 与 task 核心字段

### 步骤 5：实现 timeline 面板

新增：

- `TraceTimelinePanel`

完成后可验证：

- 详情页展示 timeline events

### 步骤 6：实现 console logs 与 alerts 面板

新增：

- `TraceConsoleLogsPanel`
- `TraceAlertsPanel`

完成后可验证：

- 详情页展示 task events、tool results、alerts

### 步骤 7：实现 graph 简版结构展示

新增：

- `TraceGraphPanel`

完成后可验证：

- 详情页展示 graph nodes 与 graph edges

### 步骤 8：补样式

修改：

- `frontend/trace-console/src/app/styles.css`

完成后可验证：

- 详情页在桌面与移动端均可阅读
- 面板视觉风格与列表页保持一致

## 14. 测试计划

### 14.1 手动联调

验证：

- 从 `/console/traces` 点击 `trace_id` 能进入详情页
- 详情页请求 `/api/console/traces/{traceId}/viewer`
- 页面能展示 overview
- 页面能展示 timeline
- 页面能展示 console logs
- 页面能展示 alerts
- 页面能展示 graph 简版结构
- 返回列表按钮可用

### 14.2 状态验证

验证：

- loading 状态
- error 状态
- no permission 状态
- traceId 缺失或无效时的错误态

### 14.3 构建验证

建议运行：

- `npm run build`

目录：

- `frontend/trace-console`

## 15. 验收标准

本阶段完成后应满足：

- `/console/traces/:traceId` 不再是占位页
- 详情页成功接入 `GET /console/traces/{trace_id}/viewer`
- 详情页展示 overview
- 详情页展示 timeline
- 详情页展示 console logs
- 详情页展示 alerts
- 详情页展示 graph 简版结构
- 详情页支持 loading / error / no permission
- 从列表页点击 `trace_id` 可进入详情页并看到真实数据
- 不新增后端接口
- 不破坏已完成的 `/console/traces` 列表页

## 16. 下一线程衔接

本阶段完成后，下一线程建议进入：

- `stage3-trace-console-task-detail-linking`

衔接内容：

- 实现 `/console/tasks/:taskId`
- 接入 `GET /tasks/{task_id}/summary`
- 完成 Trace -> Task / Task -> Trace 双向跳转闭环
- 后续再进入 graph canvas 增强与 timeline/logs 联动增强
