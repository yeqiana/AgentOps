# Phase 2 实施清单：会话、文件与消息增强

## 一、阶段目标

本阶段目标：

> 从“能聊”升级到“像一个真正可用的聊天产品”。

必须完成：
- 会话列表
- 新建会话
- 历史消息恢复
- 文件上传
- 消息支持附件
- 错误反馈与重试

本阶段不做：
- Tool Call UI
- Workflow UI
- Trace / Task 调试抽屉
- 全量知识库 / 插件体系
- 复杂 RBAC 联动

---

## 二、文件级改造清单

### A. 会话侧栏
新增或修改：
- `frontend-ai/src/components/chat/SessionSidebar.tsx`
- `frontend-ai/src/components/chat/SessionList.tsx`
- `frontend-ai/src/components/chat/SessionItem.tsx`

职责：
- 展示会话列表
- 高亮当前会话
- 提供新建会话按钮
- 支持切换当前会话

---

### B. 会话状态管理
新增或修改：
- `frontend-ai/src/stores/sessionStore.ts`
- `frontend-ai/src/services/agentops/sessions.ts`
- `frontend-ai/src/hooks/useSessions.ts`

最低能力：
- 获取会话列表
- 获取会话详情
- 新建会话
- 切换会话
- 恢复历史消息

---

### C. 文件上传
新增或修改：
- `frontend-ai/src/components/chat/FileUploadButton.tsx`
- `frontend-ai/src/components/chat/AttachmentPreview.tsx`
- `frontend-ai/src/services/agentops/files.ts`
- `frontend-ai/src/hooks/useFileUpload.ts`

职责：
- 选择文件
- 上传到 `/api/files/upload`
- 展示上传结果
- 将附件纳入消息上下文或元信息

---

### D. 消息模型增强
修改：
- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/stores/chatStore.ts`
- `frontend-ai/src/components/chat/MessageItem.tsx`

新增能力：
- 附件字段
- 消息状态：
  - `sending`
  - `streaming`
  - `done`
  - `error`
- 失败重试入口

---

### E. 页面布局升级
修改：
- `frontend-ai/src/pages/chat/ChatPage.tsx`
- `frontend-ai/src/components/chat/ChatLayout.tsx`

升级内容：
- 左侧会话栏 + 右侧对话区双栏布局
- 顶部显示当前会话标题
- 支持空态页

---

### F. 后端接口补齐
新增或修改：
- `app/presentation/api/routes/sessions.py`
- `app/presentation/api/routes/files.py`

必须具备：
- `GET /api/sessions`
- `GET /api/sessions/:id`
- `POST /api/sessions`
- `POST /api/files/upload`

---

## 三、验收标准

- 能看到会话列表
- 能新建会话
- 能切换到历史会话
- 历史消息可恢复
- 文件可上传并可展示附件
- 消息失败有反馈，可重试
