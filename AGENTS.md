# AGENTS.md

## 项目定位

这是一个基于 Python、LangGraph 和 OpenAI 兼容协议模型服务的 Agent 底座项目。

当前项目已完成阶段 1，定位为：
- 分析型 Agent 后端底座
- 支持 CLI 与 HTTP API
- 支持多模态输入、上传、工具后处理、任务追踪与排障
- 阶段 2 已启动，已落地统一鉴权、限流/幂等、trace service、基础重试与熔断降级骨架，以及 router_node / debate_node / arbitration_node / critic_node / review_node 最小多角色编排能力
- 阶段 2 当前已补充 workflow 策略注册中心、`/workflow/config` 查询接口，以及工具白名单/上传限制的安全策略控制
- 后续阶段 2 明确建设：失败恢复增强、策略中心深化、多 Agent 编排扩展
- 后续阶段 3 明确建设：可视化 trace 与观测能力
- 后续规划已补充：配置治理、版本治理、安全策略、限流与配额、成本治理
- 阶段 2 当前已新增数据库驱动配置中心：
  - `sys_runtime_config`
  - `GET /config/runtime`
  - `PUT /config/runtime`
  - `/workflow/config` 与 `/security/config` 已改为数据库覆盖优先、环境变量兜底
  - Workflow 角色注册已扩展为 `support/challenge/arbitration/critic`

## 当前文档体系

### 企业级正式文档

位于：
- `docs/enterprise/`

包含：
- 阶段1最终验收结论单
- 总体设计
- 需求规格说明书
- 详细设计说明书
- 数据库设计说明书
- 用户手册
- 组件设计说明
- 设计方案
- 功能清单
- 开发计划
- 测试报告
- 性能测试报告
- 运维手册
- 日志规范
- 操作指南
- FAQ
- 培训材料
- 项目计划书
- 周报
- 评审报告

### 架构规划资料

位于：
- `docs/architecture/plans/`

### 索引文档

- `README.md`
- `AGENTS.md`
- `docs/enterprise/README.md`
- `docs/architecture/README.md`
- `docs/api/README.md`
- `docs/prompts/README.md`

## 文档保留策略

保留：
- 企业级正式文档
- 架构规划资料
- 索引型 README

已替换：
- 原 `docs/architecture/reviews/` 下阶段性评审/使用/功能清单文档，已由 `docs/enterprise/` 正式文档替代

原则：
- 同类正式文档只保留一套主版本
- 阶段性草稿和正式版冲突时，以正式版为准

## 结构约束

- 保留五层结构
- LLM 相关能力优先放 `app/infrastructure/llm/`
- 多媒体解析优先放 `app/infrastructure/media/`
- 上传落盘和对象存储优先放 `app/infrastructure/storage/`
- 工具调用优先放 `app/infrastructure/tools/`
- API 能力优先放 `app/presentation/api/`
- workflow 策略优先放 `app/workflow/policies.py` 或后续 `app/workflow/policies/`
- 数据库表命名规则：统一使用 `xxx_xxx` 格式
- 数据库系统表与授权认证表统一使用 `sys_` 前缀
- 数据库业务表统一使用 `biz_` 前缀
- 数据库必须维护 `sys_schema_version` 版本表
- 数据库运行时配置统一落 `sys_runtime_config`
- 数据库禁止使用外键，关联关系由应用层与索引策略维护
- 所有数据库表必须包含主键与 5 个审计扩展字段：
  - `created_by`
  - `updated_by`
  - `created_at`
  - `updated_at`
  - `ext_data1`
  - `ext_data2`
  - `ext_data3`
  - `ext_data4`
  - `ext_data5`
- 测试按 `unit / integration / e2e` 分层

## 文档同步规则

- 后续每累计 3 次代码改动或结构改动，必须同步更新 `README.md` 和 `AGENTS.md`
- 如果某次改动已经显著影响结构、运行方式、输入能力、测试方式或目录布局，则必须立即更新文档

## 使用建议

对外评审、交付、培训时，优先引用：
- `docs/enterprise/阶段1最终验收结论单.md`
- `docs/enterprise/评审报告.md`
- `docs/enterprise/使用指南` 对应文档为 `docs/enterprise/用户手册.md` 和 `docs/enterprise/操作指南.md`
- `docs/enterprise/功能清单.md`
