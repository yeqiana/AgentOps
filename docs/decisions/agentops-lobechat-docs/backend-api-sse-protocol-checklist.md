# 三阶段后端 API / SSE 协议清单

## 1. 文档目的

本文档定义三阶段前端接入所需的后端接口与 SSE 事件协议，目标是：

- 让前端实施清单与后端演进保持一致
- 降低前端 Adapter 反复返工
- 为 Codex 提供可落地的 API / 协议目标

---

## 2. 总体原则

### 2.1 协议优先稳定

后端事件结构一旦用于前端渲染，除非必要，不应频繁改动。

### 2.2 事件与文本解耦

SSE 事件中，普通文本增量与运行态事件必须区分。

### 2.3 前后端统一命名

建议统一使用：

- `trace_id`
- `task_id`
- `session_id`
- `workflow_step`
- `tool_start`
- `tool_result`

避免同义字段并存。

---

## 3. Phase 1 API / SSE 清单

### 3.1 接口目标

#### `POST /api/chat/stream`

职责：

- 接收前端消息请求
- 创建本轮运行上下文
- 以 SSE 返回模型增量文本与最小元信息

#### `GET /api/models`

职责：

- 返回可用模型列表
- 返回前端可直接渲染的模型字段

---

### 3.2 `POST /api/chat/stream` 请求结构

```json
{
  "session_id": "optional",
  "messages": [
    { "role": "user", "content": "你好" }
  ],
  "model": "doubao-1.5",
  "stream": true
}
```

字段说明：

- `session_id`：Phase 1 可选
- `messages`：至少支持用户消息数组
- `model`：当前所选模型
- `stream`：固定为 `true`

---

### 3.3 Phase 1 SSE 最小事件

#### 事件 1：start

```json
{ "type": "start", "trace_id": "tr_xxx", "task_id": "tk_xxx" }
```

用途：

- 告知前端本轮 trace 与 task 标识
- 前端保存到状态中

#### 事件 2：delta

```json
{ "type": "delta", "text": "正在分析..." }
```

用途：

- 逐步追加 assistant 文本

#### 事件 3：final

```json
{ "type": "final", "message": { "role": "assistant", "content": "最终结果" } }
```

用途：

- 标记本轮流式输出结束
- 允许前端进行 finalize 处理

#### 事件 4：error

```json
{ "type": "error", "message": "something went wrong" }
```

用途：

- 告知前端本轮失败
- 前端将当前 assistant placeholder 标记为失败态

---

### 3.4 `GET /api/models` 响应建议

```json
{
  "items": [
    { "id": "doubao-1.5", "name": "Doubao 1.5", "provider": "doubao" },
    { "id": "gpt-4.1", "name": "GPT-4.1", "provider": "openai" }
  ]
}
```

要求：

- 至少提供 `id` 与 `name`
- 最好提供 `provider`
- 若后端内部结构更复杂，请在前端 `models.ts` 中做兼容整理

---

## 4. Phase 2 API / SSE 清单

### 4.1 接口目标

新增：

- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions`
- `POST /api/files/upload`

---

### 4.2 `GET /api/sessions` 响应建议

```json
{
  "items": [
    {
      "id": "sess_001",
      "title": "排查前端 SSE 问题",
      "updated_at": "2026-04-15T16:00:00Z"
    }
  ]
}
```

---

### 4.3 `GET /api/sessions/{session_id}` 响应建议

```json
{
  "id": "sess_001",
  "title": "排查前端 SSE 问题",
  "messages": [
    {
      "id": "msg_u_1",
      "role": "user",
      "content": "帮我看下 SSE 协议",
      "created_at": "2026-04-15T16:00:00Z"
    },
    {
      "id": "msg_a_1",
      "role": "assistant",
      "content": "可以，先从事件结构看。",
      "created_at": "2026-04-15T16:00:05Z"
    }
  ]
}
```

---

### 4.4 `POST /api/sessions` 请求与响应建议

请求：

```json
{ "title": "新对话" }
```

响应：

```json
{
  "id": "sess_002",
  "title": "新对话",
  "created_at": "2026-04-15T16:10:00Z"
}
```

---

### 4.5 `POST /api/files/upload` 响应建议

```json
{
  "file_id": "file_123",
  "filename": "demo.png",
  "content_type": "image/png",
  "size": 12345,
  "url": "/files/file_123"
}
```

用途：

- 前端展示附件预览
- 前端在后续聊天请求中引用附件元数据

---

### 4.6 Phase 2 对聊天流的扩展建议

Phase 2 不强制新增复杂事件，但建议允许在 `start` 中透出 `session_id`：

```json
{ "type": "start", "trace_id": "tr_xxx", "task_id": "tk_xxx", "session_id": "sess_001" }
```

便于前端将本轮消息归属到会话。

---

## 5. Phase 3 API / SSE 清单

### 5.1 接口目标

新增或补充：

- `GET /api/traces/{trace_id}`
- `GET /api/tasks/{task_id}`
- 聊天流式输出中的运行态事件

---

### 5.2 Phase 3 SSE 新增事件

#### `tool_start`

```json
{ "type": "tool_start", "name": "search_code" }
```

用途：

- 告知前端某个工具开始执行

#### `tool_result`

```json
{ "type": "tool_result", "name": "search_code", "summary": "命中 12 个文件" }
```

用途：

- 展示工具摘要结果

#### `workflow_step`

```json
{ "type": "workflow_step", "name": "plan_generation", "status": "running" }
```

或：

```json
{ "type": "workflow_step", "name": "plan_generation", "status": "completed" }
```

用途：

- 向前端透出 workflow 运行状态变化

#### `trace_link`

```json
{ "type": "trace_link", "trace_id": "tr_xxx" }
```

用途：

- 显式更新 trace 标识

#### `task_link`

```json
{ "type": "task_link", "task_id": "tk_xxx" }
```

用途：

- 显式更新 task 标识

#### `warning`

```json
{ "type": "warning", "message": "tool timeout, fallback enabled" }
```

用途：

- 前端展示弱错误或回退提示

#### `error`

```json
{ "type": "error", "message": "workflow failed" }
```

用途：

- 前端标记本轮运行失败

---

### 5.3 `GET /api/traces/{trace_id}` 响应建议

```json
{
  "id": "tr_xxx",
  "status": "completed",
  "source": "chat",
  "started_at": "2026-04-15T16:00:00Z",
  "ended_at": "2026-04-15T16:00:10Z"
}
```

---

### 5.4 `GET /api/tasks/{task_id}` 响应建议

```json
{
  "id": "tk_xxx",
  "status": "completed",
  "name": "chat_turn",
  "started_at": "2026-04-15T16:00:00Z",
  "ended_at": "2026-04-15T16:00:10Z"
}
```

---

## 6. SSE 传输格式建议

建议采用标准 SSE：

```text
data: {"type":"start","trace_id":"tr_xxx","task_id":"tk_xxx"}

data: {"type":"delta","text":"正在"}

data: {"type":"delta","text":"分析"}

data: {"type":"final","message":{"role":"assistant","content":"最终答案"}}

```

要求：

- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `Connection: keep-alive`
- 单个 `data:` 块内保证 JSON 可独立解析

---

## 7. 阶段映射总结

### Phase 1 对应

- 前端：聊天页、模型选择、SSE 渲染
- 后端：`/api/chat/stream`、`/api/models`
- SSE：`start / delta / final / error`

### Phase 2 对应

- 前端：会话栏、历史消息、上传附件
- 后端：`/api/sessions*`、`/api/files/upload`
- SSE：建议在 `start` 中携带 `session_id`

### Phase 3 对应

- 前端：Tool / Workflow / Trace / Task 调试视图
- 后端：增强版聊天流与详情查询
- SSE：`tool_start / tool_result / workflow_step / trace_link / task_link / warning / error`

---

## 8. 给 Codex 的后端实施要求

- 先补齐 Phase 1 接口，不要一口气把全部事件都做完
- 事件字段命名与前端类型定义保持一致
- 若后端已有类似接口，优先在原接口上演进，而不是平行再造一套
- 在进入下一阶段前，先保证上一阶段前后端联调通过
