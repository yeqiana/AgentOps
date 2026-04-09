# AgentOps

这是一个基于 Python、LangGraph 和 OpenAI 兼容协议的 Agent 底座项目。

当前状态：
- 阶段 1 已完成
- 阶段 2 开发中
- 已支持 CLI、HTTP API、多模态输入、工具调用、任务追踪、运行时配置中心和最小多 Agent 编排
- 阶段 2 已补齐正式角色协议：`support / challenge / planner / executor / arbitration / critic / reviewer`
- 阶段 2 已支持可切换执行协议：`delegated / standard`

## 核心能力

- 持续对话 CLI
- HTTP API
- 多模型接入
- 图片、音频、视频、文件输入与上传
- OCR / ASR / 视频探测 / 抽帧 / 抽音轨
- 工具注册与 Agent 自动调用工具
- 统一鉴权
- 限流与幂等
- trace 查询
- 恢复告警查询
- 模型与工具的基础重试、熔断与降级
- 配置化恢复策略：LLM 降级到 `mock`、工具 `soft-fail`
- `router / debate / arbitration / critic / review` 多角色工作流
- 正式角色协议与角色注册：`support / challenge / planner / executor / arbitration / critic / reviewer`
- 可切换执行协议：`delegated / standard`
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
`-- prompts/
```

## 关键接口

- `GET /health`
- `POST /chat`
- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/assets`
- `GET /sessions/{session_id}/tasks`
- `GET /assets/{asset_id}`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `GET /tools`
- `POST /tools/{tool_name}/execute`
- `POST /assets/analyze`
- `POST /assets/upload`
- `GET /config/runtime`
- `PUT /config/runtime`
- `GET /workflow/config`
- `GET /workflow/roles`
- `PUT /workflow/roles/{role_key}`
- `GET /security/config`
- `GET /recovery/config`
- `GET /traces/{trace_id}`
- `GET /traces/{trace_id}/alerts`
- `GET /alerts`
- `GET /alerts/{alert_id}`

## 数据库概览

当前核心表：
- `sys_schema_version`
- `sys_user`
- `sys_request_trace`
- `sys_runtime_config`
- `sys_workflow_role`
- `sys_alert_event`
- `biz_session`
- `biz_message`
- `biz_asset`
- `biz_task`
- `biz_tool_result`

## 文档入口

企业级正式文档：
- [企业文档总索引](docs/enterprise/README.md)
- [总体设计](docs/enterprise/总体设计.md)
- [需求规格说明书](docs/enterprise/需求规格说明书.md)
- [详细设计说明书](docs/enterprise/详细设计说明书.md)
- [数据库设计说明书](docs/enterprise/数据库设计说明书.md)
- [开发计划](docs/enterprise/开发计划.md)
- [测试报告](docs/enterprise/测试报告.md)
- [评审报告](docs/enterprise/评审报告.md)

架构与规划资料：
- [架构文档总索引](docs/architecture/README.md)
- [架构规划资料](docs/architecture/plans)

如需查看每次阶段开发内容，直接查看 git 历史：

```powershell
git log --oneline
```
