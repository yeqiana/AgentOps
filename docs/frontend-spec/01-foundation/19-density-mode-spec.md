# 19-Density Mode Specification（密度模式规范）

---

## 一、目标

定义 AgentOps 前端的“密度控制体系（Density Mode）”，用于：

- 控制页面信息密度
- 支撑后台高信息承载
- 实现 UI 全局紧凑 / 舒适切换
- 为 AI 提供可控视觉参数系统

---

## 二、设计原则

### 1. 密度必须全局一致

❌ 禁止页面单独调整密度  
✅ 所有密度通过 Token 控制

---

### 2. 密度优先级高于样式

当冲突时：

> 密度 > 美观

---

### 3. 密度必须可切换

系统至少支持：

- compact（默认）
- comfortable（舒适）

---

## 三、Density Mode 定义

---

### 3.1 Compact（默认）

特点：

- 高信息密度
- 紧凑布局
- 控制台默认模式

适用于：

- 后台系统
- 数据密集页面

---

### 3.2 Comfortable（舒适）

特点：

- 间距更大
- 可读性更高
- 密度较低

适用于：

- 新用户
- 展示型页面

---

## 四、影响范围

Density Mode 必须影响：

- 页面 padding
- 卡片 padding
- 表格行高
- 区块间距
- 字号

---

## 五、实现方式

通过 root 控制：

```html
<html data-density="compact">
<html data-density="comfortable">
## 九、UI 控制

系统必须提供用户可操作入口，用于切换 density：

- Header 中提供设置入口
- 支持 localStorage 持久化
- 页面刷新后保持状态
