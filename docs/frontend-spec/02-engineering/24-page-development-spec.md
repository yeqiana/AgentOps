# 页面开发规范

## 一、页面文件顺序
1. import
2. type / interface
3. 常量
4. 组件主体
5. hooks
6. 事件处理函数
7. 请求与数据处理函数
8. render 返回

## 二、页面区块注释
页面内部必须对大区块增加中文注释。

## 三、状态组织
状态按职责分组：

- filters
- pageState
- tableState
- uiState

## 四、初始化流程
初始化逻辑应集中，流程明确，避免多个 useEffect 相互打架。
