# Stage3 Trace Console Backend Query Contract 实施方案

## 1. 背景

当前项目已完成 stage2 的 trace、task、route、alert 与 console 聚合查询基础能力，后端已经具备以下实现基础：

- 请求级 trace 中间件与落库：
  - `app/presentation/api/middleware/trace.py`
  - `app/infrastructure/trace/service.py`
- trace 查询与 console 聚合接口：
  - `app/presentation/api/app.py`
- trace、timeline、graph、viewer 响应模型：
  - `app/presentation/api/schemas.py`
- trace、task、task_event、tool_result、route_decision、alert 的持久化表与索引：
  - `app/infrastructure/persistence/database.py`
  - `app/infrastructure/persistence/repositories.py`

当前后端已提供：

- `GET /traces/{trace_id}`
- `GET /traces/{trace_id}/summary`
- `GET /traces/{trace_id}/timeline`
- `GET /traces/{trace_id}/graph`
- `GET /console/traces/{trace_id}/viewer`
- `GET /tasks/{task_id}/summary`
- `GET /operations/overview`

其中，`/console/traces/{trace_id}/viewer` 已经具备“控制台详情页聚合接口”的雏形，但项目仍缺少 trace console 首版真正需要的“列表检索契约”与“可稳定复用的聚合服务边界”。

本子线程聚焦 stage3-trace-console 的后端查询契约收敛，为后续前端线程提供稳定、可直接接入的接口基础。

## 2. 当前问题

### 2.1 已有能力分散在 API 层

当前 trace timeline、graph、viewer 的聚合逻辑直接写在：

- `app/presentation/api/app.py`

典型表现：

- `_build_trace_timeline_events(...)`
- `_build_trace_graph(...)`
- `get_trace_summary(...)`
- `get_trace_console_viewer(...)`

这会带来以下问题：

- 聚合逻辑与 HTTP 接入层耦合过深
- 后续新增 trace list 或 viewer 变体时，`app.py` 会继续膨胀
- 难以做服务层复用与独立单元测试

### 2.2 缺少 trace console 列表接口

当前仓库只有：

- 单条 trace 查询
- trace 聚合摘要
- trace timeline / graph
- operations overview 运营摘要

但没有面向控制台列表页的：

- trace 列表
- 多条件筛选
- 分页
- 列表级聚合字段

因此前端无法无阻塞开发 trace console 首页。

### 2.3 viewer 已可用，但职责边界尚未正式固化

`GET /console/traces/{trace_id}/viewer` 已经能一次返回：

- trace
- summary
- timeline
- graph
- alerts

但当前尚未在正式文档中明确：

- 它是 trace 详情页唯一主接口
- 它不承担 trace 列表与全局统计职责
- 它的字段稳定边界是什么

### 2.4 列表所需聚合字段尚未规范

trace console 首版列表页至少需要：

- trace 基础信息
- 关联 task 信息
- route 信息
- review 状态
- alert 数量
- 最近事件时间

但当前仓库没有统一 DTO 与统一查询规则。

## 3. 子线程目标

本子线程目标是：

为 stage3-trace-console 首版建立稳定的后端查询契约，补齐 `GET /console/traces`，并将 trace console 聚合逻辑从 API 层下沉为独立服务层能力。

## 4. 范围边界

### 4.1 本子线程要做的内容

- 新增 `GET /console/traces`
- 固化 `GET /console/traces/{trace_id}/viewer` 的职责边界
- 新增 trace console 列表 DTO
- 将 trace summary、timeline、graph、viewer 聚合逻辑从 `app.py` 下沉
- 补充 repository 层 trace list 查询与筛选分页能力
- 补充 unit 与 integration 测试
- 为前端首版页面提供稳定字段清单

### 4.2 本子线程不做的内容

- 不做前端实现
- 不新增权限体系设计
- 不扩展多租户
- 不扩展成本配额
- 不扩展模型策略与模型路由
- 不新增 trace span / node / event 新表
- 不改 workflow 主执行链路
- 不改现有 `/traces/*` 契约语义
- 不扩展复杂监控大盘

## 5. 实施依据

本方案基于以下现有文件与接口判断：

- `app/presentation/api/app.py`
  - `/traces/stats`
  - `/traces/{trace_id}`
  - `/traces/{trace_id}/summary`
  - `/traces/{trace_id}/timeline`
  - `/traces/{trace_id}/graph`
  - `/console/traces/{trace_id}/viewer`
  - `/tasks/{task_id}/summary`
- `app/presentation/api/schemas.py`
  - `TracePayload`
  - `TraceSummaryPayload`
  - `TraceTimelineEventPayload`
  - `TraceGraphNodePayload`
  - `TraceGraphEdgePayload`
  - `TraceConsoleViewerPayload`
- `app/infrastructure/persistence/database.py`
  - `sys_request_trace`
  - `biz_task`
  - `biz_task_event`
  - `biz_tool_result`
  - `biz_route_decision`
  - `sys_alert_event`
- `app/infrastructure/persistence/repositories.py`
  - `SQLiteTraceRepository`
  - `SQLiteTaskEventRepository`
  - `SQLiteToolResultRepository`
  - `SQLiteRouteDecisionRepository`
- `tests/integration/test_api_http.py`
  - 已覆盖 trace summary / timeline / graph / viewer / overview 契约

## 6. 接口设计

### 6.1 当前可直接复用的接口

本子线程完成后，以下接口继续保留并供 trace console 复用：

- `GET /traces/{trace_id}`
- `GET /traces/{trace_id}/summary`
- `GET /traces/{trace_id}/timeline`
- `GET /traces/{trace_id}/graph`
- `GET /console/traces/{trace_id}/viewer`
- `GET /traces/{trace_id}/alerts`
- `GET /tasks/{task_id}/summary`
- `GET /operations/overview`

其中对前端首版最关键的是：

- `GET /console/traces`
- `GET /console/traces/{trace_id}/viewer`
- `GET /tasks/{task_id}/summary`

### 6.2 必须新增的接口

#### `GET /console/traces`

用途：

- 作为 trace console 首版列表页主接口
- 支持列表、筛选、分页与刷新

MVP 必做参数：

- `trace_id`
- `task_id`
- `session_id`
- `path`
- `method`
- `status_code`
- `route_name`
- `started_from`
- `started_to`
- `page`
- `page_size`

MVP 过滤规则：

- 所有参数组合关系为 `AND`
- `trace_id`、`task_id`、`session_id` 为精确匹配
- `method`、`path`、`status_code` 为精确匹配
- `route_name` 基于关联 task 的 route 信息
- `started_from` 与 `started_to` 基于 `sys_request_trace.started_at`
- 未关联 task 的 trace 仍需可见

MVP 分页规则：

- `page` 默认 `1`
- `page_size` 默认 `20`
- `page_size` 上限 `100`
- 固定排序：`started_at DESC, trace_id DESC`
- 返回：
  - `page`
  - `page_size`
  - `total`
  - `has_next`

MVP 返回结构：

```json
{
  "items": [
    {
      "trace_id": "trace_xxx",
      "request_id": "req_xxx",
      "method": "POST",
      "path": "/chat/stream",
      "status_code": 200,
      "error_code": "",
      "rate_limited": false,
      "started_at": "2026-04-10T10:00:00Z",
      "updated_at": "2026-04-10T10:00:03Z",
      "session_id": "session_xxx",
      "turn_id": "turn_xxx",
      "task_id": "task_xxx",
      "route_name": "deliberation_chat",
      "route_source": "request_entry",
      "execution_mode": "delegated",
      "review_status": "pass",
      "alert_count": 1,
      "last_event_at": "2026-04-10T10:00:03Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 138,
  "has_next": true
}
```

后续增强，不属于 MVP：

- `auth_subject`
- `error_code`
- `review_status`
- `has_alert`
- `route_source`
- `sort_by`
- `sort_order`
- 模糊搜索 `q`

### 6.3 `GET /console/traces/{trace_id}/viewer` 的职责边界

该接口继续保留，且职责正式收敛为：

- 作为 trace 详情页唯一主接口
- 一次返回详情页首屏所需全部聚合数据

MVP 返回内容：

- `trace`
- `summary`
- `timeline`
- `graph_nodes`
- `graph_edges`
- `alerts`

该接口不承担以下职责：

- trace 列表检索
- 大范围统计
- 跨 trace 对比
- 过滤项枚举
- 实时订阅接口
- timeline 独立分页

### 6.4 trace 与 task 跳转契约

MVP 不新增专门跳转接口，直接复用现有字段：

- trace 详情跳 task：
  - `viewer.summary.task.id`
- task 详情跳 trace：
  - `task.trace_id`

前端跳转链路：

- trace 详情页 -> `GET /tasks/{task_id}/summary`
- task 详情页 -> `GET /console/traces/{trace_id}/viewer`

这意味着后端只需保证以下字段稳定：

- `TracePayload.task_id`
- `TaskPayload.trace_id`
- `TaskPayload.session_id`
- `TaskPayload.turn_id`

## 7. DTO 草案

### 7.1 新增 DTO

建议在 `app/presentation/api/schemas.py` 新增：

#### `ConsoleTraceListItemPayload`

- `trace_id: str`
- `request_id: str`
- `method: str`
- `path: str`
- `status_code: int`
- `error_code: str = ""`
- `rate_limited: bool = False`
- `started_at: str`
- `updated_at: str`
- `session_id: str = ""`
- `turn_id: str = ""`
- `task_id: str = ""`
- `route_name: str = ""`
- `route_source: str = ""`
- `execution_mode: str = ""`
- `review_status: str = ""`
- `alert_count: int = 0`
- `last_event_at: str = ""`

#### `ConsoleTraceListResponse`

- `items: list[ConsoleTraceListItemPayload]`
- `page: int`
- `page_size: int`
- `total: int`
- `has_next: bool`

### 7.2 前端首版最小稳定字段清单

#### 列表页必需字段

- `trace_id`
- `method`
- `path`
- `status_code`
- `started_at`
- `session_id`
- `task_id`
- `route_name`
- `execution_mode`
- `review_status`
- `alert_count`

#### 详情页概览必需字段

来自 `TracePayload`：

- `trace_id`
- `request_id`
- `method`
- `path`
- `status_code`
- `error_code`
- `rate_limited`
- `started_at`
- `updated_at`
- `session_id`
- `turn_id`
- `task_id`

来自 `TaskPayload`：

- `id`
- `status`
- `execution_mode`
- `protocol_summary`
- `route_name`
- `route_reason`
- `route_source`
- `review_status`
- `review_summary`
- `tool_count`
- `error_message`
- `created_at`
- `updated_at`

#### 时间线字段

- `happened_at`
- `event_type`
- `source_type`
- `source_name`
- `title`
- `details`
- `trace_id`
- `task_id`

#### 图谱字段

node：

- `node_id`
- `node_type`
- `title`
- `subtitle`
- `happened_at`

edge：

- `source_id`
- `target_id`
- `edge_type`

#### 告警字段

- `id`
- `trace_id`
- `source_type`
- `source_name`
- `severity`
- `event_code`
- `message`
- `payload_json`
- `created_at`

## 8. 文件修改清单

### 8.1 新增文件

#### `app/application/services/trace_console_service.py`

职责：

- 提供 trace console 聚合服务
- 承担以下能力：
  - `list_console_traces(...)`
  - `get_trace_summary(...)`
  - `get_trace_timeline(...)`
  - `get_trace_graph(...)`
  - `get_trace_viewer(...)`

#### `tests/unit/test_trace_console_service.py`

职责：

- 针对 trace console 聚合逻辑做独立单测
- 覆盖 timeline、graph、viewer、list item 映射与降级规则

### 8.2 修改文件

#### `app/presentation/api/app.py`

职责调整：

- 新增 `GET /console/traces`
- 现有 trace summary / timeline / graph / viewer 接口改为调用 `TraceConsoleService`
- 不再直接承载复杂拼装逻辑

#### `app/presentation/api/schemas.py`

职责调整：

- 新增列表 DTO
- 固化 console 列表契约

#### `app/infrastructure/persistence/repositories.py`

职责调整：

- 为 `SQLiteTraceRepository` 增加 trace list 查询能力
- 支持筛选、分页与列表项聚合字段查询

#### `tests/integration/test_api_http.py`

职责调整：

- 补充 `GET /console/traces` integration test
- 保证 viewer 契约不回归

#### `app/application/services/__init__.py`

可选：

- 若项目服务导出风格要求统一，则补充 `TraceConsoleService` 导出

## 9. 聚合逻辑收敛方案

### 9.1 继续保留的逻辑

以下逻辑继续保留，但实现位置下沉：

- timeline 聚合思路
- graph 聚合思路
- viewer = summary + timeline + graph + alerts 的组合形式
- 现有 trace 相关 schema 命名

### 9.2 需要从 `app.py` 下沉的逻辑

以下内容应从 `app/presentation/api/app.py` 下沉到 `TraceConsoleService`：

- `_build_trace_timeline_events(...)`
- `_build_trace_graph(...)`
- `get_trace_summary(...)` 的聚合拼装
- `get_trace_console_viewer(...)` 的聚合拼装
- 后续 `GET /console/traces` 的列表项聚合拼装

下沉后，API 层只保留：

- 参数校验
- 权限校验
- 响应序列化
- HTTP 异常转换

## 10. 实施步骤

### 步骤 1：冻结 `GET /console/traces` 契约与 DTO

实施内容：

- 在 `schemas.py` 中新增 `ConsoleTraceListItemPayload`
- 在 `schemas.py` 中新增 `ConsoleTraceListResponse`

完成后可验证结果：

- trace list 的字段名、分页字段和最小稳定字段清单固定
- 前端可立即基于该契约做 mock

### 步骤 2：为 repository 增加 trace list 基础查询能力

实施内容：

- 在 `SQLiteTraceRepository` 中补充列表查询
- 支持：
  - `trace_id`
  - `task_id`
  - `session_id`
  - `path`
  - `method`
  - `status_code`
  - `started_from`
  - `started_to`
  - `page`
  - `page_size`

完成后可验证结果：

- 可查询 trace 列表
- 分页可用
- 基础筛选可用

### 步骤 3：补列表页聚合字段

实施内容：

- 在 repository 或 service 层补齐：
  - `route_name`
  - `route_source`
  - `execution_mode`
  - `review_status`
  - `alert_count`
  - `last_event_at`

完成后可验证结果：

- 单条列表项无需前端再拼 task/route/alert
- 无 task 的 trace 仍能稳定返回

### 步骤 4：新增 `TraceConsoleService`

实施内容：

- 新建 `app/application/services/trace_console_service.py`
- 将 trace console 聚合能力收敛到 service

完成后可验证结果：

- 聚合逻辑可被 API 层统一调用
- 逻辑复用路径清晰

### 步骤 5：将 summary / timeline / graph / viewer 聚合逻辑从 API 层下沉

实施内容：

- 从 `app.py` 中迁出拼装函数与拼装流程
- API 只调 service

完成后可验证结果：

- `app.py` 不再直接承担复杂聚合
- viewer 契约与现有行为保持兼容

### 步骤 6：新增 `GET /console/traces`

实施内容：

- 在 `app.py` 中增加路由
- 接入 service
- 使用新增 schema 输出

完成后可验证结果：

- `GET /console/traces` 可被前端直接消费
- 返回结构满足列表页要求

### 步骤 7：补 unit test

实施内容：

- 新增 `tests/unit/test_trace_console_service.py`

完成后可验证结果：

- timeline 排序稳定
- graph 生成稳定
- viewer 组合稳定
- list item 字段映射稳定

### 步骤 8：补 integration test

实施内容：

- 修改 `tests/integration/test_api_http.py`
- 补 trace list 契约测试
- 回归 viewer 契约测试

完成后可验证结果：

- 后端查询契约可通过 API 层完整验证
- 本子线程具备交付条件

## 11. 测试计划

### 11.1 Unit 测试

新增：

- `tests/unit/test_trace_console_service.py`

覆盖点：

- `list_console_traces(...)` 列表项映射规则
- `get_trace_timeline(...)` 时间线排序
- `get_trace_graph(...)` 节点与边生成
- `get_trace_viewer(...)` 组合输出完整性
- 无 task trace 的降级行为
- 有 alert / 无 alert 的分支行为

### 11.2 Integration 测试

修改：

- `tests/integration/test_api_http.py`

新增覆盖点：

- `GET /console/traces` 返回 200
- 默认分页正确
- `page/page_size` 分页行为正确
- `trace_id` 过滤
- `task_id` 过滤
- `session_id` 过滤
- `status_code` 过滤
- `method/path` 过滤
- `started_from/started_to` 过滤
- 未关联 task 的 trace 仍可查询
- `GET /console/traces/{trace_id}/viewer` 契约不回归
- `viewer.summary.task.id` 与 `/tasks/{task_id}/summary` 跳转一致

## 12. 验收标准

本子线程完成后，应满足以下条件：

- 已提供 `GET /console/traces`
- `GET /console/traces` 支持基础筛选与分页
- 列表项字段足以直接驱动 trace console 首版列表页
- `GET /console/traces/{trace_id}/viewer` 契约稳定
- `viewer` 一次返回详情页首屏所需数据
- trace 与 task 可基于现有字段双向跳转
- trace summary / timeline / graph / viewer 聚合逻辑已从 `app.py` 下沉
- 补齐 unit 与 integration 测试
- 不破坏现有 `/traces/*` 接口行为

## 13. 下一线程衔接

本子线程完成后，前端线程可无阻塞接入以下稳定契约：

- `GET /console/traces`
- `GET /console/traces/{trace_id}/viewer`
- `GET /tasks/{task_id}/summary`

前端可直接启动的工作包括：

- trace console 列表页
- trace 详情页
- trace 与 task 双向跳转
- 基础筛选与分页

前端无需等待：

- 自行拼装 summary/timeline/graph/alerts
- 额外的 task-trace link 接口
- 更多后端查询拆分

建议下一开发线程为：

- `stage3-trace-console-frontend-shell-and-pages`

该线程可在本子线程交付后，直接基于稳定契约并行推进首版页面开发。
