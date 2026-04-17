# Phase 1 实施清单：最小可运行聊天闭环

## 1. 阶段目标

本阶段只解决最小聊天闭环。

必须完成：

- `/chat` 页面可访问
- 用户输入后可请求 AgentOps
- Assistant 回复支持 SSE 流式展示
- 模型列表可加载
- `trace_id` / `task_id` 可保存到前端状态
- 提供明确预览入口

本阶段不做：

- 会话持久化
- 文件上传
- Tool / Workflow UI
- Trace / Task 深度联动
- 权限体系
- 全站接入

---

## 2. 实施范围

建议目录：

```text
frontend-ai/src/
├─ pages/chat/
├─ components/chat/
├─ services/agentops/
├─ adapters/
├─ hooks/
├─ stores/
├─ lib/
└─ types/
```

优先复用现有等价文件；若无，则新增。

---

## 3. 文件级改造清单

### 3.1 页面与路由

#### 新增或修改

- `frontend-ai/src/pages/chat/ChatPage.tsx`
- `frontend-ai/src/app/router/index.tsx` 或等价路由入口
- `frontend-ai/src/routes/index.tsx` 或等价路由文件

#### 职责

- 挂载 `/chat`
- 组织页面结构：Header / MessageList / ChatInput
- 页面顶部可显示当前模型与 `trace_id`
- 开发环境下可直接访问，不强依赖复杂权限守卫

---

### 3.2 聊天基础组件

#### 新增或修改

- `frontend-ai/src/components/chat/ChatLayout.tsx`
- `frontend-ai/src/components/chat/MessageList.tsx`
- `frontend-ai/src/components/chat/MessageItem.tsx`
- `frontend-ai/src/components/chat/ChatInput.tsx`
- `frontend-ai/src/components/chat/ModelSelector.tsx`

#### 职责

- `ChatLayout.tsx`：负责聊天页整体布局、滚动区与输入区固定
- `MessageList.tsx`：渲染消息数组并自动滚动到底部
- `MessageItem.tsx`：渲染单条消息，至少支持 `user` 与 `assistant`
- `ChatInput.tsx`：输入、发送、回车提交、streaming 禁用状态
- `ModelSelector.tsx`：加载并切换当前模型

---

### 3.3 状态管理

#### 新增或修改

- `frontend-ai/src/stores/chatStore.ts`

#### 最低状态字段

- `messages`
- `currentModel`
- `isStreaming`
- `traceId`
- `taskId`

#### 最低方法

- `setModel`
- `addUserMessage`
- `createAssistantPlaceholder`
- `appendAssistantDelta`
- `finalizeAssistantMessage`
- `setStreamingMeta`
- `resetConversation`

要求：assistant 流式回复必须使用 placeholder + delta append 方式，不能每个 chunk 新建一条消息。

---

### 3.4 类型定义

#### 新增或修改

- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/services/agentops/types.ts`

#### 至少包含

- `ChatRole`
- `ChatMessage`
- `ChatStreamEvent`
- `ChatStreamRequest`
- `ModelItem`

建议为 `start / delta / final / error` 事件建立明确类型。

---

### 3.5 API 适配层

#### 新增或修改

- `frontend-ai/src/lib/request.ts`
- `frontend-ai/src/services/agentops/chat.ts`
- `frontend-ai/src/services/agentops/models.ts`

#### 职责

- `request.ts`：封装统一请求入口，支持 `VITE_API_BASE_URL`
- `chat.ts`：封装聊天流请求参数
- `models.ts`：请求 `/api/models` 并兼容后端返回结构

---

### 3.6 SSE 适配层

#### 新增

- `frontend-ai/src/adapters/sse.ts`

#### 职责

- 发起流式请求
- 解析 SSE chunk
- 转为前端统一事件
- 推送给上层 hook / store

#### 最低支持事件

- `start`
- `delta`
- `final`
- `error`

可预留：

- `tool_start`
- `tool_result`

---

### 3.7 Hook 层

#### 新增

- `frontend-ai/src/hooks/useChatStream.ts`
- `frontend-ai/src/hooks/useModels.ts`

#### 职责

- `useChatStream.ts`：负责发送消息、创建 assistant placeholder、消费 SSE 事件、更新 `traceId / taskId`
- `useModels.ts`：负责拉取模型列表与默认模型设置

---

### 3.8 环境与开发配置

#### 新增或修改

- `frontend-ai/.env.development`
- `frontend-ai/vite.config.ts`

#### 最低要求

```env
VITE_API_BASE_URL=http://localhost:8000
```

开发联调时可提供 `/api` 代理，但仅作为开发便利，不作为正式架构的一部分。

---

### 3.9 后端最小联调点

#### 新增或修改

- `app/presentation/api/routes/chat.py` 或等价文件
- `app/presentation/api/routes/models.py` 或等价文件

#### 必须具备

- `POST /api/chat/stream`
- `GET /api/models`

#### SSE 最小事件

```json
{ "type": "start", "trace_id": "xxx", "task_id": "yyy" }
{ "type": "delta", "text": "正在分析..." }
{ "type": "final", "message": { "role": "assistant", "content": "结果..." } }
```

---

## 4. 实施顺序

1. 定位现有路由、请求封装、聊天组件与状态管理等价文件
2. 新增 `chat.ts` / `models.ts` / `types.ts`
3. 实现 `chatStore.ts`
4. 实现 `sse.ts`
5. 实现 `useChatStream.ts` 与 `useModels.ts`
6. 改造 `ChatPage.tsx`、`MessageList.tsx`、`ChatInput.tsx`
7. 挂载 `/chat`
8. 联调 `/api/models` 与 `/api/chat/stream`
9. 输出预览路由、启动方式与剩余问题

---

## 5. 验收标准

- 浏览器访问 `/chat` 成功
- 模型列表可见
- 发送消息成功
- 回复为流式追加
- `trace_id` / `task_id` 保存在前端状态中
- 页面无阻断报错

---

## 6. Codex 输出要求

Phase 1 完成后，必须输出：

- 新增文件清单
- 修改文件清单
- 关键改造点
- 预览路由
- 本地启动方式
- 已知问题
