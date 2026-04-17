# Phase 1 实施清单：最小可运行聊天闭环

## 一、阶段目标

本阶段只解决一件事：

> 让聊天页能打开、能发送消息、能流式收到回复。

必须完成：
- `/chat` 页面可访问
- 请求 AgentOps `/api/chat/stream`
- SSE 流式展示 assistant 回复
- 加载 `/api/models`
- 保存 `trace_id` / `task_id`

本阶段不做：
- 历史会话持久化
- 文件上传
- Tool Call UI
- Workflow UI
- Trace / Task 跳转
- 全站接入

---

## 二、文件级改造清单

### A. 页面与路由
新增或修改：
- `frontend-ai/src/pages/chat/ChatPage.tsx`
- `frontend-ai/src/app/router/index.tsx` 或等价路由入口
- `frontend-ai/src/routes/index.tsx` 或等价文件

职责：
- 提供 `/chat` 页面入口
- 页面包含：
  - 顶部栏
  - 模型选择
  - 消息列表
  - 输入区
  - 基础 trace/task 信息

---

### B. 聊天基础组件
新增或修改：
- `frontend-ai/src/components/chat/ChatLayout.tsx`
- `frontend-ai/src/components/chat/MessageList.tsx`
- `frontend-ai/src/components/chat/MessageItem.tsx`
- `frontend-ai/src/components/chat/ChatInput.tsx`
- `frontend-ai/src/components/chat/ModelSelector.tsx`

职责：
- `ChatLayout.tsx`：页面布局、消息区滚动、输入区固定
- `MessageList.tsx`：渲染消息数组、自动滚动到底部
- `MessageItem.tsx`：渲染 `user` / `assistant` 消息
- `ChatInput.tsx`：输入、发送、禁用状态、回车提交
- `ModelSelector.tsx`：展示模型列表、切换当前模型

---

### C. 状态管理
新增或修改：
- `frontend-ai/src/stores/chatStore.ts`

最低状态字段：
- `messages`
- `currentModel`
- `isStreaming`
- `traceId`
- `taskId`

最低方法：
- `setModel`
- `addUserMessage`
- `createAssistantPlaceholder`
- `appendAssistantDelta`
- `finalizeAssistantMessage`
- `setStreamingMeta`
- `resetConversation`

要求：
- assistant 回复必须用 placeholder + delta append 方式渲染

---

### D. 类型定义
新增或修改：
- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/services/agentops/types.ts`

至少包含：
- `ChatRole`
- `ChatMessage`
- `ChatStreamEvent`
- `ChatStreamRequest`
- `ModelItem`

---

### E. AgentOps API 适配层
新增或修改：
- `frontend-ai/src/lib/request.ts`
- `frontend-ai/src/services/agentops/chat.ts`
- `frontend-ai/src/services/agentops/models.ts`

职责：
- `request.ts`：统一 GET/POST 请求、环境变量读取
- `chat.ts`：封装流式聊天请求
- `models.ts`：封装模型列表接口

---

### F. SSE 适配
新增：
- `frontend-ai/src/adapters/sse.ts`

职责：
- 发起流式请求
- 解析 SSE chunk
- 转换为前端统一事件
- 推送给 hook / store

至少支持：
- `start`
- `delta`
- `final`
- `error`

---

### G. Hook 层
新增：
- `frontend-ai/src/hooks/useChatStream.ts`
- `frontend-ai/src/hooks/useModels.ts`

职责：
- `useChatStream.ts`：发送消息、接流、更新 store
- `useModels.ts`：拉模型列表、设置默认模型

---

### H. 环境与开发配置
新增或修改：
- `frontend-ai/.env.development`
- `frontend-ai/vite.config.ts`

至少提供：
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

### I. 后端最小联调接口
新增或修改：
- `app/presentation/api/routes/chat.py` 或等价文件
- `app/presentation/api/routes/models.py` 或等价文件

必须具备：
- `POST /api/chat/stream`
- `GET /api/models`

---

## 三、验收标准

- 浏览器访问 `/chat` 成功
- 模型列表可加载
- 输入消息后请求成功
- assistant 内容流式追加
- `trace_id` / `task_id` 被保存
- 页面无阻断性报错
