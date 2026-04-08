"""
Auth middleware.

What this is:
- FastAPI middleware adapter for the stage-2 auth service.

What it does:
- Validates incoming API credentials.
- Stores the authenticated principal on `request.state`.
- Skips auth for health and documentation endpoints.

Why this is done this way:
- Authentication must execute before route handlers so every endpoint can rely
  on a normalized request principal.
"""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.domain.errors import AgentError, AuthenticationError
from app.infrastructure.auth import AuthService
from app.presentation.api.schemas import ErrorResponse


EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: AuthService) -> None:
        super().__init__(app)
        self.auth_service = auth_service

    async def dispatch(self, request, call_next: Callable) -> Response:
        if request.url.path in EXEMPT_PATHS:
            request.state.auth_subject = "anonymous"
            request.state.auth_type = "exempt"
            return await call_next(request)

        try:
            principal = self.auth_service.authenticate(
                request.headers.get("X-API-Key"),
                request.headers.get("Authorization"),
            )
            request.state.auth_subject = principal.subject
            request.state.auth_type = principal.auth_type
            return await call_next(request)
        except AuthenticationError as error:
            payload = ErrorResponse(**error.to_dict())
            return JSONResponse(status_code=401, content=payload.model_dump())
        except AgentError as error:
            payload = ErrorResponse(**error.to_dict())
            return JSONResponse(status_code=403, content=payload.model_dump())
