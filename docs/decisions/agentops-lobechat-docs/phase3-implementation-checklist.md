# Phase 3 实施清单：融合 AgentOps 独有能力

## 1. 阶段目标

本阶段不再只是做普通聊天产品，而是把 AgentOps 的差异化能力接入前端体验。

必须完成：

- Tool Call 展示
- Tool Result 展示
- Workflow Step 展示
- Trace / Task 元信息展示
- Trace / Task 跳转入口
- 调试抽屉或运行态侧板

可以后置：

- 完整 Trace Console 嵌入
- Alert 中心整合
- 工作流大屏
- 细粒度 RBAC 页面权限

---

## 2. 文件级改造清单

### 2.1 Tool Call UI

#### 新增或修改

- `frontend-ai/src/components/chat/ToolCallCard.tsx`
- `frontend-ai/src/components/chat/ToolResultCard.tsx`
- `frontend-ai/src/components/chat/MessageItem.tsx`

#### 职责

- 展示工具开始、执行中、完成状态
- 展示工具名称、摘要、耗时、结果摘要
- 作为 assistant 消息中的运行态片段插入渲染

---

### 2.2 Workflow Step UI

#### 新增或修改

- `frontend-ai/src/components/chat/WorkflowStepList.tsx`
- `frontend-ai/src/components/chat/WorkflowStepItem.tsx`
- `frontend-ai/src/stores/chatRuntimeStore.ts`

#### 职责

- 记录并展示 workflow step
- 支持 `pending / running / completed / failed` 状态
- 将文本消息与运行态事件分离管理

---

### 2.3 Trace / Task 联动

#### 新增或修改

- `frontend-ai/src/components/chat/TraceMetaBar.tsx`
- `frontend-ai/src/components/chat/DebugDrawer.tsx`
- `frontend-ai/src/services/agentops/traces.ts`
- `frontend-ai/src/services/agentops/tasks.ts`

#### 职责

- 展示 `trace_id` / `task_id`
- 提供跳转到详情页的入口
- 在调试抽屉中显示最近一次运行的元数据与事件摘要

---

### 2.4 SSE 事件扩展

#### 修改

- `frontend-ai/src/adapters/sse.ts`
- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/hooks/useChatStream.ts`

#### 新增支持事件

- `tool_start`
- `tool_result`
- `workflow_step`
- `trace_link`
- `task_link`
- `warning`
- `error`

#### 建议事件结构

```json
{ "type": "tool_start", "name": "search_code" }
{ "type": "tool_result", "name": "search_code", "summary": "命中 12 个文件" }
{ "type": "workflow_step", "name": "plan_generation", "status": "running" }
{ "type": "workflow_step", "name": "plan_generation", "status": "completed" }
{ "type": "trace_link", "trace_id": "xxx" }
{ "type": "task_link", "task_id": "yyy" }
```

---

### 2.5 运行态状态管理

#### 新增或修改

- `frontend-ai/src/stores/chatRuntimeStore.ts`
- `frontend-ai/src/hooks/useRuntimeEvents.ts`

#### 职责

- 保存最近一次聊天的运行态事件
- 区分普通消息文本与系统事件
- 为 Tool / Workflow / Trace / Task UI 提供状态来源

---

### 2.6 后端接口与事件增强

#### 新增或修改

- `app/presentation/api/routes/chat.py`
- `app/application/services/task_service.py`
- `app/infrastructure/trace/service.py`
- 与 workflow / tool 事件输出相关的服务文件

#### 目标

- 聊天 SSE 中透出工具事件
- 聊天 SSE 中透出 workflow 事件
- 聊天 SSE 中透出 trace / task 元信息
- 保证事件顺序与结构稳定

---

## 3. 实施顺序

1. 扩展 `chat.ts` 与 `sse.ts` 对更多事件的支持
2. 建立 `chatRuntimeStore.ts`
3. 新增 Tool 与 Workflow 组件
4. 将运行态信息接入 `MessageItem.tsx` 或聊天页侧板
5. 新增 `TraceMetaBar.tsx` 与 `DebugDrawer.tsx`
6. 联调 `trace/task` 查询接口与增强版 SSE 事件
7. 完成跳转与调试体验

---

## 4. 验收标准

- Tool 调用过程可见
- Workflow Step 状态可见
- `trace_id` / `task_id` 信息可见
- 可跳转到详情页
- 聊天过程不再是黑盒

---

## 5. Codex 输出要求

Phase 3 完成后，必须输出：

- 新增文件清单
- 修改文件清单
- 运行态与调试能力接入说明
- 预览入口
- 本地启动方式
- 已知问题
