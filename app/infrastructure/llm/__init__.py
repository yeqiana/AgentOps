"""
LLM 基础设施包。

这是什么：
- 这是基础设施层下的大模型接入子包。

做什么：
- 统一承载模型客户端、Provider 适配和多模态模型接入相关能力。

为什么这么做：
- 把 LLM 相关实现正式收口到子包后，后续新增 Provider 或适配器时不会继续堆在 `infrastructure` 根目录。
"""

from app.infrastructure.llm.client import (
    LLMCallError,
    call_llm,
    get_llm_client,
    get_llm_settings,
    sanitize_text,
)

__all__ = [
    "LLMCallError",
    "call_llm",
    "get_llm_client",
    "get_llm_settings",
    "sanitize_text",
]
