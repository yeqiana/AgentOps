# AgentOps

## 项目简介

`AgentOps` 是一个面向企业内部场景的 AI Agent 后端底座，目标不是单点聊天应用，而是建设“模型 + 工具 + 任务 + 治理 + 排障”的可持续演进运行时平台。

当前项目已完成：
- 阶段 1：分析型 Agent 底座
- 阶段 2：企业级 Agent 运行时最小版

当前项目状态：
- 阶段 1：已结项
- 阶段 2：已结项
- 阶段 3：待启动

当前测试基线：
- `111 tests, OK`

## 当前能力

- CLI 连续对话
- CLI 流式回答输出
- HTTP API
- HTTP SSE 流式对话：`POST /chat/stream`
- 异步任务提交：`POST /tasks/submit`
- 异步任务运行时快照：`GET /tasks/runtime`
- 异步任务取消：`POST /tasks/{task_id}/cancel`
- 异步任务重试：`POST /tasks/{task_id}/retry`
- 任务状态统计：`GET /tasks/stats`
- 任务聚合摘要：`GET /tasks/{task_id}/summary`
- 会话聚合摘要：`GET /sessions/{session_id}/summary`
- 任务事件查询：`GET /tasks/{task_id}/events`
- 多模型接入：OpenAI 兼容协议 + `mock`
- 多模态输入：文本、图片、音频、视频、文件
- 资产上传：`POST /assets/upload`
- 资产分析：`POST /assets/analyze`
- 工具注册与自动调用
- 本地工具链：OCR、ASR、视频探测、抽帧、抽音轨
- 请求路由中台最小版
- 路由策略预览：`POST /routing/preview`
- 路由决策持久化、查询与统计，任务主记录同步保留 `route_source`
- 路由权限细分：`routing.read / routing.preview / routing.manage`
- 路由规则版本快照：`/routing/config/versions`
- 路由版本回滚：`POST /routing/config/versions/{version_no}/restore`
- 最小多 Agent 编排：`router / debate / arbitration / critic / review`
- 正式角色协议：`support / challenge / planner / executor / arbitration / critic / reviewer`
- 可切换执行协议：`delegated / standard`
- 统一鉴权
- 最小 RBAC
- 限流与幂等
- trace 查询、统计、摘要、时间线、图谱
- 控制台 trace 查看器聚合查询
- alert 查询、统计及 trace 关联查询
- 模型与工具的重试、熔断、降级
- 数据库驱动运行时配置中心
- 配置变更审计与回查
- 控制台聚合总览

## 快速开始

### 启动 CLI

```powershell
.\.venv\Scripts\python.exe run.py
```

### 启动 API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.presentation.api:create_app --factory --host 127.0.0.1 --port 8011
```

### 运行测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## 目录结构

```text
app/
|-- presentation/
|-- application/
|-- domain/
|-- workflow/
`-- infrastructure/

tests/
|-- unit/
|-- integration/
`-- e2e/

docs/
|-- enterprise/
|-- architecture/
|-- api/
|-- prompts/
`-- ai-prompts/
```

## 关键接口

- `GET /health`
- `GET /auth/me`
- `GET /auth/roles`
- `GET /auth/permissions/matrix`
- `GET /auth/subjects/{auth_subject}/roles`
- `PUT /auth/subjects/{auth_subject}/roles`
- `POST /chat`
- `POST /chat/stream`
- `POST /tasks/submit`
- `GET /tasks`
- `GET /tasks/stats`
- `GET /tasks/runtime`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/summary`
- `GET /tasks/{task_id}/events`
- `GET /tasks/{task_id}/routes`
- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/retry`
- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/summary`
- `GET /sessions/{session_id}/assets`
- `GET /sessions/{session_id}/tasks`
- `GET /assets/{asset_id}`
- `GET /tools`
- `POST /tools/{tool_name}/execute`
- `POST /assets/analyze`
- `POST /assets/upload`
- `GET /workflow/config`
- `GET /workflow/roles`
- `PUT /workflow/roles/{role_key}`
- `GET /routing/config`
- `GET /routing/config/template`
- `GET /routing/config/events`
- `GET /routing/config/versions`
- `POST /routing/config/versions/{version_no}/restore`
- `POST /routing/preview`
- `GET /routes`
- `GET /routes/stats`
- `GET /config/runtime`
- `GET /config/runtime/events`
- `PUT /config/runtime`
- `GET /security/config`
- `GET /recovery/config`
- `GET /traces/{trace_id}`
- `GET /traces/stats`
- `GET /traces/{trace_id}/summary`
- `GET /traces/{trace_id}/timeline`
- `GET /traces/{trace_id}/graph`
- `GET /console/traces/{trace_id}/viewer`
- `GET /traces/{trace_id}/alerts`
- `GET /alerts`
- `GET /alerts/stats`
- `GET /alerts/{alert_id}`
- `GET /operations/overview`

## 数据库概览

系统表：
- `sys_schema_version`
- `sys_user`
- `sys_request_trace`
- `sys_runtime_config`
- `sys_runtime_config_event`
- `sys_workflow_role`
- `sys_alert_event`
- `sys_auth_role`
- `sys_auth_permission`
- `sys_auth_role_permission`
- `sys_auth_subject_role`

业务表：
- `biz_session`
- `biz_message`
- `biz_asset`
- `biz_task`
- `biz_task_event`
- `biz_tool_result`
- `biz_route_decision`

## 文档入口

当前状态与正式文档，优先查看：
- [企业文档总索引](docs/enterprise/README.md)
- [开发计划](docs/enterprise/开发计划.md)
- [阶段1最终验收结论单](docs/enterprise/阶段1最终验收结论单.md)
- [阶段2结项复核单](docs/enterprise/阶段2结项复核单.md)

规划资料索引：
- [架构文档总索引](docs/architecture/README.md)

如需查看每次阶段开发内容，直接查看 git 历史：

```powershell
git log --oneline
```

## frontend-vue

`frontend-vue/` is the Vue 3 + Element Plus frontend workspace for the Figma ChatGPT redesign page.

```powershell
cd frontend-vue
npm install
npm run dev
```

Default route:
- `/chatgpt-redesign`
