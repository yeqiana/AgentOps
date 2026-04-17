# Codex Phase 1 开工提示词：最小可运行聊天闭环

你现在开始执行 **Lobe 风格前端接入 AgentOps 的 Phase 1**。  
本阶段目标只有一个：**把聊天主链路跑通。**

## 一、实施依据

必须先读取并遵循以下文档：

- `docs/decisions/lobechat-frontend-integration.md`
- `docs/implementation/lobechat/phase1-implementation-checklist.md`
- `docs/implementation/lobechat/backend-api-sse-protocol-checklist.md`

---

## 二、本阶段目标

必须完成：

- 提供 `/chat` 可访问页面
- 加载 `/api/models`
- 发送消息到 `/api/chat/stream`
- 通过 SSE 流式展示 assistant 回复
- 保存并基础展示 `trace_id` / `task_id`

本阶段明确不做：

- 会话列表
- 历史消息恢复
- 文件上传
- Tool Call UI
- Workflow UI
- Trace / Task 跳转
- 全站接入
- 完整鉴权

---

## 三、优先处理的文件

请结合当前仓库现状，定位并新增或修改这些文件的等价实现：

- `src/pages/chat/ChatPage.tsx`
- `src/components/chat/ChatLayout.tsx`
- `src/components/chat/MessageList.tsx`
- `src/components/chat/MessageItem.tsx`
- `src/components/chat/ChatInput.tsx`
- `src/components/chat/ModelSelector.tsx`
- `src/stores/chatStore.ts`
- `src/types/chat.ts`
- `src/services/agentops/types.ts`
- `src/services/agentops/chat.ts`
- `src/services/agentops/models.ts`
- `src/adapters/sse.ts`
- `src/hooks/useChatStream.ts`
- `src/hooks/useModels.ts`
- 路由入口文件
- `.env.development`
- `vite.config.ts`

注意：
- 如果仓库中已有等价文件，优先原位改造
- 不要机械创建重复目录

---

## 四、关键实现要求

### 1. assistant 流式更新方式
必须使用：
- 先插入 assistant placeholder
- 后续 delta 逐步 append 到同一条消息

### 2. SSE 适配
至少支持事件：
- `start`
- `delta`
- `final`
- `error`

### 3. 模型列表
- 从 `/api/models` 获取
- 设置默认模型
- 当前模型影响下一次发送

### 4. 页面结构
`/chat` 页面至少包含：
- 顶部栏
- 模型选择
- 消息列表
- 输入区
- 基础 trace/task 信息显示区

### 5. 工程约束
- 保持与现有前端风格尽量一致
- 把请求逻辑收口到 `services/agentops/*`
- 不把复杂逻辑塞满页面组件

---

## 五、后端联调要求

请检查后端是否已具备：
- `POST /api/chat/stream`
- `GET /api/models`

若未具备：
- 列出缺口
- 给出最小补齐点
- 不要擅自扩展到 Phase 2 / 3

---

## 六、输出要求

请严格按以下顺序汇报：

1. 现有结构分析
2. 等价文件映射
3. 新增文件清单
4. 修改文件清单
5. 关键实现说明
6. 预览路由
7. 启动方式
8. 已知问题 / 风险

不要先讲大而空的方案，直接进入仓库分析并开始实现 Phase 1。
