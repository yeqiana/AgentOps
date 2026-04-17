# Phase 2 实施清单：会话、文件与消息能力补齐

## 1. 阶段目标

本阶段目标是把“能聊”升级为“可用的聊天产品”。

必须完成：

- 会话列表
- 历史消息恢复
- 新建会话
- 文件上传
- 消息支持附件与状态
- 错误反馈与重试能力

本阶段不做：

- 完整知识库
- 插件市场
- 深度 RBAC 联动
- 完整 Trace / Task 调试面板

---

## 2. 文件级改造清单

### 2.1 会话栏与会话列表

#### 新增或修改

- `frontend-ai/src/components/chat/SessionSidebar.tsx`
- `frontend-ai/src/components/chat/SessionList.tsx`
- `frontend-ai/src/components/chat/SessionItem.tsx`

#### 职责

- 渲染左侧会话栏
- 提供会话列表与当前会话高亮
- 提供新建会话入口
- 支持点击切换会话

---

### 2.2 会话状态管理与 API

#### 新增或修改

- `frontend-ai/src/stores/sessionStore.ts`
- `frontend-ai/src/services/agentops/sessions.ts`
- `frontend-ai/src/hooks/useSessions.ts`

#### 最低状态

- `sessions`
- `currentSessionId`
- `isLoadingSessions`

#### 最低能力

- 拉取会话列表
- 拉取会话详情
- 新建会话
- 切换会话
- 恢复会话历史消息

---

### 2.3 文件上传能力

#### 新增或修改

- `frontend-ai/src/components/chat/FileUploadButton.tsx`
- `frontend-ai/src/components/chat/AttachmentPreview.tsx`
- `frontend-ai/src/services/agentops/files.ts`
- `frontend-ai/src/hooks/useFileUpload.ts`

#### 职责

- 选择本地文件
- 上传至 `/api/files/upload`
- 在输入区或消息区展示附件预览
- 将上传结果映射到消息上下文或附件元数据中

---

### 2.4 消息模型增强

#### 修改

- `frontend-ai/src/types/chat.ts`
- `frontend-ai/src/stores/chatStore.ts`
- `frontend-ai/src/components/chat/MessageItem.tsx`

#### 新增能力

- 消息附件字段
- 消息状态字段：`sending` / `streaming` / `done` / `error`
- 失败消息反馈
- 消息重试入口

---

### 2.5 页面布局升级

#### 修改

- `frontend-ai/src/pages/chat/ChatPage.tsx`
- `frontend-ai/src/components/chat/ChatLayout.tsx`

#### 升级内容

- 左侧会话栏 + 右侧聊天区双栏布局
- 顶部展示当前会话标题
- 支持空态页或首次进入引导态

---

### 2.6 后端接口补齐

#### 新增或修改

- `app/presentation/api/routes/sessions.py`
- `app/presentation/api/routes/files.py`

#### 必须具备

- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions`
- `POST /api/files/upload`

---

## 3. 实施顺序

1. 新增 `sessions.ts`、`sessionStore.ts`、`useSessions.ts`
2. 完成左侧会话栏组件
3. 改造 `ChatPage.tsx` 为双栏布局
4. 新增 `files.ts`、`useFileUpload.ts`
5. 接入上传按钮与附件预览
6. 扩展消息类型与消息状态
7. 联调会话接口与文件上传接口
8. 补充失败反馈与重试体验

---

## 4. 验收标准

- 会话栏可见
- 历史会话可切换
- 历史消息能恢复
- 可新建会话
- 文件可上传并显示
- 消息错误状态与重试可用

---

## 5. Codex 输出要求

Phase 2 完成后，必须输出：

- 新增文件清单
- 修改文件清单
- 会话与文件能力接入说明
- 预览入口
- 本地启动方式
- 已知问题
