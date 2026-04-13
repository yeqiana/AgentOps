# Web Admin 前端整体骨架优化方案

## 1. 背景

当前 `frontend/trace-console` 已完成 Trace Console 的多页能力，包括请求链路列表、请求链路详情、任务详情、观测面板和登录页。随着页面增加，前端已经开始出现页面标题区、页面提示、状态区、导航规则和静态配置分散在页面或组件内部的问题。

本方案基于 `docs/frontend-spec/` 下已落地的前端规范体系，面向当前 Web Admin 前端做整体骨架优化规划，使页面从分散结构收口为统一后台骨架。

重点参考规范：

- `docs/frontend-spec/03-web-admin/31-layout-navigation.md`
- `docs/frontend-spec/03-web-admin/32-dashboard-spec.md`
- `docs/frontend-spec/03-web-admin/33-table-list-page-spec.md`
- `docs/frontend-spec/03-web-admin/35-detail-page-spec.md`
- `docs/frontend-spec/03-web-admin/36-trace-observability-page-spec.md`
- `docs/frontend-spec/02-engineering/20-frontend-architecture.md`
- `docs/frontend-spec/02-engineering/21-project-structure.md`
- `docs/frontend-spec/02-engineering/22-config-system.md`
- `docs/frontend-spec/02-engineering/23-component-development-spec.md`
- `docs/frontend-spec/02-engineering/24-page-development-spec.md`

## 2. 当前前端项目现状

### 2.1 当前布局结构

当前前端工程已建立：

- `frontend/trace-console/`

当前前端技术栈：

- React
- TypeScript
- Vite
- React Router

当前已有后台骨架：

- `frontend/trace-console/src/layouts/AppLayout.tsx`
- `frontend/trace-console/src/layouts/AuthLayout.tsx`

`AppLayout` 当前结构：

- `Sidebar`
- `Header`
- `PageNavigation`
- `Outlet`
- `Footer`

`AuthLayout` 当前结构：

- 品牌说明区
- 登录表单区
- `Footer`

判断：

- 当前已经不是完全分散结构，已经具备 `AppLayout` 和 `AuthLayout` 的基础。
- 当前缺口不是“从零重建布局”，而是补齐 `PageHeader`、页面 Shell、配置中心与导航规则收口。

### 2.2 已有公共组件

当前已有通用组件：

- `frontend/trace-console/src/components/LinkButton.tsx`
- `frontend/trace-console/src/components/PageStateView.tsx`
- `frontend/trace-console/src/components/StatusBadge.tsx`

当前已有布局组件：

- `frontend/trace-console/src/components/layout/Footer.tsx`
- `frontend/trace-console/src/components/layout/Header.tsx`
- `frontend/trace-console/src/components/layout/PageHintBar.tsx`
- `frontend/trace-console/src/components/layout/PageNavigation.tsx`
- `frontend/trace-console/src/components/layout/Sidebar.tsx`
- `frontend/trace-console/src/components/layout/UserMenu.tsx`

判断：

- `Footer`、`Header`、`PageHintBar`、`PageNavigation`、`Sidebar`、`UserMenu` 均可复用。
- `PageHintBar` 已被列表、详情、观测页使用，应保留并纳入页面 Shell。
- 当前缺少 `PageHeader`，导致页面标题区在页面内重复实现。

### 2.3 已有页面路由

当前路由定义位于：

- `frontend/trace-console/src/app/router.tsx`

当前已存在路由：

- `/login`
- `/`
- `/console`
- `/console/traces`
- `/console/observability`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`

判断：

- `/` 和 `/console` 当前重定向到 `/console/observability`，观测面板已经成为默认控制台入口。
- 路由本身集中在 `router.tsx`，但路由路径、面包屑规则和导航元信息还没有集中配置。

### 2.4 适合复用的部分

适合直接复用：

- `AppLayout`
- `AuthLayout`
- `Footer`
- `Header`
- `PageNavigation`
- `Sidebar`
- `UserMenu`
- `PageHintBar`
- `LinkButton`
- `PageStateView`
- `StatusBadge`
- 当前所有业务 feature panels
- 当前所有 API 封装
- 当前所有 DTO 类型

### 2.5 需要抽离的部分

需要抽离：

- 页面标题区：当前在 `TraceListPage`、`TraceDetailEntryPage`、`TaskDetailPage`、`ObservabilityDashboardPage` 内重复实现。
- 页面 Shell：Dashboard、List、Detail 三类页面结构需要抽为模板。
- Sidebar 导航配置：当前写在 `Sidebar.tsx` 内部。
- Breadcrumb 规则：当前写在 `PageNavigation.tsx` 内部。
- Header 和环境静态信息：当前主要来自 `UI_TEXT`，但缺少 `ui.config.ts` 与 `env.config.ts` 的边界。
- 页面路由路径常量与元信息：当前只在 `router.tsx` 与 `PageNavigation.tsx` 中分散存在。

## 3. 目标骨架结构

目标骨架：

```text
AppLayout
├── Sidebar
├── Header
│   └── UserMenu
├── PageNavigation
├── PageContent
│   ├── PageHeader
│   ├── PageHintBar
│   └── PageShell children
└── Footer

AuthLayout
├── AuthBrandPanel
├── AuthFormPanel
└── Footer
```

目标组件职责：

- `AppLayout`：承载后台全局骨架，不关心具体页面标题和业务数据。
- `AuthLayout`：承载登录入口骨架，本轮不扩展真实登录逻辑。
- `Sidebar`：只负责渲染导航，导航数据从 `navigation.config.ts` 获取。
- `Header`：只负责渲染全局头部，产品、环境、搜索提示从配置或文案表获取。
- `Footer`：保持统一底部。
- `PageNavigation`：负责面包屑，规则从 `route.config.ts` 获取。
- `PageHeader`：统一页面标题、副标题、主操作按钮。
- `PageHintBar`：保留当前可收起提示能力。
- `UserMenu`：保留当前用户菜单结构。

## 4. 建议目录结构

建议在当前 `src` 下增量补齐目录：

```text
frontend/trace-console/src/
├── app/
├── layouts/
│   ├── AppLayout.tsx
│   ├── AuthLayout.tsx
│   ├── DashboardPageShell.tsx
│   ├── ListPageShell.tsx
│   └── DetailPageShell.tsx
├── components/
│   ├── layout/
│   │   ├── Footer.tsx
│   │   ├── Header.tsx
│   │   ├── PageHeader.tsx
│   │   ├── PageHintBar.tsx
│   │   ├── PageNavigation.tsx
│   │   ├── Sidebar.tsx
│   │   └── UserMenu.tsx
│   ├── LinkButton.tsx
│   ├── PageStateView.tsx
│   └── StatusBadge.tsx
├── config/
│   ├── navigation.config.ts
│   ├── ui.config.ts
│   ├── env.config.ts
│   └── route.config.ts
├── pages/
│   ├── auth/
│   ├── observability/
│   ├── tasks/
│   └── traces/
└── features/
```

## 5. 页面模板拆分建议

### 5.1 DashboardPageShell

适用页面：

- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`

职责：

- 承接 Dashboard 类页面的 `PageHeader`。
- 承接 `PageHintBar`。
- 承接指标卡与面板栅格容器。
- 不负责请求数据。
- 不负责业务 panel 内部逻辑。

### 5.2 ListPageShell

适用页面：

- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`

职责：

- 承接列表页 `PageHeader`。
- 承接 `PageHintBar`。
- 提供 filters slot。
- 提供 content slot。
- 提供 pagination slot。
- 不修改 `getConsoleTraces`、筛选和分页业务逻辑。

### 5.3 DetailPageShell

适用页面：

- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`
- `frontend/trace-console/src/pages/tasks/TaskDetailPage.tsx`

职责：

- 承接详情页 `PageHeader`。
- 承接 `PageHintBar`。
- 提供 actions slot。
- 提供 detail grid content slot。
- 不修改 trace viewer 和 task summary 的请求逻辑。

## 6. 配置收口建议

### 6.1 navigation.config.ts

承接内容：

- `Sidebar.tsx` 内部的 `sidebarSections`。

建议包含：

- section title
- item label
- item route
- item badge
- disabled 状态

边界：

- 只做导航结构配置。
- 不接真实权限。
- disabled 项保持现有语义，避免误开未实现页面。

### 6.2 route.config.ts

承接内容：

- `router.tsx` 中的路径常量。
- `PageNavigation.tsx` 中的 breadcrumb 规则。

建议包含：

- route path 常量
- 默认重定向路径
- breadcrumb label 映射
- 动态路由匹配规则

边界：

- 不扩新增业务路由。
- 只收口现有路由和面包屑。

### 6.3 ui.config.ts

承接内容：

- 页面壳层相关静态 UI 配置。
- Header 产品显示配置。
- PageShell 默认配置。

边界：

- `UI_TEXT` 继续作为文案表保留。
- 不在本轮迁移全部文案。

### 6.4 env.config.ts

承接内容：

- 环境标签。
- 版本信息。
- 是否展示环境标签。

边界：

- 首版只做静态配置。
- 不接真实运行时配置中心。

## 7. 实施顺序

1. 先抽骨架

新增 `PageHeader`、`DashboardPageShell`、`ListPageShell`、`DetailPageShell`，只替换重复页面标题区和提示区，不改业务请求逻辑。

2. 再接 Dashboard

让 `/console/observability` 使用 `DashboardPageShell`。该页面是当前默认入口，最适合作为骨架收口第一处验证点。

3. 再接 Trace List

让 `/console/traces` 使用 `ListPageShell`，保留筛选、分页、loading、error、no permission 逻辑。

4. 再接 Trace Detail

让 `/console/traces/:traceId` 使用 `DetailPageShell`，保留 viewer、timeline、console logs、alerts、graph。

5. 同步接 Task Detail

让 `/console/tasks/:taskId` 使用 `DetailPageShell`，避免详情页风格再次分叉。

6. 最后做配置收口

新增 `navigation.config.ts`、`route.config.ts`、`ui.config.ts`、`env.config.ts`，让 Sidebar、PageNavigation、Header 从配置读取。

7. 最后回归验证

检查以下路由：

- `/login`
- `/console/observability`
- `/console/traces`
- `/console/traces/:traceId`
- `/console/tasks/:taskId`

## 8. 影响文件清单

### 8.1 新增文件

- `frontend/trace-console/src/components/layout/PageHeader.tsx`
- `frontend/trace-console/src/layouts/DashboardPageShell.tsx`
- `frontend/trace-console/src/layouts/ListPageShell.tsx`
- `frontend/trace-console/src/layouts/DetailPageShell.tsx`
- `frontend/trace-console/src/config/navigation.config.ts`
- `frontend/trace-console/src/config/ui.config.ts`
- `frontend/trace-console/src/config/env.config.ts`
- `frontend/trace-console/src/config/route.config.ts`

### 8.2 修改文件

- `frontend/trace-console/src/components/layout/Sidebar.tsx`
- `frontend/trace-console/src/components/layout/Header.tsx`
- `frontend/trace-console/src/components/layout/PageNavigation.tsx`
- `frontend/trace-console/src/pages/observability/ObservabilityDashboardPage.tsx`
- `frontend/trace-console/src/pages/traces/TraceListPage.tsx`
- `frontend/trace-console/src/pages/traces/TraceDetailEntryPage.tsx`
- `frontend/trace-console/src/pages/tasks/TaskDetailPage.tsx`
- `frontend/trace-console/src/app/styles.css`
- `frontend/trace-console/src/constants/uiText.ts`

### 8.3 暂不处理文件

- `frontend/trace-console/src/features/trace-console/api/traceConsoleApi.ts`
- `frontend/trace-console/src/features/trace-console/types/traceConsole.ts`
- `frontend/trace-console/src/features/trace-console/components/*`
- `frontend/trace-console/src/lib/http/client.ts`
- `frontend/trace-console/src/pages/auth/LoginPage.tsx`

说明：

- 本轮不改接口契约。
- 本轮不改 DTO。
- 本轮不改业务 panel。
- 本轮不改 HTTP 行为。
- 登录页除非后续做 AuthLayout 深化，否则不改业务逻辑。

## 9. 风险与边界

### 9.1 风险点

- `styles.css` 当前承载大量全局样式，抽 PageShell 时应避免大规模重命名，优先兼容式新增。
- `PageNavigation` 当前使用 pathname hardcode，改配置时必须验证动态路由：
  - `/console/traces/:traceId`
  - `/console/tasks/:taskId`
- `Sidebar` 当前存在 disabled 导航项，配置化后要保留 disabled 语义。
- `PageShell` 不应膨胀为万能组件，只承接页面结构，不承接数据请求。
- 如果一次性迁移过多文案，会增加无关 diff，建议保留 `UI_TEXT` 主文案表。

### 9.2 边界

- 本轮不改接口契约。
- 本轮不改业务逻辑。
- 本轮不扩业务功能。
- 本轮不处理移动端。
- 本轮不引入图表库。
- 本轮不引入全局状态管理。
- 本轮不接真实权限。
- 本轮不接真实登录。
- 本轮不做自动刷新或 SSE。

## 10. 验收标准

- `/console/observability` 页面可正常访问。
- `/console/traces` 页面可正常访问，筛选和分页不受影响。
- `/console/traces/:traceId` 页面可正常访问，viewer 展示不受影响。
- `/console/tasks/:taskId` 页面可正常访问，Task -> Trace 跳转不受影响。
- `/login` 页面可正常访问。
- Sidebar 导航渲染与当前一致。
- Header、Footer、UserMenu 渲染与当前一致。
- PageNavigation 面包屑在列表页、详情页、任务页、观测页均正确。
- 页面标题区统一由 `PageHeader` 承接。
- Dashboard/List/Detail 页面通过对应 Shell 承接结构。
- 未改动后端接口、前端 API 契约和业务数据加载逻辑。
