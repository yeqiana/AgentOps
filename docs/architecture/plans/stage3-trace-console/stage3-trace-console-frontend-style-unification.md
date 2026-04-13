# Stage3：Trace Console 前端样式统一实施文档

---

## 一、背景

在 stage3-trace-console-frontend-pages 中，已完成：

- 前端骨架统一（AppLayout / PageContainer / PageShell）
- 页面结构收口（Dashboard / List / Detail）
- 导航与路由配置化（navigation.config.ts / route.config.ts）
- 页面标题区统一（PageHeader / PageHintBar）

当前前端已经从“页面集合”升级为“结构统一的后台系统”。

但仍存在：

- 样式体系不统一
- 页面视觉风格存在差异
- 历史样式与新骨架样式混用
- styles.css 中存在临时兼容规则

因此本阶段目标是：

> 对所有控制台页面进行**样式统一收口**，建立稳定的后台视觉体系。

---

## 二、当前现状

### 1. 样式来源

当前样式主要来自：

- `src/app/styles.css`
- 页面内部 class（如 page-card / trace-detail-hero 等）
- 新骨架补充样式（page-shell / page-header-actions）

---

### 2. 已统一部分

- 页面骨架结构已统一
- 页面标题区已通过 PageHeader 抽象
- 页面提示区已统一为 PageHintBar

---

### 3. 仍存在问题

#### 页面层

- 页面间距不一致（padding / section spacing）
- 页面内容宽度不统一

#### Header 区

- 标题字号不统一
- 副标题样式不统一
- 操作区布局不一致

#### Card / Panel

- 圆角、边框、阴影不统一
- 内边距不统一
- 卡片 header 风格不一致

#### 表格 / 列表

- 查询区与操作区位置不完全统一
- 表格行高、间距不一致
- 分页区样式不统一

#### 状态

- Loading / Empty / Error 表现不统一
- 不同页面实现方式不同

#### 样式代码

- styles.css 中存在旧样式与新样式混用
- 缺乏统一命名与分层

---

## 三、本线程目标

本线程目标：

> 建立统一后台样式体系，使所有页面在视觉与间距上保持一致。

具体目标：

1. 统一页面容器样式（PageContainer）
2. 统一 PageHeader 与 PageHintBar 样式
3. 统一 Card / Panel 样式
4. 统一 Table / List 区域样式
5. 统一状态展示（Loading / Empty / Error）
6. 收口 styles.css 中的通用样式
7. 为后续 Token 化（design token）打基础

---

## 四、范围边界

### 本轮包含

- 样式统一（layout / page / card / table / state）
- styles.css 收口
- 页面接入统一样式

---

### 本轮不包含

- ❌ 不修改业务逻辑
- ❌ 不修改 API
- ❌ 不新增功能
- ❌ 不重写页面结构
- ❌ 不做移动端适配
- ❌ 不引入 UI 框架
- ❌ 不做完整 design token 体系

---

## 五、样式统一对象拆分

本轮样式统一分为 6 类：

---

### 1. Page（页面层）

统一：

- 页面左右 padding
- 页面顶部间距
- 区块垂直间距
- 内容最大宽度

作用组件：

- PageContainer

---

### 2. Header 区

统一：

- 页面标题字号
- 副标题样式
- 操作区对齐
- Header 与内容间距

作用组件：

- PageHeader

---

### 3. Hint 区

统一：

- 提示条背景
- 边框 / 弱化样式
- 与 Header / Content 间距

作用组件：

- PageHintBar

---

### 4. Card / Panel

统一：

- 背景色
- 圆角
- 边框
- 阴影
- 内边距
- Header / Body / Footer 结构

适用：

- Dashboard 卡片
- Detail 面板
- Section 容器

---

### 5. Table / List

统一：

- 查询区位置（左上）
- 操作区位置（右上）
- 表格 header 样式
- 行高
- hover 效果
- 分页区

适用页面：

- TraceListPage
- 后续所有列表页

---

### 6. State（状态）

统一：

- Loading
- Empty
- Error
- No Permission

要求：

- 统一结构
- 统一文案风格
- 统一视觉样式

---

## 六、样式落位策略

### 1. styles.css 分层

建议拆分逻辑层级（不强制拆文件）：

```text
# Layout 层
.page-container
.page-shell

# Header 层
.page-header
.page-header-title
.page-header-subtitle
.page-header-actions

# Hint 层
.page-hint

# Card 层
.card
.card-header
.card-body
.card-footer

# Table 层
.table-container
.table-toolbar
.table-pagination

# State 层
.state-loading
.state-empty
.state-error
