# Codex Phase 2 开工提示词：会话、文件与消息增强

你现在开始执行 **Lobe 风格前端接入 AgentOps 的 Phase 2**。  
前提：Phase 1 已跑通聊天主链路。

## 一、实施依据

必须先读取并遵循以下文档：

- `docs/decisions/lobechat-frontend-integration.md`
- `docs/implementation/lobechat/phase2-implementation-checklist.md`
- `docs/implementation/lobechat/backend-api-sse-protocol-checklist.md`

---

## 二、本阶段目标

必须完成：

- 会话列表
- 新建会话
- 历史消息恢复
- 文件上传
- 消息支持附件
- 基础错误反馈与重试

本阶段明确不做：

- Tool Call UI
- Workflow UI
- Trace / Task 调试抽屉
- 全量知识库 / 插件体系
- 复杂 RBAC 联动

---

## 三、优先处理的文件

- `src/components/chat/SessionSidebar.tsx`
- `src/components/chat/SessionList.tsx`
- `src/components/chat/SessionItem.tsx`
- `src/components/chat/FileUploadButton.tsx`
- `src/components/chat/AttachmentPreview.tsx`
- `src/stores/sessionStore.ts`
- `src/services/agentops/sessions.ts`
- `src/services/agentops/files.ts`
- `src/hooks/useSessions.ts`
- `src/hooks/useFileUpload.ts`
- `src/pages/chat/ChatPage.tsx`
- `src/types/chat.ts`
- `src/stores/chatStore.ts`

若已有等价文件，优先原位改造。

---

## 四、关键实现要求

### 1. 会话能力
- 展示会话列表
- 支持切换当前会话
- 支持新建会话
- 支持恢复历史消息

### 2. 文件上传
- 接入 `/api/files/upload`
- 上传成功后在 UI 中展示附件信息
- 附件应能进入消息上下文或消息元信息

### 3. 消息状态
消息应至少支持：
- `sending`
- `streaming`
- `done`
- `error`

### 4. 页面布局
- 左侧会话栏
- 右侧对话区
- 空态体验合理

---

## 五、后端联调要求

请确认或补齐：
- `GET /api/sessions`
- `GET /api/sessions/:id`
- `POST /api/sessions`
- `POST /api/files/upload`

如接口未具备，请列出最小补齐点。

---

## 六、输出要求

按以下顺序汇报：

1. Phase 1 现状确认
2. Phase 2 等价文件映射
3. 新增文件清单
4. 修改文件清单
5. 关键实现说明
6. 预览位置
7. 启动方式
8. 已知问题 / 风险
