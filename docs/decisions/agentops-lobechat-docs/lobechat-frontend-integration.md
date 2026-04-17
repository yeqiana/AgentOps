# Lobe 风格前端接入 AgentOps 总体实施方案

## 1. 文档目的

本文档用于定义：

- 为什么接入 Lobe 风格前端，而不是直接搬运 LobeChat 全栈
- 三阶段实施边界、先后顺序与验收标准
- 前端改造与后端接口演进之间的对应关系
- 交付给 Codex 时应遵循的工程约束

本文档是总纲文档。

配套文档：

- `phase1-implementation-checklist.md`
- `phase2-implementation-checklist.md`
- `phase3-implementation-checklist.md`
- `backend-api-sse-protocol-checklist.md`

---

## 2. 背景

当前 AgentOps 已具备以下底座能力：

- 多模型路由与 Provider 切换
- Workflow 编排
- Tool 调用
- Trace / Task / Alert 体系
- CLI / API 双入口
- 文件上传与资产分析能力

当前缺口主要在 Chat Web 前端体验。

Lobe 风格前端适合复用的部分主要是：

- Chat UI 结构
- 消息列表交互
- 输入框体验
- 会话页布局
- 模型切换交互
- 现代聊天产品的前端视觉语言

但不应直接接入其原有后端能力，因为其默认依赖通常包含：

- 内建 API / Runtime
- 用户认证体系
- 会话持久化逻辑
- 插件、知识库、市场等完整产品能力

这些能力与 AgentOps 当前底座边界并不一致。

---

## 3. 核心决策

### 3.1 采用方案

采用：

**Lobe 风格前端体验 + AgentOps 自有后端 API + 前端 Adapter 层**

即：

```text
frontend-ai (Lobe 风格 UI)
        ↓
services/agentops/* + adapters/sse.ts
        ↓
AgentOps Backend API
        ↓
Model / Workflow / Tool / Trace / Task
```

### 3.2 不采用方案

明确不采用：

- 不接入 Lobe 原生后端
- 不做大而全的 LobeChat API 兼容层
- 不长期维护整套 Lobe fork
- 不把“开发代理转发”当成正式架构方案

### 3.3 核心原则

- 复用 UI，不复用其后端契约
- 保留聊天体验，重写数据层
- 先做主链路，再做会话与文件，再做 AgentOps 特有能力可视化
- 所有 Agent 运行态元数据，最终都以 AgentOps 协议为准

---

## 4. 实施总览

### 4.1 Phase 1：最小可运行聊天闭环

目标：

- `/chat` 页面可访问
- 消息可发送到 AgentOps
- Assistant 回复可通过 SSE 流式渲染
- 模型列表可加载
- `trace_id` / `task_id` 可保存在前端状态中

不包含：

- 历史会话持久化
- 文件上传
- Tool / Workflow 可视化
- Trace / Task 页面联动

### 4.2 Phase 2：会话、文件与消息能力补齐

目标：

- 会话列表与会话切换
- 历史消息恢复
- 新建会话
- 文件上传
- 消息状态与附件能力增强

不包含：

- 完整知识库
- 插件市场
- 复杂 RBAC 联动
- 深度调试视图

### 4.3 Phase 3：融合 AgentOps 独有运行态能力

目标：

- Tool Call / Tool Result 展示
- Workflow Step 展示
- Trace / Task 元信息展示与跳转
- 调试抽屉 / 运行态侧板
- 使聊天过程从黑盒变为可观察

---

## 5. 前端目标结构

建议优先落在 `frontend-ai`，并尽量并入现有结构。

推荐目标结构：

```text
frontend-ai/
└─ src/
   ├─ app/
   ├─ pages/chat/
   ├─ components/chat/
   ├─ services/agentops/
   ├─ adapters/
   ├─ hooks/
   ├─ stores/
   ├─ lib/
   └─ types/
```

建议重点目录职责：

- `pages/chat/`：聊天页容器
- `components/chat/`：消息、输入、会话栏、运行态组件
- `services/agentops/`：前端调用 AgentOps 的 API 适配层
- `adapters/`：SSE / 事件协议转换
- `stores/`：聊天状态、会话状态、运行态状态
- `types/`：通用消息与运行事件类型

---

## 6. 后端演进总览

### 6.1 Phase 1 最小接口

- `POST /api/chat/stream`
- `GET /api/models`

### 6.2 Phase 2 补充接口

- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions`
- `POST /api/files/upload`

### 6.3 Phase 3 扩展事件与查询接口

建议至少支持：

- 聊天 SSE 中输出 `tool_start`
- 聊天 SSE 中输出 `tool_result`
- 聊天 SSE 中输出 `workflow_step`
- 聊天 SSE 中输出 `trace_link`
- 聊天 SSE 中输出 `task_link`
- `GET /api/traces/{trace_id}`
- `GET /api/tasks/{task_id}`

---

## 7. 三阶段对应关系

### 7.1 前端与后端的依赖顺序

- Phase 1：前端聊天页依赖最小聊天流式接口
- Phase 2：前端会话与附件依赖会话、文件接口
- Phase 3：前端运行态组件依赖更丰富的 SSE 事件与详情查询接口

### 7.2 协议优先级

若 UI 与协议设计冲突，优先保证：

1. 后端协议稳定
2. 前端 Adapter 可兼容
3. UI 再适配协议结果

避免反向为了 UI 细节频繁变更后端事件结构。

---

## 8. 对 Codex 的执行约束

交给 Codex 时必须明确：

- 先分析仓库现状与等价文件，再修改代码
- 优先复用现有 `frontend-ai` 结构，不要平地起新工程
- 不要尝试接入 Lobe 原生后端体系
- Phase 1 必须先独立跑通，不得混入 Phase 2 / 3 的复杂逻辑
- 每个阶段完成后都要输出：
  - 新增文件清单
  - 修改文件清单
  - 预览入口
  - 启动方式
  - 风险项

---

## 9. 阶段验收总表

### 9.1 Phase 1 验收

- `/chat` 页面可访问
- 可以切换模型
- 可以发送消息
- 回复为流式渲染
- `trace_id` / `task_id` 已保存在前端状态
- 页面无阻断性报错

### 9.2 Phase 2 验收

- 左侧会话栏可用
- 历史会话可恢复
- 可新建会话
- 文件可上传
- 消息附件可展示
- 失败消息可反馈并重试

### 9.3 Phase 3 验收

- Tool 调用过程可见
- Workflow 步骤状态可见
- Trace / Task 信息可见
- 可从聊天页跳转详情
- 调试信息不再是黑盒

---

## 10. 文档使用方式

建议实际交付顺序：

1. 先将本文档作为总纲交给 Codex
2. 再按阶段分别附带：
   - Phase 1 实施清单
   - Phase 2 实施清单
   - Phase 3 实施清单
   - 后端 API / SSE 协议清单
3. 让 Codex 一次只实施一个阶段
4. 每阶段结束后再进入下一阶段

---

## 11. 结论

本方案的本质不是“集成 LobeChat”，而是：

**借 Lobe 风格前端壳，强化 AgentOps 自己的 Chat 产品能力。**

因此最终目标不是成为另一个 Lobe 产品分支，而是：

- 前端体验更成熟
- 后端能力仍完全掌握在 AgentOps 手里
- 协议、运行态和调试能力都为 AgentOps 服务
