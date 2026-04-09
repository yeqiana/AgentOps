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

from app.config import get_api_keys, get_auth_admin_subjects, get_bearer_tokens, is_auth_enabled, is_rbac_enabled
from app.domain.errors import AuthenticationError, AuthorizationError, ValidationError
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.persistence.repositories import (
    SQLiteAuthPermissionRepository,
    SQLiteAuthRolePermissionRepository,
    SQLiteAuthRoleRepository,
    SQLiteAuthSubjectRoleRepository,
)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    auth_type: str


@dataclass(frozen=True)
class AuthorizationProfile:
    subject: str
    auth_type: str
    roles: list[str]
    permissions: list[str]


class AuthService:
    def __init__(self) -> None:
        self.enabled = is_auth_enabled()
        self.rbac_enabled = is_rbac_enabled()
        self.api_keys = set(get_api_keys())
        self.bearer_tokens = set(get_bearer_tokens())
        self.admin_subjects = set(get_auth_admin_subjects())
        self.role_repository = SQLiteAuthRoleRepository()
        self.permission_repository = SQLiteAuthPermissionRepository()
        self.role_permission_repository = SQLiteAuthRolePermissionRepository()
        self.subject_role_repository = SQLiteAuthSubjectRoleRepository()

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

    def get_authorization_profile(self, subject: str, auth_type: str) -> AuthorizationProfile:
        normalized_subject = sanitize_text(subject)
        normalized_auth_type = sanitize_text(auth_type)
        if not self.rbac_enabled:
            return AuthorizationProfile(
                subject=normalized_subject,
                auth_type=normalized_auth_type,
                roles=["rbac_disabled"],
                permissions=["*"],
            )

        role_records = self.subject_role_repository.list_by_subject(normalized_subject)
        role_keys = [item["role_key"] for item in role_records]
        if normalized_subject in self.admin_subjects and "admin" not in role_keys:
            role_keys.append("admin")
        permission_records = self.role_permission_repository.list_by_role_keys(role_keys)
        permissions = sorted({item["permission_key"] for item in permission_records})
        return AuthorizationProfile(
            subject=normalized_subject,
            auth_type=normalized_auth_type,
            roles=sorted(role_keys),
            permissions=permissions,
        )

    def authorize(self, *, subject: str, auth_type: str, permission_key: str) -> AuthorizationProfile:
        profile = self.get_authorization_profile(subject, auth_type)
        if "*" in profile.permissions or permission_key in profile.permissions:
            return profile
        raise AuthorizationError(
            "当前主体没有访问该资源的权限。",
            details={"required_permission": permission_key, "auth_subject": profile.subject},
        )

    def list_roles(self) -> list[dict[str, object]]:
        return self.role_repository.list_roles()

    def list_permissions(self) -> list[dict[str, object]]:
        return self.permission_repository.list_permissions()

    def get_subject_assignments(self, *, auth_subject: str) -> list[dict[str, object]]:
        normalized_subject = sanitize_text(auth_subject)
        if not normalized_subject:
            raise ValidationError("auth_subject 不能为空。")
        return self.subject_role_repository.list_by_subject(normalized_subject)

    def assign_subject_roles(self, *, auth_subject: str, role_keys: list[str], updated_by: str) -> list[dict[str, object]]:
        normalized_subject = sanitize_text(auth_subject)
        if not normalized_subject:
            raise ValidationError("auth_subject 不能为空。")
        known_roles = {item["role_key"] for item in self.role_repository.list_roles()}
        normalized_role_keys = [sanitize_text(item) for item in role_keys if sanitize_text(item)]
        unknown_roles = sorted(set(normalized_role_keys) - known_roles)
        if unknown_roles:
            raise ValidationError(
                "存在未注册的角色，无法完成授权。",
                details={"unknown_roles": ",".join(unknown_roles)},
            )
        return self.subject_role_repository.replace_subject_roles(
            auth_subject=normalized_subject,
            role_keys=normalized_role_keys,
            updated_by=sanitize_text(updated_by) or "api-auth",
        )
