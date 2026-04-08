"""
Authentication service.

What this is:
- The stage-2 minimal auth service.

What it does:
- Validates API Key or Bearer Token credentials against configured static lists.
- Produces a normalized authenticated principal for downstream middleware and
  handlers.

Why this is done this way:
- Stage 2 needs a single auth boundary now, even if stage 3 later replaces it
  with database-backed users, SSO, or IAM integration.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_api_keys, get_bearer_tokens, is_auth_enabled
from app.domain.errors import AuthenticationError
from app.infrastructure.llm.client import sanitize_text


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    auth_type: str


class AuthService:
    def __init__(self) -> None:
        self.enabled = is_auth_enabled()
        self.api_keys = set(get_api_keys())
        self.bearer_tokens = set(get_bearer_tokens())

    def authenticate(self, api_key: str | None, authorization: str | None) -> AuthenticatedPrincipal:
        if not self.enabled:
            return AuthenticatedPrincipal(subject="anonymous", auth_type="disabled")

        normalized_api_key = sanitize_text(api_key or "")
        if normalized_api_key and normalized_api_key in self.api_keys:
            return AuthenticatedPrincipal(subject=f"apikey:{normalized_api_key[:8]}", auth_type="api_key")

        normalized_authorization = sanitize_text(authorization or "")
        if normalized_authorization.lower().startswith("bearer "):
            token = sanitize_text(normalized_authorization[7:])
            if token and token in self.bearer_tokens:
                return AuthenticatedPrincipal(subject=f"bearer:{token[:8]}", auth_type="bearer")

        raise AuthenticationError("认证失败，请提供有效的 API Key 或 Bearer Token。")
