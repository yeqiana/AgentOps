# 三阶段后端 API / SSE 协议清单

本文件用于对齐三阶段前端改造与后端接口、流式协议。

---

## 一、总体原则

- 后端唯一数据源为 AgentOps
- 前端通过 `services/agentops/*` 访问后端
- 流式响应统一采用 SSE
- 事件结构稳定，允许扩展，不允许随意变更字段语义

---

## 二、Phase 1：最小聊天闭环

### 1. 必需 API

#### `POST /api/chat/stream`
请求示例：
```json
{
  "session_id": null,
  "messages": [
    { "role": "user", "content": "你好" }
  ],
  "model": "doubao-1.5",
  "stream": true
}
```

响应类型：
- `Content-Type: text/event-stream`

#### `GET /api/models`
响应示例：
```json
{
  "items": [
    { "id": "doubao-1.5", "name": "Doubao 1.5", "provider": "doubao" }
  ]
}
```

### 2. Phase 1 SSE 事件
至少支持：

#### start
```json
{ "type": "start", "trace_id": "trace_xxx", "task_id": "task_xxx" }
```

#### delta
```json
{ "type": "delta", "text": "正在分析..." }
```

#### final
```json
{ "type": "final", "message": { "role": "assistant", "content": "结果内容" } }
```

#### error
```json
{ "type": "error", "message": "请求失败" }
```

---

## 三、Phase 2：会话与文件

### 1. 必需 API

#### `GET /api/sessions`
响应示例：
```json
{
  "items": [
    { "id": "s1", "title": "新会话", "updated_at": "2026-04-15T10:00:00Z" }
  ]
}
```

#### `GET /api/sessions/:id`
响应示例：
```json
{
  "id": "s1",
  "title": "新会话",
  "messages": [
    { "id": "m1", "role": "user", "content": "你好" },
    { "id": "m2", "role": "assistant", "content": "你好，我在。" }
  ]
}
```

#### `POST /api/sessions`
请求示例：
```json
{ "title": "新会话" }
```

#### `POST /api/files/upload`
响应示例：
```json
{
  "file_id": "file_xxx",
  "name": "demo.pdf",
  "content_type": "application/pdf",
  "size": 102400
}
```

### 2. Phase 2 数据补充要求
消息结构建议支持：
```json
{
  "id": "m1",
  "role": "user",
  "content": "请分析这个文件",
  "attachments": [
    {
      "file_id": "file_xxx",
      "name": "demo.pdf",
      "content_type": "application/pdf"
    }
  ],
  "status": "done"
}
```

---

## 四、Phase 3：运行态可观测能力

### 1. SSE 事件扩展

#### tool_start
```json
{ "type": "tool_start", "name": "search_code" }
```

#### tool_result
```json
{ "type": "tool_result", "name": "search_code", "summary": "命中 12 个文件" }
```

#### workflow_step
```json
{ "type": "workflow_step", "name": "plan_generation", "status": "running" }
```

或：
```json
{ "type": "workflow_step", "name": "plan_generation", "status": "completed" }
```

#### trace_link
```json
{ "type": "trace_link", "trace_id": "trace_xxx" }
```

#### task_link
```json
{ "type": "task_link", "task_id": "task_xxx" }
```

#### warning
```json
{ "type": "warning", "message": "部分工具执行降级" }
```

#### error
```json
{ "type": "error", "message": "工具执行失败" }
```

---

## 五、推荐后端落点

建议重点检查或新增这些文件：

- `app/presentation/api/routes/chat.py`
- `app/presentation/api/routes/models.py`
- `app/presentation/api/routes/sessions.py`
- `app/presentation/api/routes/files.py`
- `app/application/services/task_service.py`
- `app/infrastructure/trace/service.py`

---

## 六、联调要求

### Phase 1 联调要求
- `/api/chat/stream` 可稳定返回 SSE
- `/api/models` 可返回模型列表
- 浏览器跨域或代理配置可用

### Phase 2 联调要求
- `/api/sessions` 系列接口可用
- `/api/files/upload` 可用
- 消息附件字段稳定

### Phase 3 联调要求
- SSE 事件类型稳定
- Tool / Workflow / Trace / Task 事件可消费
- 前端能基于事件构建可观测 UI
