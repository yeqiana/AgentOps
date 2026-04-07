# AGENTS.md

## 项目定位

这是一个基于 Python、LangGraph 和 OpenAI 兼容协议模型服务的 Agent 底座项目。

当前项目已完成阶段 1，定位为：
- 分析型 Agent 后端底座
- 支持 CLI 与 HTTP API
- 支持多模态输入、上传、工具后处理、任务追踪与排障
- 后续阶段 2 明确建设：统一鉴权、失败重试、trace service
- 后续阶段 3 明确建设：可视化 trace 与观测能力
- 后续规划已补充：配置治理、版本治理、安全策略、限流与配额、成本治理

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
