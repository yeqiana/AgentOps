# 下一步开发与设计计划

## 一、项目当前底座现状总评

当前项目更接近“可迭代后台 + 半成品重构中”，不是概念验证，也还没到“可扩展产品底座”。后端五层结构、API、认证/RBAC、Trace/Task/Alert 聚合查询已经较完整；前端已从单页 Trace Console 发展出 AppLayout/AuthLayout/PageShell、登录守卫、Dashboard/Trace/Task 页面和统一 API client。但前端仍处在阶段 3 早期收口期：权限闭环、状态管理、设计系统、文档基线和规范落地还不稳定。尤其是 `docs/decisions/frontend-stack-final.md` 写了 Ant Design 与 TanStack Query，但 `frontend/trace-console/package.json` 尚未引入，说明方案和实现存在差距。

## 二、已完成能力盘点

### 工程/架构

- 当前已有内容：后端保持 `app/` 五层结构，`presentation / application / domain / workflow / infrastructure` 基本符合 AGENTS 约束；前端在 `frontend/trace-console/` 已形成 React + TypeScript + Vite 工程。
- 已达到程度：后端结构可持续扩展；前端已经从页面集合进入后台 App Shell 阶段。
- 可否支撑继续扩展：可以，但前端还缺工程质量脚本、测试基线和文档冻结。

### 认证/授权

- 当前已有内容：后端 `app/presentation/api/middleware/auth.py` + `app/infrastructure/auth/service.py` 支持 API Key/Bearer 与最小 RBAC；前端 `AuthProvider`、`RequireAuth`、`usePermission` 已接 `/auth/me`。
- 已达到程度：开发凭证登录、用户态、菜单权限、路由权限已经形成最小闭环。
- 可否支撑继续扩展：可作为骨架复用，但还不是正式登录体系，也未做 panel-level 权限。

### 页面骨架

- 当前已有内容：`AppLayout`、`AuthLayout`、`DashboardPageShell`、`ListPageShell`、`DetailPageShell`、`Sidebar`、`Header`、`PageNavigation`、`PageHeader`。
- 已达到程度：已形成清晰的 app shell / layout / page shell。
- 可否支撑继续扩展：可支撑继续扩展，但 `PageHeader` 仍存在固定 kicker“控制台首页”等通用性问题。

### 数据层/API

- 当前已有内容：前端 `traceConsoleApi.ts` 与 `traceConsole.ts` 覆盖 Trace List、Trace Viewer、Task Summary、Operations Overview、Trace Stats、Alert Stats；后端 `TraceConsoleService` 已承接列表、viewer、summary、timeline、graph 聚合逻辑。
- 已达到程度：Trace/Task/Alert MVP 数据链路基本跑通。
- 可否支撑继续扩展：可支撑首版控制台，但 DTO 仍手写，缺少 schema 生成或契约校验。

### UI/设计系统

- 当前已有内容：`tokens.css`、dark mode、density mode、SettingsPanel、分层样式入口 `styles/index.css`。
- 已达到程度：已有 token 与主题骨架，但未形成完整设计系统。
- 可否支撑继续扩展：短期可继续开发，长期需要收敛硬编码色值、圆角、阴影、渐变和组件规范。

### 核心业务模块

- 当前已有内容：`ObservabilityDashboardPage`、`TraceListPage`、`TraceDetailEntryPage`、`TaskDetailPage` 已接真实 API；Alert 已作为统计和详情面板存在。
- 已达到程度：Trace/Task 详情链路已具备，Alert 仍缺独立页面。
- 可否支撑继续扩展：可继续扩展，但不宜继续把所有入口堆在 Observability 页面。

## 三、关键缺口与风险

1. P0：前后端权限不一致。前端路由 `/console/traces` 只要求 `trace.read`，但后端 `/console/traces` 和 viewer 同时要求 `trace.read + alert.read`。如果不处理，会导致用户能进入页面但接口 403。
2. P0：认证仍是开发凭证 + localStorage。它能支撑内测，但不能作为正式后台登录；后续接 SSO、token、cookie 时，如果边界不稳定，会牵连所有 API 请求和路由守卫。
3. P0：设计规范文档基线不稳。工作区状态显示大量 `docs/frontend-spec` 删除，同时新决策文档又引用这些规范；如果不先定稿，会影响 AI 和多人协作输入。
4. P1：前端数据层未形成统一状态管理。当前页面用 `useEffect + useState` 手写 loading/error/retry；页面一多会重复请求、缓存、失效、并发处理逻辑。
5. P1：技术决策与依赖不一致。`docs/decisions/frontend-stack-final.md` 写 Ant Design 与 TanStack Query，但实际未在 `package.json` 落地；后续页面开发会在“继续自研 CSS”还是“引入组件库”上反复摇摆。
6. P1：UI 规范落地差距明显。tokens 存在，但 `page-shell.css` 与 `layout.css` 仍有硬编码渐变、18px/14px 圆角、负字距；与可持续设计系统不一致。
7. P1：缺少前端测试/验收脚本。后端有 unit/integration/e2e，前端只有 build 脚本；后续改布局或权限时容易回归。
8. P1：Alert/Task/Trace 信息架构尚未完全拆清。Observability 同时承载任务、告警、Trace、模块入口；不拆会让 Dashboard 变成万能页。
9. P2：API DTO 由前端手写。短期可用，长期易与 `app/presentation/api/schemas.py` 漂移。
10. P2：Figma/MCP 没有落地边界。现在只有决策说明，没有设计稿命名、组件映射、验收清单；容易让设计稿反向绑架代码结构。

### 规范落地差距

- 后端查询契约文档与代码基本一致。
- 前端 pages 文档部分过期，仍描述 Trace Detail 占位，但代码已实现。
- auth skeleton 文档与代码基本一致。
- style unification 只部分落地。
- frontend stack final 尚未在依赖层落地。

## 四、下一阶段最合理的建设顺序

### 1. 前端底座冻结

- 目标：冻结路由、权限、API client、PageShell、状态组件、token 基线。
- 为什么先做：当前业务页面已经够验证数据链路，继续堆页面会放大权限和样式债。
- 产出物：权限矩阵对齐、统一 403/PageState、API error 策略、PageShell v1、设计 token v1。
- 涉及目录：`frontend/trace-console/src/`、`app/presentation/api/`。
- 风险点：不要一次性重写 UI，也不要引入过多库。

### 2. 核心页面闭环

- 目标：把 Dashboard/Trace List/Trace Detail/Task Detail/Alert Center 做成可演示闭环。
- 为什么先做：Trace/Task/Alert 是阶段 3 的核心业务链路。
- 产出物：独立 Alert 页面、Task 列表入口、Trace-Task-Alert 双向跳转、空/错/无权限一致体验。
- 涉及目录：`frontend/trace-console/src/pages/`、`frontend/trace-console/src/features/trace-console/`。
- 风险点：避免把所有聚合都塞进 Observability。

### 3. 设计系统与协作链路

- 目标：形成 Figma -> MCP -> Codex 可复用流程。
- 为什么后做：要先冻结代码组件边界，设计稿才能映射到真实组件。
- 产出物：Figma 页面模板、组件映射表、token 对照表、MCP 使用边界。
- 涉及目录：`docs/decisions/`、`docs/architecture/plans/`、`docs/ai-prompts/`。
- 风险点：设计稿只指导视觉和结构，不决定领域目录/API 契约。

## 五、未来 2~4 周开发路线图

### Week 1

- 核心目标：补底座。
- 具体任务：对齐 `trace.read / alert.read / task.read` 路由与接口权限；补统一 403；整理 `docs/frontend-spec` 去留；确认 Ant Design/TanStack Query 是否立即引入；清理 PageHeader/PageShell 通用性。
- 预期成果：前端底座决策冻结，权限不再“能进但 403”。
- 前置依赖：确认当前工作区文档删除是否有效。

### Week 2

- 核心目标：核心页面闭环。
- 具体任务：拆出 Alert Center 页面；补 Task List 或从 Dashboard 明确进入 Task Detail；增强 Trace/Task/Alert 跳转；统一 loading/empty/error/no permission。
- 预期成果：Trace -> Task -> Trace、Trace -> Alert 的控制台闭环。
- 前置依赖：Week 1 权限和路由基线完成。

### Week 3

- 核心目标：设计系统 v1。
- 具体任务：收敛 token/radius/shadow/spacing；定义 Panel/Table/Form/State/PageHeader 组件规范；决定 AntD 用于 CRUD 的接入边界；补前端 build/lint/typecheck/test 文档。
- 预期成果：新增页面可按同一套 UI 规范开发。
- 前置依赖：核心页面结构稳定。

### Week 4

- 核心目标：设计协作与质量基线。
- 具体任务：建立 Figma 低保真模板、MCP 读取规则、AI 开发提示模板；补前端 smoke 验收清单；后端 API 契约文档与前端 DTO 对齐。
- 预期成果：多人/AI 协作可持续推进。
- 前置依赖：设计系统 v1 已冻结。

## 六、设计计划

- 哪些页面要先设计：Observability Dashboard、Trace List、Trace Detail、Task Detail、Alert Center、403/Empty/Error 状态页。
- 哪些组件要先抽象：App Shell、PageHeader、PageHintBar、Panel、KPI Card、Table、FilterBar、Pagination、Timeline、Log Panel、Graph 简版、StatusBadge。
- 当前更适合低保真还是高保真：当前更适合低保真到中保真，不建议直接高保真大改视觉；先冻结信息架构和组件层级。
- Figma 在这个阶段应该产出什么：页面流、组件清单、token 表、状态页、关键断点布局、Trace/Task/Alert 跳转关系。
- MCP 在这个阶段应该如何介入：只读取 Figma 结构、层级、间距、组件命名，转成实现任务和验收清单。
- 哪些内容不能让设计稿反向绑架代码结构：不能改五层后端结构，不能决定 API DTO，不能绕过现有 PageShell/feature 目录，不能因为视觉稿引入第二套样式体系。

## 七、建议立即创建/补充的文档

### `frontend-foundation-freeze-v1.md`

- 目的：冻结前端底座边界。
- 建议目录：`docs/decisions/`。
- 应包含章节：技术栈、依赖取舍、路由、权限、数据层、样式体系、验收标准。

### `frontend-permission-contract.md`

- 目的：对齐前后端权限。
- 建议目录：`docs/architecture/plans/`。
- 应包含章节：页面权限、接口权限、403 策略、panel-level 后置计划。

### `trace-console-page-map.md`

- 目的：明确 Dashboard/Trace/Task/Alert 页面关系。
- 建议目录：`docs/architecture/plans/`。
- 应包含章节：路由、入口、数据接口、跳转、状态。

### `design-system-v1.md`

- 目的：沉淀 token 与组件规范。
- 建议目录：`docs/decisions/`。
- 应包含章节：颜色、字号、间距、圆角、Panel/Table/Form/State。

### `figma-mcp-codex-workflow.md`

- 目的：规范设计协作。
- 建议目录：`docs/ai-prompts/frontend/` 或 `docs/decisions/`。
- 应包含章节：输入、MCP 输出、Codex 任务模板、禁止事项。

### `frontend-quality-checklist.md`

- 目的：补协作验收。
- 建议目录：`docs/architecture/plans/`。
- 应包含章节：build、权限、响应式、状态、API、回归路径。

## 八、最终结论

当前下一步最应该做的 3 件事：

1. 先冻结前端底座与权限契约。
2. 再补齐 Trace/Task/Alert 控制台业务闭环。
3. 最后把设计系统和 Figma/MCP 协作流程文档化。

现在不要做：

- 完整微服务化。
- 复杂图谱画布。
- 实时 SSE 大盘。
- SSO/OIDC 全量改造。
- 成本配额和模型路由策略引擎。

可以等底座稳定后再做：

- Ant Design 大规模 CRUD 接入。
- TanStack Query 全量迁移。
- panel-level 权限。
- 自动刷新。
- 多 trace 对比。
- 完整权限治理控制台。

当前优先级是“补底座”，不是继续单纯补业务页面。
