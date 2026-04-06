"""
LLM 兼容转发模块。

这是什么：
- 这是旧的 `app.infrastructure.llm_client` 兼容入口。

做什么：
- 把历史导入路径转发到新的 `app.infrastructure.llm.client`。

为什么这么做：
- 当前项目已经把 LLM 正式分包到 `infrastructure/llm/`。
- 保留这个薄转发层可以避免一次性改动过大，同时给迁移留出过渡期。
"""

from app.infrastructure.llm.client import *  # noqa: F401,F403
