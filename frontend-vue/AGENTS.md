# AGENTS.md

## 作用范围

- 本文件只约束 `frontend-vue/` 子工程。
- 上级 `../AGENTS.md` 和仓库根规则仍然有效；如果与本文件冲突，以本文件中更贴近 `frontend-vue/` 的规则优先。

## 项目定位

- `frontend-vue/` 是 AgentOps 的 Vue 前端子应用。
- 当前目标是承载 Figma 驱动的 ChatGPT 风格页面还原与后续前端接入。
- 当前页面不是完整业务聊天系统，而是“聊天首页 / 欢迎页 / 会话侧边栏 / 输入栏”的可运行前端界面。
- 默认路由入口是 `/chatgpt-redesign`，根路径 `/` 会重定向到该页面。

## 技术栈

- Vue 3
- Vite
- TypeScript
- Vue Router
- Element Plus
- Element Plus Icons
- vue-i18n

## 目录结构

```text
frontend-vue/
|-- src/
|   |-- components/      # 可复用 UI 组件
|   |-- i18n/            # 多语言配置与文案
|   |-- pages/           # 页面级组件
|   |-- router/          # Vue Router 路由配置
|   |-- App.vue
|   |-- main.ts
|   |-- styles.css       # 当前全局样式入口
|   `-- vite-env.d.ts
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
`-- vite.config.ts
```

## 运行命令

```powershell
npm install
npm run dev
npm run build
npm run preview
```

- `npm run dev` 启动本地开发服务。
- `npm run build` 会先执行 `vue-tsc --noEmit` 类型检查，再执行 Vite 构建。
- 构建产物在 `dist/`，不要提交。

## 路由规则

- 路由集中维护在 `src/router/index.ts`。
- 当前路由：
  - `/` -> 重定向到 `/chatgpt-redesign`
  - `/chatgpt-redesign` -> `src/pages/ChatRedesignPage.vue`
- 新增页面时，优先放在 `src/pages/`，再在 `src/router/index.ts` 注册。
- 不要在组件内部硬编码跳转路径；如果后续路由变多，应集中定义路径常量。

## 组件职责

- `ChatRedesignPage.vue`
  - 页面级组装组件。
  - 管理当前 tab、当前会话、搜索词、输入框草稿等页面状态。
  - 负责把用户操作串起来，例如搜索、选择会话、点击示例、点击新建聊天。

- `ChatComposer.vue`
  - 底部输入栏组件。
  - 负责输入框、本地草稿同步、发送事件、新建聊天事件。
  - 不直接调用后端 API，只通过事件把动作交给页面或上层业务处理。

- `ConversationList.vue`
  - 会话列表组件。
  - 接收会话数据、当前选中项，并通过 `update:modelValue` 通知父组件切换选中会话。

- `SidebarTabs.vue`
  - 左侧“聊天 / 收藏”tab 组件。
  - 只负责 tab 的展示和选中值更新，不负责真实数据切换。

- `IconButton.vue`
  - 通用图标按钮组件。
  - 负责统一 size、disabled、selected、aria-label 和基础交互态。

- `ChatLogo.vue`
  - ChatGPT 风格 logo 展示组件。
  - 当前 logo 是 CSS 近似实现，不依赖 Figma 临时图片资源。

- `WelcomePanel.vue`
  - 中央欢迎区组件。
  - 展示示例、能力、限制。
  - 用户点击示例后，向外抛出 `selectPrompt`。

## 数据与状态规则

- 页面状态优先放在页面级组件，例如 `ChatRedesignPage.vue`。
- 可复用组件尽量保持“受控组件”风格：
  - 输入来自 props。
  - 状态变化通过 emit 通知父组件。
  - 不在通用组件里直接写业务逻辑。
- 当前 mock 数据允许保留在页面内；当接入真实接口时，应迁移到 service / API 层。
- 不要在多个组件里重复维护同一份状态。

## i18n 规则

- i18n 入口在 `src/i18n/index.ts`。
- 文案定义在 `src/i18n/messages.ts`。
- 默认语言是 `zh-CN`。
- fallback 语言是 `en`。
- 新增用户可见文案时，必须写入 `messages.ts`，不要直接硬编码在模板里。
- aria-label、placeholder、按钮文字、分组标题、列表标题都属于用户可见或辅助技术可见文案，也要走 i18n。
- 临时调试文案可以短期硬编码，但提交前应移入 i18n。

## 样式规则

- 当前全局样式入口是 `src/styles.css`。
- 视觉风格基于 Figma ChatGPT redesign：
  - 白色主背景
  - 浅灰侧栏
  - 绿色选中态
  - 小圆角为主
  - 轻量阴影
  - 简洁层级
- 优先复用已有 CSS 变量：
  - `--page-bg`
  - `--sidebar-bg`
  - `--soft-bg`
  - `--soft-control`
  - `--text`
  - `--muted`
  - `--line`
  - `--green`
  - `--green-soft`
  - `--purple-tag`
- 新增组件样式应使用清晰的组件前缀，例如 `.chat-composer__field`。
- 不要随意引入新的全局颜色体系；新增颜色前先确认是否可复用现有变量。
- hover、active、focus-visible、disabled、selected 等基础交互态要补齐。
- 移动端适配已有断点：
  - `900px`
  - `640px`

## Element Plus 使用规则

- 可以使用 Element Plus 和 `@element-plus/icons-vue`。
- 当前主 UI 多数是自定义 CSS 还原 Figma，而不是直接套 Element Plus 组件。
- 引入 Element Plus 组件时，要确认不会破坏当前视觉层级。
- 当前 `ElementPlus` 是全量注册，构建会有 chunk size 警告；后续如优化包体，可改为按需引入。

## 注释规则

- 页面级复杂交互可以保留“人话注释”，尤其是“用户点击 -> 发生什么”的说明。
- 方法上方应说明用户动作、状态变化和后续接入点。
- 不要给显而易见的 Vue 语法写注释。
- 注释应解释业务意图，不解释语法。

## 可访问性规则

- 图标按钮必须提供 `aria-label`。
- 搜索框、输入框必须有 label 或 aria-label。
- 可点击项使用 `button` 优先，不要用不可访问的 `div` 模拟按钮。
- focus-visible 状态不能删除。

## 禁止提交的内容

- `node_modules/`
- `dist/`
- `*.log`
- `*.tsbuildinfo`
- `vite.config.js`
- `vite.config.d.ts`
- `.idea/`
- 本地临时文件

## 修改边界

- 修改 `frontend-vue/` 时，不要顺手改 `fronted-ai/`、`frontend/trace-console/`、`lobe-chat/` 等其他前端目录。
- 不要改后端业务逻辑，除非用户明确要求接入接口。
- 不要因为视觉调整重构 unrelated 组件。
- 新增依赖前先确认是否确实需要；能用现有 Vue / Element Plus / CSS 完成的，不额外引包。

## 验证要求

- 修改源码后至少执行：

```powershell
npm run build
```

- 如果只改注释或文档，可以不跑构建，但最终回复里要说明未运行。
- 如果改了样式或交互，建议启动 dev server 人工检查页面：

```powershell
npm run dev
```

## 当前已知事项

- 当前页面仍以 mock 数据为主，尚未接入真实聊天 API。
- `sendMessage` 当前只是前端占位逻辑，后续接后端时可从这里扩展。
- `SidebarTabs` 当前只切换 tab 选中态，还未切换真实聊天/收藏数据源。
- Vite 构建可能提示 chunk size 超过 500KB，主要来自 Element Plus 全量引入；这不是功能错误。
