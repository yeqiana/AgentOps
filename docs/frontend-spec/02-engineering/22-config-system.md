# 配置中心规范

## 一、目标
统一页面级静态规则，避免散落式定义。

## 二、推荐目录
`src/config/`

## 三、推荐配置拆分
- app.config.ts
- ui.config.ts
- env.config.ts
- table.config.ts
- route.config.ts
- permission.config.ts

## 四、原则
- 页面只读取配置
- 不在页面内部重复定义
- 配置命名要直白
