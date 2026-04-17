# Codex Phase 3 开工提示词：融合 AgentOps 独有能力

你现在开始执行 **Lobe 风格前端接入 AgentOps 的 Phase 3**。  
前提：Phase 1 和 Phase 2 已完成主链路、会话与文件能力。

## 一、实施依据

必须先读取并遵循以下文档：

- `docs/decisions/lobechat-frontend-integration.md`
- `docs/implementation/lobechat/phase3-implementation-checklist.md`
- `docs/implementation/lobechat/backend-api-sse-protocol-checklist.md`

---

## 二、本阶段目标

必须完成：

- Tool Call 展示
- Tool Result 展示
- Workflow Step 展示
- Trace / Task 元信息展示
- Trace / Task 跳转入口
- 调试抽屉或侧板
- 运行过程可观测化

---

## 三、优先处理的文件

- `src/components/chat/ToolCallCard.tsx`
- `src/components/chat/ToolResultCard.tsx`
- `src/components/chat/WorkflowStepList.tsx`
- `src/components/chat/WorkflowStepItem.tsx`
- `src/components/chat/TraceMetaBar.tsx`
- `src/components/chat/DebugDrawer.tsx`
- `src/stores/chatRuntimeStore.ts`
- `src/hooks/useRuntimeEvents.ts`
- `src/services/agentops/traces.ts`
- `src/services/agentops/tasks.ts`
- `src/adapters/sse.ts`
- `src/hooks/useChatStream.ts`
- `src/types/chat.ts`
- `src/components/chat/MessageItem.tsx`

如已有等价文件，优先原位改造。

---

## 四、关键实现要求

### 1. 运行事件可视化
至少支持展示：
- `tool_start`
- `tool_result`
- `workflow_step`
- `trace_link`
- `task_link`
- `warning`
- `error`

### 2. UI 目标
- 用户能看到工具调用过程
- 用户能看到 workflow 状态变化
- 用户能从聊天页跳到 Trace / Task 详情
- 运行过程不再是黑盒

### 3. 事件与文本分层
- 消息正文仍是 assistant 内容
- 运行态事件放入独立结构或独立 store
- 不要把所有事件粗暴拼进消息文本

---

## 五、后端联调要求

请确认聊天 SSE 已支持：
- `tool_start`
- `tool_result`
- `workflow_step`
- `trace_link`
- `task_link`
- `warning`
- `error`

如后端未具备，请列出最小补齐点，不要擅自扩张到更大产品范围。

---

## 六、输出要求

按以下顺序汇报：

1. Phase 1 / 2 现状确认
2. Phase 3 等价文件映射
3. 新增文件清单
4. 修改文件清单
5. 关键实现说明
6. 预览位置
7. 启动方式
8. 已知问题 / 风险
