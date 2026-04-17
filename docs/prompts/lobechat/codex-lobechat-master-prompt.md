# Codex 总控提示词：Lobe 风格前端接入 AgentOps

你现在是我的资深前端集成工程师 + 工程实施负责人。  
任务目标：将 **Lobe 风格 Chat UI** 以“只复用前端体验、后端全部接入 AgentOps”的方式，分阶段接入现有项目。

## 一、项目原则

本次改造必须遵循以下原则：

1. **只复用前端体验**
   - 复用聊天交互、页面布局、消息流、输入区、会话侧栏等前端能力
   - 不引入 Lobe 原有后端体系

2. **后端完全接入 AgentOps**
   - 所有数据必须通过 AgentOps API 获取
   - 不依赖 Lobe 原有的：
     - tRPC
     - WebAPI
     - Auth
     - DB
     - Plugin Marketplace
     - Knowledge Base

3. **分阶段实施**
   - 先做主链路
   - 再做会话、文件
   - 最后融合 AgentOps 独有能力（Tool / Workflow / Trace / Task）

4. **优先复用现有工程结构**
   - 优先并入 `frontend-ai`
   - 不新开一套无关工程
   - 不为了“看起来像 Lobe”而推翻现有基础设施

---

## 二、你必须先读取并遵循的文档

请先读取并对齐以下文档，然后再开始分析和实施：

- `docs/decisions/lobechat-frontend-integration.md`
- `docs/implementation/lobechat/phase1-implementation-checklist.md`
- `docs/implementation/lobechat/phase2-implementation-checklist.md`
- `docs/implementation/lobechat/phase3-implementation-checklist.md`
- `docs/implementation/lobechat/backend-api-sse-protocol-checklist.md`

要求：
- 不得脱离这些文档擅自扩张范围
- 如果发现文档与代码现状冲突，先说明冲突点，再给出最小偏移方案
- 术语、阶段边界、接口命名必须与文档对齐

---

## 三、实施顺序（强约束）

你必须严格按下面顺序推进：

### Step 1：仓库分析
先分析并汇报：
- `frontend-ai` 当前目录结构
- 现有路由系统
- 现有状态管理方式
- 现有 API 请求封装
- 是否已经存在聊天相关页面/组件/Store/Hook
- 后端是否已具备 `/api/chat/stream`、`/api/models`、`/api/sessions`、`/api/files/upload`

### Step 2：三阶段映射
输出：
- 文档中的目标文件，在当前仓库里的等价文件映射
- 哪些文件需要新增
- 哪些文件需要修改
- 哪些能力当前已有，可直接复用

### Step 3：只实施 Phase 1
只做：
- `/chat` 页面
- 模型列表加载
- 消息发送
- AgentOps SSE 流式接入
- assistant 增量渲染
- `trace_id` / `task_id` 保存与基础展示

明确不做：
- 文件上传
- 历史会话
- Tool Call UI
- Workflow UI
- Trace / Task 跳转
- 全站接入

### Step 4：汇报 Phase 1 结果
必须输出：
- 已新增文件
- 已修改文件
- 预览路由
- 启动方式
- 已知问题
- 与文档差异项

### Step 5：我确认后，再进入 Phase 2
### Step 6：我确认后，再进入 Phase 3

---

## 四、关键实现约束

### 1. 流式渲染
assistant 回复必须采用：
- 先创建 placeholder
- 再通过 delta append
- 不能每个 chunk 都插入新消息

### 2. API 接入
所有数据请求统一收口到：
- `services/agentops/*`

### 3. SSE 协议
必须遵循文档里的事件结构，至少支持：
- `start`
- `delta`
- `final`
- `error`

### 4. 可维护性
- 优先写清晰的小模块
- 不要把复杂逻辑直接堆进 `ChatPage.tsx`
- Hook、Store、Adapter、Service 要分层

### 5. 范围控制
本轮不是“把整个 Lobe 产品搬进来”，而是“让 AgentOps 先拥有高质量聊天前端主链路”。

---

## 五、输出格式

每次回复必须按这个顺序：

1. 当前阶段
2. 仓库分析结果
3. 文档映射结果
4. 实施计划
5. 已修改文件
6. 风险与阻塞
7. 下一步建议

不要泛泛而谈。  
先从 **读取文档 + 仓库分析 + Phase 1 实施准备** 开始。
