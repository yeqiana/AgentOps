# AgentOps

## 项目简介

`AgentOps` 是一个面向企业内部场景的 AI Agent 后端底座，目标不是做单点聊天，而是把“模型 + 工具 + 任务 + 治理 + 排障”这条链路沉淀成可持续演进的运行时平台。

当前项目重点是：
- 多模态输入与工具增强
- 统一鉴权、限流、幂等、RBAC
- trace、告警、恢复治理
- trace 聚合摘要查询
- 请求路由中台最小版
- 多 Agent 最小编排
- 运行时配置中心
- 流式对话与异步任务预留

当前阶段：
- 阶段 1：已完成
- 阶段 2：开发中，当前进度约 `93%`
- 阶段 3：规划中

## 当前能力

- CLI 连续对话
- CLI 流式回答输出
- HTTP API
- HTTP SSE 流式对话：`POST /chat/stream`
- 异步任务提交预留：`POST /tasks/submit`
- 异步任务运行时快照：`GET /tasks/runtime`
- 异步任务取消：`POST /tasks/{task_id}/cancel`
- 任务事件查询：`GET /tasks/{task_id}/events`
- 多模型接入：OpenAI 兼容协议 + `mock`
- 多模态输入：文本、图片、音频、视频、文件
- 上传型资产入口：`POST /assets/upload`
- 资产分析入口：`POST /assets/analyze`
- 工具注册与自动调用
- 本地工具链：OCR、ASR、视频探测、抽帧、抽音轨
- 请求路由中台最小版
- 路由决策持久化、查询与统计
- 路由配置模板与校验：`GET /routing/config/template`，并对 `routing` 配置写入执行 key/type 校验
- 异步任务事件持久化与回查
- 最小多 Agent 编排：
  - `router`
  - `debate`
  - `arbitration`
  - `critic`
  - `review`
- 正式角色协议：
  - `support`
  - `challenge`
  - `planner`
  - `executor`
  - `arbitration`
  - `critic`
  - `reviewer`
- 可切换执行协议：
  - `delegated`
  - `standard`
- 统一鉴权
- 最小 RBAC
- 限流与幂等
- trace 查询
- 告警记录、查询与 trace 关联查询
- trace 聚合摘要查询
- 模型与工具的重试、熔断、降级
- 数据库驱动运行时配置中心
- 数据库驱动角色注册

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
- `PUT /auth/subjects/{auth_subject}/roles`
- `POST /chat`
- `POST /chat/stream`
- `POST /tasks/submit`
- `GET /tasks`
- `GET /tasks/runtime`
- `POST /tasks/{task_id}/cancel`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/events`
- `GET /tasks/{task_id}/routes`
- `GET /sessions`
- `GET /sessions/{session_id}`
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
- `GET /routes`
- `GET /routes/stats`
- `GET /config/runtime`
- `PUT /config/runtime`
- `GET /security/config`
- `GET /recovery/config`
- `GET /traces/{trace_id}`
- `GET /traces/{trace_id}/summary`
- `GET /traces/{trace_id}/alerts`
- `GET /alerts`
- `GET /alerts/{alert_id}`

## 数据库概览

系统表：
- `sys_schema_version`
- `sys_user`
- `sys_request_trace`
- `sys_runtime_config`
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

企业级正式文档：
- [企业文档总索引](docs/enterprise/README.md)
- [总体设计](docs/enterprise/总体设计.md)
- [详细设计说明书](docs/enterprise/详细设计说明书.md)
- [数据库设计说明书](docs/enterprise/数据库设计说明书.md)
- [开发计划](docs/enterprise/开发计划.md)
- [测试报告](docs/enterprise/测试报告.md)
- [功能清单](docs/enterprise/功能清单.md)
- [评审报告](docs/enterprise/评审报告.md)

架构规划资料：
- [架构文档总索引](docs/architecture/README.md)
- [架构规划资料](docs/architecture/plans)

提示词与归档资料：
- [Prompts 索引](docs/prompts/README.md)
- [AI Prompts 索引](docs/ai-prompts/README.md)

如需查看每次阶段开发内容，直接查看 git 历史：

```powershell
git log --oneline
```
