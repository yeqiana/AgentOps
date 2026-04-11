# Stage3 Trace Console Observability Advanced 实施方案

## 1. 背景

stage3-trace-console 已完成 Trace、Task 与 Observability 第一阶段能力。当前 `/console/observability` 已经作为 Trace Console 的全局运行态入口，基于 `GET /operations/overview` 展示 runtime、task status、recent tasks、recent alerts 和 route stats。

本线程在不重构现有 Observability 首页的前提下，增量接入 trace stats 与 alert stats，补充请求流量、状态码、限流、告警统计等高级观测信息。

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
- `/console/observability`

当前 `/console/traces` 列表页已完成，支持筛选、分页、loading、empty、error、no permission 和 trace_id 跳转详情页。

当前 `/console/traces/:traceId` Trace Detail 已完成，并接入：

- `GET /console/traces/{trace_id}/viewer`

当前 `/console/tasks/:taskId` Task Detail 已完成，并接入：

- `GET /tasks/{task_id}/summary`

当前 Trace -> Task -> Trace 双向跳转闭环已完成。

当前 `/console/observability` 第一阶段已完成，并且第一阶段仅接入：

- `GET /operations/overview`

当前 Observability 页面已具备：

- runtime KPI
- task status 分布
- recent tasks
- recent alerts
- route stats
- Task / Trace 跳转
- loading / error / no permission / empty / ready 状态

当前前端尚未接入：

- `GET /traces/stats`
- `GET /alerts/stats`
- `GET /tasks/stats`

其中 `GET /tasks/stats` 本线程默认不接入，仅作为后续可选扩展。

## 3. 本线程目标

在现有 `/console/observability` 基础上扩展高级观测能力，新增 TraceTrafficStatsPanel 与 AlertStatsPanel，并对 KPI 做轻量增强。

## 4. 当前已完成项

- `frontend/trace-console` 前端工程已建立。
- React + TypeScript + Vite 已稳定运行。
- `/console/traces` 列表页已完成。
- `/console/traces/:traceId` Trace Detail 已完成。
- `/console/tasks/:taskId` Task Detail 已完成。
- `/console/observability` 第一阶段已完成。
- `GET /operations/overview` 前端 API 已封装。
- `OperationsOverviewResponse` 前端 DTO 已存在。
- `ObservabilityDashboardPage` 已存在。
- `ObservabilityKpiGrid` 已存在。
- `TaskStatusSummaryPanel` 已存在。
- `RecentActivityPanel` 已存在。
- `AlertSummaryPanel` 已存在。
- `RouteStatsPanel` 已存在。
- 后端已提供 `GET /traces/stats`。
- 后端已提供 `GET /alerts/stats`。
- 后端已提供 `GET /tasks/stats`，但本线程不默认接入。

## 5. 当前未完成项

- 前端 API 层尚未封装 `getTraceStats()`。
- 前端 API 层尚未封装 `getAlertStats()`。
- 前端类型层尚未补齐 `TraceStatsResponse`。
- 前端类型层尚未补齐 `AlertStatsResponse`。
- `/console/observability` 页面尚未加载 trace stats。
- `/console/observability` 页面尚未加载 alert stats。
- 尚未新增 `TraceTrafficStatsPanel`。
- 尚未新增 `AlertStatsPanel`。
- KPI 尚未展示 total traces、success rate、error traces、rate limited traces。

## 6. 范围边界

### 6.1 做什么

- 新增 `TraceTrafficStatsPanel`。
- 新增 `AlertStatsPanel`。
- 接入 `GET /traces/stats`。
- 接入 `GET /alerts/stats`。
- 对 KPI 做轻量增强：
  - total traces
  - success rate（粗算）
  - error traces
  - rate limited traces
- 复用当前 Observability 页面布局。
- 复用当前页面级 loading、error、no permission、empty 状态模式。
- 保持 Task / Trace / Observability 现有跳转闭环。

### 6.2 不做什么

- 不重构现有 observability 首页。
- 不接 `GET /tasks/stats`。
- 不做时间范围筛选。
- 不做趋势图。
- 不做耗时统计。
- 不做自动刷新。
- 不做 SSE。
- 不做图表库。
- 不做全局状态管理。
- 不新增后端接口。
- 不做成本扩展。
- 不做配额扩展。
- 不做权限治理扩展。
- 不做模型策略扩展。

## 7. 页面路由设计

本线程不新增路由。

继续使用现有路由：

- `/console/observability`

页面结构约束：

- 不重构现有 observability 首页。
- 不改变 `/console/traces`、`/console/traces/:traceId`、`/console/tasks/:taskId` 既有路由。
- 仅在 `/console/observability` 中增量新增：
  - `TraceTrafficStatsPanel`
  - `AlertStatsPanel`

## 8. 页面拆分

当前已有页面容器：

- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

本线程在该页面内增量扩展：

- 加载 trace stats。
- 加载 alert stats。
- 将 trace stats 提供给 `TraceTrafficStatsPanel`。
- 将 alert stats 提供给 `AlertStatsPanel`。
- 将 trace stats 汇总结果提供给 `ObservabilityKpiGrid` 做轻量增强。

推荐页面结构：

- Hero
- `ObservabilityKpiGrid`
- `TraceTrafficStatsPanel`
- `AlertStatsPanel`
- `TaskStatusSummaryPanel`
- `RecentActivityPanel`
- `AlertSummaryPanel`
- `RouteStatsPanel`

说明：

- `AlertSummaryPanel` 继续负责 recent alerts。
- `AlertStatsPanel` 只负责 alert stats 聚合展示。
- `TaskStatusSummaryPanel` 继续使用 `operations/overview.summary.task_stats`。
- 本线程不新增 task stats 独立面板。

## 9. 组件拆分

新增组件：

- `frontend/trace-console/src/features/trace-console/components/TraceTrafficStatsPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/AlertStatsPanel.tsx`

修改组件：

- `frontend/trace-console/src/features/trace-console/components/ObservabilityKpiGrid.tsx`

复用组件：

- `frontend/trace-console/src/components/PageStateView.tsx`
- `frontend/trace-console/src/components/StatusBadge.tsx`
- `frontend/trace-console/src/components/LinkButton.tsx`

复用或少量扩展样式：

- `frontend/trace-console/src/app/styles.css`

样式约束：

- 优先复用当前 `.observability-grid`、`.observability-kpi-grid`、`.observability-list`、`.observability-table-wrap` 风格。
- 如需补充，只添加与 stats panel 直接相关的少量样式。
- 不引入图表库。

## 10. 前端工程落位方案

API 层修改：

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`

类型层修改：

- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`

页面层修改：

- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

组件层新增：

- `frontend/trace-console/src/features/trace-console/components/TraceTrafficStatsPanel.tsx`
- `frontend/trace-console/src/features/trace-console/components/AlertStatsPanel.tsx`

组件层修改：

- `frontend/trace-console/src/features/trace-console/components/ObservabilityKpiGrid.tsx`

文案层可选修改：

- `frontend/trace-console/src/constants/uiText.ts`

样式层可选修改：

- `frontend/trace-console/src/app/styles.css`

## 11. 当前接口依赖

### 11.1 本线程接入

接口：

- `GET /traces/stats`
- `GET /alerts/stats`

`GET /traces/stats` 当前后端参数：

- `method?: string`
- `path?: string`
- `limit?: int`
- `offset?: int`

`GET /traces/stats` 当前返回字段：

- `stats[].method`
- `stats[].path`
- `stats[].status_code`
- `stats[].rate_limited`
- `stats[].trace_count`
- `stats[].last_started_at`

`GET /alerts/stats` 当前后端参数：

- `source_type?: string`
- `limit?: int`
- `offset?: int`

`GET /alerts/stats` 当前返回字段：

- `stats[].severity`
- `stats[].source_type`
- `stats[].alert_count`
- `stats[].last_created_at`

### 11.2 本线程不接入

接口：

- `GET /tasks/stats`

原因：

- `/console/observability` 当前已经通过 `GET /operations/overview` 获取 `summary.task_stats`。
- 本线程不做 session 维度筛选。
- 为避免接口膨胀，本线程不重复拉取 task stats。

## 12. 实施步骤

1. 类型与 API 封装

完成内容：

- 在 `traceConsole.ts` 新增 `TraceStat`、`TraceStatsResponse`。
- 在 `traceConsole.ts` 新增 `AlertStat`、`AlertStatsResponse`。
- 在 `traceConsoleApi.ts` 新增 `getTraceStats()`。
- 在 `traceConsoleApi.ts` 新增 `getAlertStats()`。

可验证结果：

- TypeScript 可识别 trace stats 与 alert stats DTO。
- 前端可通过统一 HTTP client 请求 `GET /traces/stats` 与 `GET /alerts/stats`。

2. 页面状态扩展

完成内容：

- 在 `ObservabilityDashboardPage` 增加 trace stats state。
- 在 `ObservabilityDashboardPage` 增加 alert stats state。
- 页面加载时在 `GET /operations/overview` 基础上增加 stats 请求。

可验证结果：

- `/console/observability` 页面仍可访问。
- operations overview 原有模块不受影响。
- stats 数据可进入页面 state。

3. TraceTrafficStatsPanel

完成内容：

- 新增 `TraceTrafficStatsPanel`。
- 展示 method、path、status_code、rate_limited、trace_count、last_started_at。
- 基于 trace stats 做 total traces、error traces、rate limited traces 的汇总。

可验证结果：

- trace stats 空数据时显示空态。
- trace stats 有数据时可正常展示。

4. AlertStatsPanel

完成内容：

- 新增 `AlertStatsPanel`。
- 展示 severity、source_type、alert_count、last_created_at。

可验证结果：

- alert stats 空数据时显示空态。
- alert stats 有数据时可正常展示。

5. KPI 轻量增强

完成内容：

- 修改 `ObservabilityKpiGrid` 入参，允许接收 trace stats 汇总。
- 展示 total traces。
- 展示 success rate（粗算）。
- 展示 error traces。
- 展示 rate limited traces。

粗算规则：

- `total traces = sum(trace_count)`
- `error traces = sum(trace_count where status_code >= 400)`
- `rate limited traces = sum(trace_count where rate_limited = true)`
- `success rate = (total traces - error traces) / total traces`
- 当 `total traces = 0` 时显示 `-`

可验证结果：

- KPI 原有 runtime 指标仍正常。
- 新增 KPI 在 trace stats 可用时正常展示。

6. 最小联调与验收

完成内容：

- 联调 `/console/observability`。
- 验证 `GET /traces/stats`。
- 验证 `GET /alerts/stats`。
- 验证新增 panel 和 KPI。
- 验证 Trace / Task / Observability 现有闭环。

可验证结果：

- 页面可访问。
- 新增 stats 数据可正常展示。
- 现有 Observability 模块不受影响。

## 13. 测试计划

### 13.1 /console/observability 页面可访问

验证内容：

- 访问 `/console/observability`。

通过标准：

- 页面正常渲染。
- 原有 operations overview 模块仍正常。

### 13.2 traces/stats 联调成功

验证内容：

- 页面请求 `GET /traces/stats`。
- 返回数据进入 `TraceTrafficStatsPanel`。

通过标准：

- 请求路径正确。
- `method/path/status_code/rate_limited/trace_count/last_started_at` 可展示。

### 13.3 alerts/stats 联调成功

验证内容：

- 页面请求 `GET /alerts/stats`。
- 返回数据进入 `AlertStatsPanel`。

通过标准：

- 请求路径正确。
- `severity/source_type/alert_count/last_created_at` 可展示。

### 13.4 新增两个 panel 可正常渲染

验证内容：

- `TraceTrafficStatsPanel` 有数据、空数据均可展示。
- `AlertStatsPanel` 有数据、空数据均可展示。

通过标准：

- 不出现运行时错误。
- 不影响原有 panel。

### 13.5 KPI 粗算结果可展示

验证内容：

- total traces 可展示。
- success rate 可展示。
- error traces 可展示。
- rate limited traces 可展示。

通过标准：

- 粗算结果符合 trace stats 输入。
- `total traces = 0` 时 success rate 显示为 `-`。

### 13.6 loading / error / no permission / empty 正常

验证内容：

- loading 状态显示正常。
- 接口错误显示 error。
- 401 或 403 显示 no permission。
- stats 为空时新增 panel 显示空态。

通过标准：

- 页面不出现空白。
- 页面不出现未捕获异常。
- 状态展示与现有 Observability 页面风格一致。

## 14. 验收标准

- `/console/observability` 页面可访问。
- `GET /traces/stats` 联调成功。
- `GET /alerts/stats` 联调成功。
- `TraceTrafficStatsPanel` 可正常展示。
- `AlertStatsPanel` 可正常展示。
- KPI 可展示 total traces、success rate、error traces、rate limited traces。
- 现有 Observability 模块不受影响。
- 不破坏 Trace / Task / Observability 现有闭环。
- 本线程未接入 `GET /tasks/stats`。
- 未新增后端接口。
- 未引入图表库。
- 未引入全局状态管理。
- 未实现时间范围筛选。
- 未实现自动刷新或 SSE。

## 15. 下一线程衔接

下一线程：

- `stage3-trace-console-console-polish`

衔接目标：

- 用于后续导航入口优化、中文化统一、交互与样式收口。
- 在高级观测数据稳定后，统一 Trace Console 的页面入口、文案、按钮、空态、错误态和视觉层级。
