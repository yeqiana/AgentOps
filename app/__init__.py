"""
应用主包。

这是什么：
- 这是整个 Agent 底座项目的顶层 Python 包。

做什么：
- 作为各层代码的命名空间根目录。
- 把项目按 `presentation / application / domain / infrastructure / workflow` 分层组织起来。

为什么这么做：
- Python 项目没有唯一标准三层架构，但工程化项目通常会按“接口层、业务层、领域层、基础设施层”拆分。
- 这种结构比把所有逻辑平铺在根目录更容易维护，也更适合后续继续扩展不同 Agent 应用。
"""

