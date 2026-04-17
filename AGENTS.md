# AGENTS.md

## frontend-vue

- `frontend-vue/` is the Vue 3 + Element Plus frontend workspace for Figma-driven UI implementation.
- Current route entry: `/chatgpt-redesign`.
- Keep generated `node_modules/` and `dist/` out of commits.

## 项目定位

- 这是一个基于 Python、LangGraph 和 OpenAI 兼容协议的 Agent 底座项目
- 阶段 1 已完成并结项
- 阶段 2 已完成并结项
- 阶段 3 尚未启动
- 当前重点从阶段 2 收尾转向阶段 3 规划与前置开发
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

## 当前阶段状态

- 阶段 1 已完成：
  - 分析型 Agent 底座闭环
  - 多模态输入与工具链
  - 数据库、API、日志与测试基础
- 阶段 2 已完成：
  - 请求路由中台最小版
  - 路由决策持久化、查询、统计与预览，任务主记录同步保留 `route_source`
  - 路由配置模板与校验：`/routing/config/template` + `routing` scope key/type validation
  - 路由配置审计查询：`/routing/config/events`
  - 路由规则版本快照：`/routing/config/versions` + `current_version`
  - 路由版本回滚：`POST /routing/config/versions/{version_no}/restore`
  - 路由权限细分：`routing.read / routing.preview / routing.manage`
  - 统一鉴权与最小 RBAC
  - 主体授权关系回查
  - 角色权限矩阵查询
  - 限流与幂等
  - trace service
  - trace 统计、摘要、时间线、图谱与告警关联查询
  - 控制台 trace 查看器聚合查询：`/console/traces/{trace_id}/viewer`
  - 告警统计聚合
  - 基础重试与熔断降级
  - 配置化恢复策略
  - `router / debate / arbitration / critic / review` 最小多角色编排
  - 数据库驱动运行时配置中心
  - 运行时配置变更审计与回查
  - 数据库驱动角色注册
  - 正式角色协议：`support / challenge / planner / executor / arbitration / critic / reviewer`
  - 可切换执行协议：`delegated / standard`
  - 流式对话输出：CLI 流式打印，API `SSE` 流式返回
  - 异步任务深化：提交、运行、取消、重试、事件追踪、运行时快照
  - 任务状态统计、任务聚合摘要、会话聚合摘要
  - 控制台聚合总览
- 阶段 3 规划：
  - 可视化 trace
  - 观测与监控面板
  - 完整异步任务平台
  - 完整权限治理体系
  - 成本与配额治理
  - 模型路由与策略引擎

## Git 提交规则

- 未经用户明确说“现在提交”，不要自动执行 `git commit`
- 提交前必须先检查：
  - `git status --short`
  - `git diff --stat`
- 一次提交只对应一个线程或一个明确目标
- 禁止使用 `git add .`
- 必须按文件精确 add
- 禁止提交：
  - `.env / .env.local`
  - 本地日志
  - 临时 txt
  - 构建产物
  - 与当前线程无关的改动
- 在准备提交时，先输出：
  1. 建议提交的文件
  2. 不应提交的文件
  3. 建议的 commit message
- 只有在用户明确确认后，才执行 `git commit`

## 继承说明

- 通用协作规则、开发流程、测试要求、风险检查、提交规则、设计规范等，统一遵循项目同级全局 [AGENTS.md](/D:/workspace/YeQianWorkSpace/Agent/AGENTS.md)
- 本文件仅保留 AgentOps 项目特有的定位、结构、数据库、文档与阶段约束
