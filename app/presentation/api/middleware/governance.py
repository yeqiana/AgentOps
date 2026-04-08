"""
Governance middleware.

What this is:
- FastAPI middleware for rate limiting and idempotency.

What it does:
- Applies a simple in-memory rate limit per principal.
- Replays cached POST responses when the same idempotency key is reused.

Why this is done this way:
- Stage 2 needs baseline governance controls before the project grows into
  multi-user and multi-agent traffic patterns.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import (
    get_idempotency_ttl_seconds,
    get_rate_limit_requests,
    get_rate_limit_window_seconds,
    is_idempotency_enabled,
    is_rate_limit_enabled,
)
from app.domain.errors import RateLimitError
from app.presentation.api.schemas import ErrorResponse


@dataclass
class CachedResponse:
    status_code: int
    body: bytes
    media_type: str | None
    expires_at: float


class RateLimiter:
    def __init__(self) -> None:
        self.enabled = is_rate_limit_enabled()
        self.limit = get_rate_limit_requests()
        self.window_seconds = get_rate_limit_window_seconds()
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def check(self, identity: str, path: str) -> None:
        if not self.enabled:
            return
        bucket_key = f"{identity}:{path}"
        timestamps = self._windows[bucket_key]
        now = time.time()
        threshold = now - self.window_seconds
        while timestamps and timestamps[0] < threshold:
            timestamps.popleft()
        if len(timestamps) >= self.limit:
            raise RateLimitError(
                "请求过于频繁，请稍后再试。",
                details={"identity": identity, "path": path, "limit": str(self.limit)},
            )
        timestamps.append(now)


class IdempotencyStore:
    def __init__(self) -> None:
        self.enabled = is_idempotency_enabled()
        self.ttl_seconds = get_idempotency_ttl_seconds()
        self._responses: dict[str, CachedResponse] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def make_cache_key(self, identity: str, method: str, path: str, idempotency_key: str) -> str:
        return f"{identity}:{method}:{path}:{idempotency_key}"

    def get_lock(self, cache_key: str) -> asyncio.Lock:
        if cache_key not in self._locks:
            self._locks[cache_key] = asyncio.Lock()
        return self._locks[cache_key]

    def get(self, cache_key: str) -> CachedResponse | None:
        cached = self._responses.get(cache_key)
        if not cached:
            return None
        if cached.expires_at < time.time():
            self._responses.pop(cache_key, None)
            self._locks.pop(cache_key, None)
            return None
        return cached

    def put(self, cache_key: str, response: CachedResponse) -> None:
        self._responses[cache_key] = response


class GovernanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: RateLimiter, idempotency_store: IdempotencyStore) -> None:
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.idempotency_store = idempotency_store

    async def dispatch(self, request, call_next: Callable) -> Response:
        identity = getattr(request.state, "auth_subject", "anonymous")
        path = request.url.path

        try:
            self.rate_limiter.check(identity, path)
        except RateLimitError as error:
            request.state.rate_limited = True
            request.state.error_code = error.code
            payload = ErrorResponse(**error.to_dict())
            return JSONResponse(status_code=429, content=payload.model_dump())

        request.state.rate_limited = False
        request.state.idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not self.idempotency_store.enabled or request.method.upper() != "POST" or not request.state.idempotency_key:
            return await call_next(request)

        cache_key = self.idempotency_store.make_cache_key(
            identity,
            request.method.upper(),
            path,
            request.state.idempotency_key,
        )
        lock = self.idempotency_store.get_lock(cache_key)
        async with lock:
            cached = self.idempotency_store.get(cache_key)
            if cached:
                replay = Response(content=cached.body, status_code=cached.status_code, media_type=cached.media_type)
                replay.headers["X-Idempotent-Replay"] = "true"
                return replay

            response = await call_next(request)
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            rebuilt = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            if 200 <= rebuilt.status_code < 300:
                self.idempotency_store.put(
                    cache_key,
                    CachedResponse(
                        status_code=rebuilt.status_code,
                        body=body,
                        media_type=rebuilt.media_type,
                        expires_at=time.time() + self.idempotency_store.ttl_seconds,
                    ),
                )
            rebuilt.headers["X-Idempotent-Replay"] = "false"
            return rebuilt
