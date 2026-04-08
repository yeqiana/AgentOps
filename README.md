# Agent Base Runtime

这是一个基于 Python、LangGraph 和 OpenAI 兼容协议模型服务的 Agent 底座项目。

## 当前状态

- 阶段 1 已完成
- 阶段 2 已启动，治理底座与最小编排能力已落地
- CLI、HTTP API、多模态输入、工具网关、数据库、排障链路均已落地
- 当前自动化测试基线：`74 tests, OK`
- 阶段 2 已落地：统一鉴权、失败重试、熔断降级、trace service、router_node、debate_node、arbitration_node、critic_node、review_node、安全策略白名单与上传限制配置
- 阶段 3 已明确纳入：可视化 trace 与观测面板
- 规划已补充：配置治理、版本治理、安全策略、限流与配额、成本治理

## 快速入口

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

## 核心能力

- 持续对话 CLI
- HTTP API
- 统一鉴权骨架
- 限流与幂等基础能力
- Trace 查询接口
- 模型调用基础重试
- 工具调用基础重试
- 模型熔断与快速降级
- 工具熔断与快速降级
- 路由决策节点
- 多 Agent 辩论节点
- 仲裁节点
- 批评代理节点
- 结果复核节点
- Workflow 策略注册中心
- `/workflow/config` 策略查询接口
- `/security/config` 安全配置查询接口
- 数据库业务表 / 系统表命名规范
- 数据库无外键治理规范
- 所有表统一主键与 5 个审计扩展字段
- 上传型多模态输入
- 工具白名单控制
- 上传大小限制与上传类型白名单
- PDF 解析
- 视频抽帧 / 抽音轨
- OCR / ASR
- 任务、资产、工具结果查询

## 文档索引

### 企业级正式文档

- [企业级文档总索引](docs/enterprise/README.md)
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

### 架构规划资料

- [架构文档索引](docs/architecture/README.md)
- [适合这个项目下一阶段落地的精简目录方案](docs/architecture/plans/适合这个项目下一阶段落地的精简目录方案.md)
- [企业级完整版目录方案](docs/architecture/plans/企业级完整版目录方案.md)
- [数据库表设计建议](docs/architecture/plans/数据库表设计建议.md)
- [当前底座成熟度评估](docs/architecture/plans/当前底座成熟度评估.md)
- [阶段1的详细开发计划清单](docs/architecture/plans/阶段1的详细开发计划清单.md)

### 其他索引

- [API 文档索引](docs/api/README.md)
- [Prompt 文档索引](docs/prompts/README.md)

## 文档维护规则

- 每累计 3 次代码或结构改动，必须同步更新 `README.md` 和 `AGENTS.md`
- 如果改动显著影响结构、运行方式、输入能力、测试方式或目录布局，则必须立即更新

## 数据库规范

- 表名统一使用 `xxx_xxx` 格式。
- 系统与授权认证相关表统一使用 `sys_` 前缀。
- 业务执行相关表统一使用 `biz_` 前缀。
- 当前核心表为：
  - `sys_user`
  - `sys_schema_version`
  - `sys_request_trace`
  - `biz_session`
  - `biz_message`
  - `biz_asset`
  - `biz_task`
  - `biz_tool_result`
- 当前数据库层不使用外键约束，关联关系由应用层与索引策略维护。
- 所有表必须包含：
  - 主键
  - `created_by`
  - `updated_by`
  - `created_at`
  - `updated_at`
  - `ext_data1`
  - `ext_data2`
  - `ext_data3`
  - `ext_data4`
  - `ext_data5`
- 当前已按 SQLite 落地索引；分区、排序、分库分表策略以 PostgreSQL/MySQL 生产化方案为后续演进目标。
- 当前已引入 `sys_schema_version` 作为数据库结构版本表，后续迁移需基于版本演进。

## 阶段 1 收口说明

- `docs/enterprise/` 现在是企业级正式文档主版本目录
- 原 `docs/architecture/reviews/` 下重复的阶段性评审文档已移除
- 当前阶段 1 最终验收主依据为 `docs/enterprise/阶段1最终验收结论单.md`

## 阶段 2 增量进展

- 已补数据库驱动运行时配置中心：
  - 系统表 `sys_runtime_config`
  - 接口 `GET /config/runtime`
  - 接口 `PUT /config/runtime`
- `/workflow/config` 与 `/security/config` 现在优先读取数据库覆盖配置，环境变量作为兜底默认值
- 工具白名单与 workflow 角色策略已进入统一配置治理链
- Workflow 角色注册已扩展为：
  - `support_role`
  - `challenge_role`
  - `arbitration_role`
  - `critic_role`
- 当前自动化测试基线已更新为 `74 tests, OK`
