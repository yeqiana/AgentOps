# AgentOps

这是一个基于 Python、LangGraph 和 OpenAI 兼容协议模型服务的 Agent 底座项目。

当前状态：
- 阶段 1 已完成
- 阶段 2 开发中
- 已支持 CLI、HTTP API、多模态输入、工具调用、任务追踪、运行时配置中心和最小多 Agent 编排
- 当前自动化测试基线：`78 tests, OK`

## 核心能力

- 持续对话 CLI
- HTTP API
- 多模型接入
- 图片、音频、视频、文件输入与上传
- OCR / ASR / 视频探测 / 抽帧 / 抽音轨
- 工具注册与工具调用
- 统一鉴权
- 限流与幂等
- trace 查询
- 恢复告警查询
- 模型与工具的基础重试、熔断与降级
- router / debate / arbitration / critic / review 多角色工作流
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
- [阶段1最终验收结论单](docs/enterprise/阶段1最终验收结论单.md)
- [总体设计](docs/enterprise/总体设计.md)
- [需求规格说明书](docs/enterprise/需求规格说明书.md)
- [详细设计说明书](docs/enterprise/详细设计说明书.md)
- [数据库设计说明书](docs/enterprise/数据库设计说明书.md)
- [用户手册](docs/enterprise/用户手册.md)
- [组件设计说明](docs/enterprise/组件设计说明.md)
- [设计方案](docs/enterprise/设计方案.md)
- [功能清单](docs/enterprise/功能清单.md)
- [开发计划](docs/enterprise/开发计划.md)
- [测试报告](docs/enterprise/测试报告.md)
- [性能测试报告](docs/enterprise/性能测试报告.md)
- [运维手册](docs/enterprise/运维手册.md)
- [日志规范](docs/enterprise/日志规范.md)
- [操作指南](docs/enterprise/操作指南.md)
- [FAQ](docs/enterprise/FAQ.md)
- [培训材料](docs/enterprise/培训材料.md)
- [项目计划书](docs/enterprise/项目计划书.md)
- [周报](docs/enterprise/周报.md)
- [评审报告](docs/enterprise/评审报告.md)

架构规划资料：
- [架构文档索引](docs/architecture/README.md)
- [架构规划方案](docs/architecture/plans/)

其他索引：
- [API 文档索引](docs/api/README.md)
- [Prompt 文档索引](docs/prompts/README.md)
