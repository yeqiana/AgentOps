# AgentOps Codex 落地执行文档 v1

## 一、文档定位

本文件用于指导 Codex 在 AgentOps 前端项目中按统一规范落地，实现目标包括：

1. 按已确认的后台系统 UI 规范实施页面与布局。
2. 保留当前已确认方向的登录页、后台首页、Trace 页，不做推翻式改造。
3. 抽离公共布局与公共组件，形成长期可扩展的后台管理系统骨架。
4. 参考用户提供的 Vue 文件中“易读、结构清晰、可维护”的写法风格，转译为适合当前 React / TypeScript 项目的前端代码规范。

---

## 二、已确认的 UI 基线（不得推翻）

### 1. 登录页
保留第一版登录页的大结构，只做增强：

- 保留品牌区 + 表单区的双栏布局
- 优化背景层次，解决大片空白
- 增加底部备案信息
- 不改成营销官网风
- 不加入花哨插画和复杂动态背景

### 2. 后台首页
采用已确认的后台系统结构：

- 左侧 Sidebar
- 顶部 Header
- 页面导航层 PageNavigation
- 页面标题区
- 首页统计卡片
- 最近任务
- 最近 Trace
- 模块入口区
- 底部 Footer 备案栏

### 3. Trace 页面
以当前已确认满意的 Trace 页为标准参考页：

- 保留三栏布局
- 保留轻提示条
- 保留顶部指标区
- 保留左侧步骤列表 / 中间详情 / 右侧调试信息
- 不随意推翻主体结构
- 仅补系统级能力，如用户菜单、页面导航层、底部备案信息、统一 Header / Sidebar / Footer

---

## 三、Codex 执行总原则

### 原则 1：先抽骨架，再改页面
不要先在单页面零散改样式，必须先形成统一后台骨架。

### 原则 2：保留已确认的视觉方向
对登录页、后台首页、Trace 页只做收口与补齐，不做推翻式重做。

### 原则 3：优先系统一致性
优先保证：
- 结构一致
- 页面层级一致
- 用户入口一致
- 底部备案一致
- 提示条一致

### 原则 4：页面不是孤岛
所有页面都必须长在统一骨架里，不允许每个页面单独拼布局。

---

## 四、Codex 落地任务拆分

---

### 任务 A：抽离公共布局

目标：形成统一后台框架

建议目录：

```text
src/
  layouts/
    AppLayout.tsx
    AuthLayout.tsx
  components/layout/
    Sidebar.tsx
    Header.tsx
    Footer.tsx
    PageNavigation.tsx
    PageHeader.tsx
    PageHintBar.tsx
    UserMenu.tsx
```

要求：

1. `AppLayout.tsx`
   - 包含 Sidebar / Header / PageNavigation / Footer
   - 适用于登录后的后台页面

2. `AuthLayout.tsx`
   - 适用于登录页
   - 支持品牌区 + 登录表单区布局

3. `Header.tsx`
   - 包含页面标题、副标题、全局搜索、环境标签、用户菜单

4. `UserMenu.tsx`
   - 点击头像或用户名可展开下拉菜单
   - 菜单项包括：
     - 个人中心
     - 账号设置
     - 系统偏好
     - 切换环境
     - 退出登录

5. `Footer.tsx`
   - 全页面统一底部备案信息
   - 样式弱化但始终存在

6. `PageNavigation.tsx`
   - 放在 Header 下方
   - 以面包屑形式展示当前页面路径

---

### 任务 B：登录页落地

目标：保留当前确认方向，优化背景层次

建议目录：

```text
src/pages/auth/LoginPage.tsx
```

要求：

1. 使用 `AuthLayout`
2. 结构保持双栏：
   - 左侧：品牌介绍
   - 右侧：登录表单
3. 背景加入：
   - 轻渐变光斑
   - 轻网格层次
4. 底部增加备案信息
5. 不做大留白，不做营销官网风

验收标准：

- 视觉聚焦
- 背景不空
- 表单可读性强
- 登录页与后台风格统一

---

### 任务 C：后台首页落地

建议目录：

```text
src/pages/dashboard/DashboardPage.tsx
```

要求：

1. 使用 `AppLayout`
2. 页面结构：
   - PageNavigation
   - PageHeader
   - 指标卡片
   - 最近任务
   - 最近 Trace
   - 功能模块区
3. 顶部右侧必须有用户菜单
4. 底部备案信息统一显示

验收标准：

- 像后台系统，不像单页面 demo
- 模块层级清晰
- 首页有数据感和入口感

---

### 任务 D：Trace 页面落地

建议目录：

```text
src/pages/traces/TraceDetailPage.tsx
```

要求：

1. 使用 `AppLayout`
2. 保留当前已确认的 Trace 主体结构：
   - 顶部标题和按钮区
   - 轻提示条
   - 指标概览区
   - 三栏布局
3. 新增：
   - Header 统一用户菜单
   - PageNavigation 导航层
   - Footer 备案信息
4. 页面提示必须轻量，不允许占大面积
5. 不推翻当前满意的布局节奏

验收标准：

- 页面主体风格保留
- 系统层级更清晰
- 顶部不拥挤
- 三栏布局仍然稳定

---

## 五、统一页面结构规范

所有登录后的后台页面必须遵循以下层级：

```text
AppLayout
  ├── Header
  ├── PageNavigation
  ├── PageContainer
  │   ├── PageHeader
  │   ├── PageHintBar（可选）
  │   └── PageContent
  └── Footer
```

要求：

- 页面不能直接顶在 Header 下
- Header 与 PageHeader 不是一回事
- 面包屑导航层必须独立存在
- Footer 不得缺失

---

## 六、统一 UI 组件规范

建议目录：

```text
src/components/common/
  Card.tsx
  StatusTag.tsx
  MetricCard.tsx
  JsonBlock.tsx
  EmptyState.tsx
  ErrorState.tsx
  LoadingBlock.tsx
```

约束：

1. `Card`
   - 统一边框、圆角、留白
   - 不允许每页自写一套卡片样式

2. `StatusTag`
   - 成功 / 失败 / 运行中 / 重试中 / 未执行
   - 颜色和文案统一

3. `MetricCard`
   - 用于顶部概览卡片
   - 统一标题、数值、副文案结构

4. `JsonBlock`
   - 统一 JSON 代码块风格
   - 用于 Trace 右侧或原始输出区域

---

## 七、参考 Vue 文件后沉淀的前端代码规范（适配 React / TypeScript）

用户上传的 Vue 文件虽然不是当前技术栈，但其中有一些很适合保留的优点：

### 可借鉴的优点

1. 模板结构清楚
   - 顶部搜索区域
   - 主体区域
   - 左右分区
   - 表格区
   - 分页区
   每个块都有明确职责

2. 注释清楚
   - 使用中文注释说明大区块用途
   - 对阅读者友好

3. 数据组织有层次
   - `url`
   - `inputRules`
   - `searchForm`
   - `treeData`
   - 本地状态
   说明作者会按职责分组

4. 方法命名直接
   - `handleSearch`
   - `handleNodeClick`
   - `handleCurrentChange`
   可读性强

5. 初始化步骤清晰
   - `created` 中按顺序完成初始化
   - 先设默认值，再查数据，再刷新页面

---

### 转译为 React / TypeScript 后的规范

#### 1. 组件文件结构要清楚

每个页面组件建议采用这个顺序：

```text
1. import
2. type / interface
3. 常量
4. 组件主体
5. hooks（state / memo / effect）
6. 事件处理函数
7. 请求与数据处理函数
8. render 返回
```

不要把：
- 请求函数
- 事件函数
- useEffect
- 业务常量
全部打散混写。

---

#### 2. 页面内部区域必须有中文区块注释

例如：

```tsx
{/* 页面顶部操作区 */}
{/* 左侧步骤列表 */}
{/* 中间步骤详情 */}
{/* 右侧调试信息 */}
```

要求：
- 注释只写大区块
- 不写废话式注释
- 以帮助快速阅读为目标

---

#### 3. 状态要按职责分组

不允许把所有状态无序平铺。

推荐按以下方式组织：

```tsx
const [filters, setFilters] = useState(...)
const [pageState, setPageState] = useState(...)
const [tableState, setTableState] = useState(...)
const [uiState, setUiState] = useState(...)
```

或者封装为：

```tsx
const [searchForm, setSearchForm] = useState(...)
const [traceSummary, setTraceSummary] = useState(...)
const [stepList, setStepList] = useState(...)
const [selectedStep, setSelectedStep] = useState(...)
```

重点是：
- 名称有语义
- 同类状态放在一起
- 能让人一眼看懂页面状态结构

---

#### 4. 事件函数统一用 handle 前缀

沿用你给的 Vue 文件里这种风格，适合你阅读：

- `handleSearch`
- `handleReset`
- `handleStepClick`
- `handleRetryTask`
- `handleCopyTraceId`
- `handleToggleHint`

要求：
- 直接表达动作
- 不用过度抽象命名

---

#### 5. 请求函数与数据转换函数分开

例如不要在点击事件里直接写一长段请求 + 数据清洗。

推荐：

```tsx
async function fetchTraceDetail() {}
function mapTraceSummary() {}
function mapStepList() {}
function handleRefresh() {}
```

这样你更容易看懂，也便于 Codex 后续改。

---

#### 6. 页面级配置集中放

适合把一些静态配置集中管理，例如：

```tsx
const STATUS_LABEL_MAP = {...}
const TRACE_ACTIONS = [...]
const STEP_TYPE_LABEL_MAP = {...}
```

这和 Vue 文件里把 `url`、`inputRules`、`treeData` 放在一起的思路类似，优点是好找、易改。

---

#### 7. useEffect 中的初始化流程要写清楚

参考 Vue 文件的 `created` 顺序感，在 React 中也要保留“初始化步骤清晰”的风格。

推荐：

```tsx
useEffect(() => {
  initPage()
}, [])

async function initPage() {
  await fetchSummary()
  await fetchStepList()
  setDefaultSelectedStep(...)
}
```

不要把初始化逻辑拆成多个互相打架的 `useEffect`，除非确有必要。

---

#### 8. JSX 不要嵌套过深

如果一个页面 JSX 超过两层复杂嵌套，优先抽组件。

例如 Trace 页可以拆：

- `TraceSummarySection`
- `TraceStepList`
- `TraceStepContent`
- `TraceDebugPanel`

这样既保留页面整体可读性，又避免一个文件里全是大段 JSX。

---

#### 9. 保持“能看懂优先”，不要过度抽象

这是本次规范里非常重要的一条。

不要求为了所谓高级写法做这些事：

- 过度 hook 化
- 过度泛型化
- 过度配置驱动
- 过早抽象成复杂 schema 渲染

对你当前项目来说，更适合：

- 页面清楚
- 区块清楚
- 命名清楚
- 数据流清楚

---

#### 10. TS 类型要写，但要服务可读性

要求：

- API 返回结构写 type/interface
- 组件 props 写 type/interface
- 核心状态类型明确
- 不追求花哨类型技巧

例如：

```ts
interface TraceSummary {
  traceId: string
  taskStatus: string
  totalToken: number
}
```

要的是“看得懂”，不是“炫技”。

---

## 八、命名规范

### 文件命名
使用 PascalCase：

- `TraceDetailPage.tsx`
- `UserMenu.tsx`
- `PageHintBar.tsx`

### 组件命名
与文件名一致，使用 PascalCase。

### 函数命名
使用 camelCase，事件统一 `handleXxx`。

### 状态命名
优先语义化：

- `searchForm`
- `selectedStep`
- `traceSummary`
- `isHintCollapsed`

---

## 九、禁止事项

### UI 方面
- 不允许每页单独写一套布局
- 不允许缺少用户菜单
- 不允许缺少底部备案
- 不允许提示条占大面积
- 不允许推翻当前已满意的 Trace 主体布局

### 代码方面
- 不允许一个页面把所有逻辑揉成一个大函数
- 不允许大量无注释的大段 JSX
- 不允许状态命名模糊，如 `data1`, `obj`, `temp`
- 不允许为了抽象而抽象
- 不允许写出你自己后面看不懂的“高技巧代码”

---

## 十、Codex 执行顺序（必须按顺序）

### 第 1 步：抽公共骨架
- Sidebar
- Header
- Footer
- UserMenu
- PageNavigation
- PageHintBar

### 第 2 步：接登录页
- 保留原方向
- 优化背景
- 加备案信息

### 第 3 步：接后台首页
- 接入统一布局
- 接用户菜单
- 接页面导航层
- 接底部备案

### 第 4 步：接 Trace 页面
- 保留当前主体结构
- 补统一系统能力

### 第 5 步：做代码收口
- 统一注释
- 统一函数命名
- 统一状态组织
- 统一类型声明

---

## 十一、给 Codex 的执行提示词

```text
请按《AgentOps Codex 落地执行文档 v1》对当前前端项目进行落地。

本次任务目标：
1. 落地统一后台系统骨架：
   - Sidebar
   - Header
   - Footer
   - UserMenu
   - PageNavigation
   - PageHintBar
2. 保留当前已确认的登录页、后台首页、Trace 页方向，不做推翻式改造。
3. 为所有页面统一增加底部备案信息。
4. Header 右上角必须支持用户下拉菜单，包括：
   - 个人中心
   - 账号设置
   - 系统偏好
   - 切换环境
   - 退出登录
5. Trace 页面保留现有三栏主体结构，只补系统级能力。
6. 参考提供的 Vue 文件风格，将前端代码规范调整为：
   - 结构清晰
   - 中文区块注释清楚
   - 状态按职责分组
   - 事件函数使用 handle 前缀
   - 初始化流程明确
   - 可读性优先，不做过度抽象

执行要求：
- 先分析当前代码结构与可复用区域
- 先输出改造方案与文件影响范围
- 再开始修改代码
- 最后输出修改清单、目录结构、验收方式

注意：
- 不改接口契约
- 不改业务逻辑
- 不做大规模视觉推翻
- 不要写后续难以阅读的“炫技代码”
```

---

## 十二、最终目标

这份规范最终不是为了“看起来更高级”，而是为了做到：

- 你自己后面能看懂
- Codex 后续能持续接着改
- 页面和代码都符合系统化、规范化、可维护的方向

一句话总结：

> AgentOps 前端要做到：界面像系统，代码也像系统。
