"""
领域错误模型。
这是什么：
- 这是项目统一的错误类型定义模块。
做什么：
- 定义模型错误、工具错误、解析错误、持久化错误等基础错误类型。
- 为 API、CLI、日志和后续任务系统提供统一错误对象。
为什么这么做：
- 如果每一层都直接抛原始异常，后面很难稳定排障。
- 统一错误模型后，日志、接口返回和数据库记录才能说同一种错误语言。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentError(Exception):
    """
    Agent 基础错误对象。
    这是什么：
    - 所有领域级错误的共同父类。
    做什么：
    - 保存错误类别、错误码、用户可读消息、执行链路标识和补充细节。
    为什么这么做：
    - 统一的错误对象更适合跨层传递，不需要上层关心底层库的异常细节。
    """

    category: str
    code: str
    message: str
    trace_id: str | None = None
    details: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def with_trace_id(self, trace_id: str | None) -> "AgentError":
        """
        绑定 trace_id。
        这是什么：
        - 给错误对象补执行链路标识的辅助方法。
        做什么：
        - 在不丢失原有错误信息的前提下，补上当前请求的 trace_id。
        为什么这么做：
        - 错误通常在底层创建，但 trace_id 往往在更上层才拿得到。
        """
        self.trace_id = trace_id
        return self

    def to_dict(self) -> dict[str, object]:
        """
        转成字典。
        这是什么：
        - 给 API 和日志层使用的序列化方法。
        做什么：
        - 输出稳定的错误结构。
        为什么这么做：
        - 接口返回和持久化记录都更适合处理普通字典。
        """
        return {
            "category": self.category,
            "code": self.code,
            "message": self.message,
            "trace_id": self.trace_id,
            "details": self.details,
        }


class ValidationError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("validation", "validation_error", message, trace_id, details or {})


class ParsingError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("parsing", "parsing_error", message, trace_id, details or {})


class ModelError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("model", "model_error", message, trace_id, details or {})


class ToolError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("tool", "tool_error", message, trace_id, details or {})


class PersistenceError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("persistence", "persistence_error", message, trace_id, details or {})


class TraceConsistencyError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("persistence", "trace_consistency_error", message, trace_id, details or {})


class AuthenticationError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("auth", "authentication_error", message, trace_id, details or {})


class AuthorizationError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("auth", "authorization_error", message, trace_id, details or {})


class RateLimitError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("rate_limit", "rate_limit_error", message, trace_id, details or {})


class ConflictError(AgentError):
    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__("conflict", "conflict_error", message, trace_id, details or {})
