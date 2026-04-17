# Phase 3 实施清单：融合 AgentOps 独有能力

## 一、阶段目标

本阶段目标：

> 把 AgentOps 的 Tool / Workflow / Trace / Task 融进聊天体验里。

必须完成：
- Tool Call 展示
- Tool Result 展示
- Workflow Step 展示
- Trace / Task 元信息展示
- Trace / Task 跳转入口
- 调试抽屉或侧板
- 运行过程可观测化

---

## 二、文件级改造清单

### A. Tool Call UI
新增或修改：
- `frontend-ai/src/components/chat/ToolCallCard.tsx`
- `frontend-ai/src/components/chat/ToolResultCard.tsx`
- `frontend-ai/src/components/chat/MessageItem.tsx`

职责：
- 展示工具开始、执行中、完成
- 展示工具名称、结果摘要、耗时、状态

---

### B. Workflow UI
新增或修改：
- `frontend-ai/src/components/chat/WorkflowStepList.tsx`
- `frontend-ai/src/components/chat/WorkflowStepItem.tsx`
- `frontend-ai/src/stores/chatRuntimeStore.ts`

职责：
- 展示 workflow step
- 标识状态：
  - `pending`
  - `running`
  - `completed`
  - `failed`

---

### C. Trace / Task 联动
新增或修改：
- `frontend-ai/src/components/chat/TraceMetaBar.tsx`
- `frontend-ai/src/components/chat/DebugDrawer.tsx`
- `frontend-ai/src/services/agentops/traces.ts`
- `frontend-ai/src/services/agentops/tasks.ts`

职责：
- 展示 `trace_id` / `task_id`
- 提供跳转入口
- 在调试抽屉展示运行元信息

---

### D. 流式协议扩展
修改：
- `frontend-ai/src/adapters/sse.ts`
- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/hooks/useChatStream.ts`

新增支持事件：
- `tool_start`
- `tool_result`
- `workflow_step`
- `trace_link`
- `task_link`
- `warning`
- `error`

---

### E. 后端接口与事件增强
新增或修改：
- `app/presentation/api/routes/chat.py`
- `app/application/services/task_service.py`
- `app/infrastructure/trace/service.py`
- 与 workflow / tool event 输出相关的服务文件

目标：
- 聊天 SSE 中透出工具事件
- 透出 workflow step 事件
- 透出 trace/task 元信息
- 保持协议稳定

---

## 三、验收标准

- 用户能看到工具调用过程
- 用户能看到 workflow step 状态变化
- 聊天页能展示 trace/task 信息
- 能从聊天页跳到详情页
- 运行过程不再是黑盒
