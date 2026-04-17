"""
Trace 中间件。

这是一个 FastAPI 中间件，用于为每个进入的 HTTP 请求创建和管理请求级别的 Trace 记录。

它的功能：
- 在请求处理前启动 trace。
- 将 `trace_id` 和 `request_id` 写入 `request.state`，供后续处理流程使用。
- 在 HTTP 响应头中返回 `X-Trace-Id` 和 `X-Request-Id`。
- 在请求处理完成后记录请求状态、错误码和限流信息。

这样设计的原因：
- Trace 需要对所有请求统一生效，不能依赖单个路由或处理器。
- 通过中间件边界，可以保证请求生命周期、鉴权上下文、错误和限流状态
  都被一致地写入追踪系统。
"""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.trace import TraceService


class TraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, trace_service: TraceService) -> None:
        super().__init__(app)
        self.trace_service = trace_service

    async def dispatch(self, request, call_next: Callable) -> Response:
        trace = self.trace_service.start_trace(
            source_type="http",
            method=request.method.upper(),
            path=request.url.path,
            auth_subject=getattr(request.state, "auth_subject", ""),
            auth_type=getattr(request.state, "auth_type", ""),
            idempotency_key=sanitize_text(request.headers.get("Idempotency-Key", "")),
        )
        trace_id = trace["trace_id"]
        request_id = trace["request_id"]
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        request.state.rate_limited = False

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-Id"] = request_id
        self.trace_service.finish_request(
            trace_id,
            status_code=response.status_code,
            error_code=sanitize_text(getattr(request.state, "error_code", "")),
            rate_limited=bool(getattr(request.state, "rate_limited", False)),
        )
        return response
