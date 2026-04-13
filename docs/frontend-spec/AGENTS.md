# AgentOps Frontend AGENTS Guide

> This document is a **guideline for AI agents (Codex/Cursor)**.
> It defines how to use the frontend specification system.
> It is NOT an execution script.

## 文档目的

本文件用于指导 Codex / Cursor 等 AI Agent 在前端设计、实现与验收过程中，如何正确引用和使用 AgentOps 前端规范体系。

前端规范体系是参考体系，不是执行脚本。AI Agent 应按当前任务需要选择性读取相关规范文件，不应每次全量加载。

## 使用原则

- 只引用当前任务相关的规范文件。
- 优先使用定向引用，避免加载整个 `docs/frontend-spec/` 目录。
- 规范用于辅助判断和约束实现，不用于重复解释规范正文。
- 输出应聚焦当前任务，不扩展无关范围。
- 保持已确认的产品方向、命名、目录结构和文件编号。

## 使用方式

### 设计阶段

根据任务类型引用相关规范，用于确定页面结构、交互模型、布局方式、组件边界和验收标准。

### 实现阶段

按需引用相关规范文件指导代码或文档修改。除非用户明确要求，不要复述完整规范内容。

### 验收阶段

使用相关规范检查结果是否符合布局、状态、交互、密度、命名和工程约定。

## 快速引用表

[WEB-LAYOUT] → `03-web-admin/31-layout-navigation.md`  
[WEB-TABLE] → `03-web-admin/33-table-list-page-spec.md`  
[WEB-DASHBOARD] → `03-web-admin/32-dashboard-spec.md`  
[WEB-FORM] → `03-web-admin/34-form-config-page-spec.md`  
[WEB-DETAIL] → `03-web-admin/35-detail-page-spec.md`  
[WEB-TRACE] → `03-web-admin/36-trace-observability-page-spec.md`  
[WEB-PERMISSION] → `03-web-admin/37-permission-security-state-spec.md`  
[WEB-DENSITY] → `03-web-admin/38-responsive-density-spec.md`  

[ENG-ARCH] → `02-engineering/20-frontend-architecture.md`  
[ENG-PROJECT] → `02-engineering/21-project-structure.md`  
[ENG-CONFIG] → `02-engineering/22-config-system.md`  
[ENG-COMP] → `02-engineering/23-component-development-spec.md`  
[ENG-PAGE] → `02-engineering/24-page-development-spec.md`  
[ENG-API-STATE] → `02-engineering/25-api-state-spec.md`  
[ENG-AI-COLLAB] → `02-engineering/26-codex-collaboration-spec.md`  
[ENG-ACCEPTANCE] → `02-engineering/27-acceptance-checklist.md`  

[FOUND-TOKEN] → `01-foundation/10-design-tokens.md`  
[FOUND-COLOR] → `01-foundation/11-color-system.md`  
[FOUND-TYPE] → `01-foundation/12-typography.md`  
[FOUND-SPACING] → `01-foundation/13-spacing-radius-shadow.md`  
[FOUND-STATE] → `01-foundation/14-state-system.md`  
[FOUND-FEEDBACK] → `01-foundation/15-feedback-system.md`  
[FOUND-A11Y] → `01-foundation/16-accessibility.md`  
[FOUND-CONTENT] → `01-foundation/17-content-writing.md`  

[OVERVIEW] → `00-overview/00-AgentOps-frontend-spec-overview.md`  
[PRINCIPLES] → `00-overview/01-design-principles.md`  
[PRODUCT-FORM] → `00-overview/02-product-form-classification.md`  

## 引用规则

- 布局类任务引用 `[WEB-LAYOUT]`。
- 表格页或列表页任务引用 `[WEB-TABLE]`、`[ENG-PAGE]`、`[FOUND-STATE]`。
- Dashboard 页面任务引用 `[WEB-DASHBOARD]`、`[WEB-LAYOUT]`、`[WEB-DENSITY]`。
- 表单页或配置页任务引用 `[WEB-FORM]`、`[ENG-CONFIG]`、`[FOUND-FEEDBACK]`。
- 详情页任务引用 `[WEB-DETAIL]`、`[WEB-LAYOUT]`、`[FOUND-STATE]`。
- Trace 或可观测页面任务引用 `[WEB-TRACE]`、`[WEB-LAYOUT]`、`[WEB-DENSITY]`。
- 组件实现任务引用 `[ENG-COMP]`；仅在涉及视觉或状态行为时补充基础层规范。
- 页面实现任务引用 `[ENG-PAGE]`，并补充对应 Web Admin 页面类型规范。
- API 与状态管理任务引用 `[ENG-API-STATE]`。
- 验收任务引用 `[ENG-ACCEPTANCE]`，并补充对应页面类型规范。

## 禁止事项

- 不要每次加载完整规范体系。
- 不要重复解释规范，除非用户明确要求解释。
- 不要把本文档当作执行脚本。
- 不要把本文档改写为 Step 1 / Step 2 形式的任务清单。
- 未经明确要求，不要创建或扩写预留目录下的正文文件。
- 不要修改前端规范体系的文件编号或目录名称。
- 不要用通用 UI 假设覆盖已确认的产品方向。

## 预留范围

以下目录为后续扩展预留。除非用户明确要求，本阶段不要扩写：

- `04-mobile-admin/`
- `05-ai-chat-client/`
- `06-gen-creative-platform/`

## 输出要求

AI Agent 使用本文档时，应保持输出聚焦：

- 只引用相关规范 key 或文件。
- 输出具体变更或验收结果。
- 避免大段复述规范正文。
- 严格遵守当前任务边界。
