# AgentOps Frontend Stack Final

## 一、文档目标

本文件用于明确 AgentOps 三端前端最终技术选型，作为：

- 前端架构基线
- 后续开发与重构的判断依据
- Codex / Cursor / AI 协作的统一输入
- 技术边界与职责划分说明

---

## 二、核心判断

AgentOps 的核心能力是：

- Agent 底座
- Trace 执行链路
- Observability
- AI 对话与工具调用

前端的职责是：

> 稳定、清晰、可扩展地承载这些能力，而不是成为项目的核心技术负担。

因此，前端选型必须遵循：

### 原则 1：核心体验自研，通用能力借力
- 核心页面与核心交互：自研
- 通用后台页面与基础组件：借助成熟框架

### 原则 2：避免同一端出现过多样式体系
每一端最多保留：
- 1 套主 UI 体系
- 1 套辅助组件体系

### 原则 3：不要为了“统一”而牺牲效率
三端不追求同一套 UI 框架，而追求：
- 每一端使用最适合自己的主流方案
- 在体验一致的前提下保持开发效率

---

## 三、最终选型总览

| 端 | 技术选型 | Tailwind |
|---|---|---|
| 管理后台（Web Admin） | React + TypeScript + Vite + Ant Design + 自研核心控制台 UI | ❌ 不使用 |
| 客户端（Chat Web） | React + TypeScript + Vite + shadcn/ui + Tailwind CSS + 自研核心交互 | ✅ 使用 |
| 移动端（Native App） | Expo + React Native + Tamagui | ❌ 不使用 |
| 数据层 | TanStack Query | - |

---

## 四、管理后台（Web Admin）

### 4.1 最终选型

- React
- TypeScript
- Vite
- Ant Design
- 自研后台设计系统
    - Token
    - Theme / Dark Mode
    - Density
    - Settings Panel
    - PageShell / Layout / Detail / Table 体系

---

### 4.2 页面职责划分

#### 使用 Ant Design 的页面
用于：
- CRUD 页面
- 表单页
- 配置页
- 简单列表页
- 工具型后台页面

#### 使用自研 UI 的页面
用于：
- Trace Console
- Observability Dashboard
- Task / Trace Detail
- Timeline / Log / Graph / Alert
- 其他核心控制台页面

---

### 4.3 为什么管理后台不使用 Tailwind

当前后台已经具备：

- 自研 token 系统
- 自研 theme / dark mode
- 自研 density 控制
- 分层样式体系
- Ant Design 作为 CRUD 加速器

如果再引入 Tailwind，会形成：

```text
自研 CSS + Ant Design + Tailwind
```

---

## 十二、设计协作与 UI 产出流程（Figma + MCP）

### 12.1 设计工具选型

- Figma（UI 设计与原型）
- MCP（Model Context Protocol，用于读取 Figma 结构数据）

---

### 12.2 使用目标

Figma + MCP 用于：

- UI 结构设计
- 组件层级拆分
- 间距与排版参考
- 设计与开发协同

而不是：

- 直接生成生产级前端代码
- 替代现有 UI 体系（Token / Theme / Component）

---

### 12.3 标准工作流

```text
Figma（设计稿）
   ↓
MCP（读取结构）
   ↓
前端实现（基于现有架构）
