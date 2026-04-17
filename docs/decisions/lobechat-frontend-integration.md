# LobeChat 前端接入 AgentOps 实施方案

## 一、背景与目标

当前 AgentOps 已具备核心能力：

- 模型路由（多 Provider）
- Workflow 编排
- Tool 调用
- Trace / Task / Alert 体系
- CLI / API 双入口
- 媒体处理能力

但缺少一个成熟的 Chat Web UI。

本方案采用：

> 只复用 Lobe 风格前端聊天体验，后端全部接入 AgentOps。

---

## 二、核心决策

### 采用
- 只复用聊天 UI、消息流、输入区、会话侧栏等前端体验
- 所有数据请求统一改接 AgentOps API
- 按三阶段推进：主链路 → 会话/文件 → AgentOps 能力融合

### 不采用
- 不接入 Lobe 原有后端体系
- 不依赖 tRPC / WebAPI / Auth / DB / Plugin / Knowledge Base
- 不做 Lobe 后端兼容层
- 不通过“只改 proxy”作为最终架构方案

---

## 三、总体架构

```text
frontend-ai (Lobe 风格 UI)
        ↓
services/agentops/* + adapters/sse.ts
        ↓
AgentOps Backend
        ↓
Model / Workflow / Tools / Trace / Task
```

---

## 四、阶段定义

### Phase 1：最小可运行聊天闭环
目标：
- `/chat` 页面可访问
- 能发送消息到 AgentOps
- 能通过 SSE 流式显示 assistant 回复
- 能加载模型列表
- 能拿到 `trace_id` / `task_id`

### Phase 2：会话、文件与消息增强
目标：
- 会话列表
- 新建会话
- 历史消息恢复
- 文件上传
- 附件消息展示
- 错误与重试能力

### Phase 3：融合 AgentOps 独有能力
目标：
- Tool Call / Tool Result 展示
- Workflow Step 展示
- Trace / Task 元信息与跳转
- 调试抽屉或侧板
- 让运行过程可观测化

---

## 五、目录建议

```text
docs/
├─ decisions/
│  └─ lobechat-frontend-integration.md
├─ implementation/
│  └─ lobechat/
│     ├─ phase1-implementation-checklist.md
│     ├─ phase2-implementation-checklist.md
│     ├─ phase3-implementation-checklist.md
│     └─ backend-api-sse-protocol-checklist.md
└─ prompts/
   └─ lobechat/
```

---

## 六、总体验收

### Phase 1 验收
- 聊天页面可访问
- 可选择模型
- 可流式收到回复
- `trace_id` / `task_id` 可获取

### Phase 2 验收
- 可查看会话列表
- 可切换/新建会话
- 可恢复历史消息
- 可上传文件并展示附件

### Phase 3 验收
- 可查看工具调用过程
- 可查看 workflow step
- 可查看并跳转 trace/task
- 运行过程可观测
