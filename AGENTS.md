# AGENTS.md

## 项目定位

- 这是一个基于 Python、LangGraph 和 OpenAI 兼容协议的 Agent 底座项目
- 阶段 1 已完成，阶段 2 正在开发
- 当前重点是治理底座、多 Agent 编排、运行时配置中心、数据库规范、可排障能力、请求路由中台和异步任务深化
- 当前已支持 CLI 与 API 的流式对话输出

## 结构约束

- 保留五层结构：`presentation / application / domain / workflow / infrastructure`
- LLM 能力放在 `app/infrastructure/llm/`
- 多媒体解析放在 `app/infrastructure/media/`
- 上传与存储放在 `app/infrastructure/storage/`
- 工具能力放在 `app/infrastructure/tools/`
- 异步任务与队列预留放在 `app/infrastructure/queue/`
- API 能力放在 `app/presentation/api/`
- workflow 策略相关代码放在 `app/workflow/`
- 测试按 `tests/unit`、`tests/integration`、`tests/e2e` 分层

## 数据库约束

- 表名统一使用 `xxx_xxx`
- 系统表统一使用 `sys_` 前缀
- 业务表统一使用 `biz_` 前缀
- 禁止外键约束
- 所有表必须有主键
- 所有表必须包含：
  - `created_by`
  - `updated_by`
  - `created_at`
  - `updated_at`
  - `ext_data1`
  - `ext_data2`
  - `ext_data3`
  - `ext_data4`
  - `ext_data5`
- 结构版本统一由 `sys_schema_version` 维护

## 文档规则

- `README.md` 只保留项目说明、能力、目录、启动方式和文档入口
- 企业级正式文档主目录是 `docs/enterprise/`
- 架构规划资料主目录是 `docs/architecture/plans/`
- 同类正式文档只保留一套主版本
- 每累计 3 次代码或结构改动，更新一次 `README.md` 和 `AGENTS.md`
- 如果改动显著影响结构、接口、运行方式、测试方式或目录布局，则立即更新

## 提示词资产归档规则

- 对项目有长期价值的提示词、任务描述、架构要求或实现约束，需要归档到 `docs/ai-prompts/`
- 归档内容应具备可检索性，不要使用无语义文件名
- 归档方向建议按 `frontend / backend / architecture / product` 分类

## 当前阶段重点

- 阶段 2 已落地：
  - 请求路由中台最小版：`request_route_service`
  - 路由决策持久化、查询与统计
  - 路由策略预览：`/routing/preview`
  - 路由配置模板与校验：`/routing/config/template` + `routing` scope key/type validation
  - 统一鉴权
  - 最小 RBAC
  - 主体授权关系回查
  - 角色权限矩阵查询
  - 限流与幂等
  - trace service
  - trace 统计聚合查询：`/traces/stats`
  - 恢复告警记录、查询与 trace 关联查询
  - trace 聚合摘要查询：`/traces/{trace_id}/summary`
  - trace 时间线聚合查询：`/traces/{trace_id}/timeline`
  - 告警统计聚合：`/alerts/stats`
  - 基础重试与熔断降级
  - 配置化恢复策略
  - `router / debate / arbitration / critic / review` 最小多角色编排
  - 数据库驱动运行时配置中心
  - 运行时配置变更审计与回查
  - 数据库驱动角色注册
  - 正式角色协议：`support / challenge / planner / executor / arbitration / critic / reviewer`
  - 可切换执行协议：`delegated / standard`
  - 流式对话输出：CLI 流式打印，API `SSE` 流式返回
  - 异步任务深化：`/tasks/submit` + 本地后台执行器 + `queued/running/completed/failed` 状态链
  - 异步任务运行时快照：`/tasks/runtime`
  - 异步任务取消：`/tasks/{task_id}/cancel`
  - 异步任务重试：`/tasks/{task_id}/retry`
  - 任务状态统计：`/tasks/stats`
  - 任务聚合摘要：`/tasks/{task_id}/summary`
  - 会话聚合摘要：`/sessions/{session_id}/summary`
  - 任务事件持久化与查询：`biz_task_event`、`/tasks/{task_id}/events`
  - 任务状态聚合统计：`/tasks/stats`
  - 控制台聚合总览：`/operations/overview`
- 阶段 2 后续继续建设：
  - 失败恢复增强
  - 策略中心深化
  - 多 Agent 角色协议扩展
  - 异步任务体系深化
- 阶段 3 规划：
  - 可视化 trace
  - 观测与监控面板
