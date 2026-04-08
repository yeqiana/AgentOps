"""
Trace middleware.

What this is:
- FastAPI middleware for request-level trace records.

What it does:
- Assigns `trace_id` and `request_id`.
- Persists request trace metadata before and after handler execution.
- Returns the trace ID in response headers.

Why this is done this way:
- Trace persistence must happen consistently for every request, not only in
  selected route handlers.
"""

from __future__ import annotations

import uuid
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
        trace_id = sanitize_text(request.headers.get("X-Trace-Id", "")) or f"trace_{uuid.uuid4().hex}"
        request_id = f"req_{uuid.uuid4().hex}"
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        request.state.rate_limited = False
        self.trace_service.begin_request(
            trace_id=trace_id,
            request_id=request_id,
            method=request.method.upper(),
            path=request.url.path,
            auth_subject=getattr(request.state, "auth_subject", ""),
            auth_type=getattr(request.state, "auth_type", ""),
            idempotency_key=sanitize_text(request.headers.get("Idempotency-Key", "")),
        )

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
