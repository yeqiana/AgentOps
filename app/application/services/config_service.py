"""
Runtime configuration service.

What this is:
- An application-layer service for runtime policy overrides.

What it does:
- Reads database-backed configuration overrides.
- Merges them with environment-based defaults.
- Exposes stable effective workflow and security configuration snapshots.

Why this is done this way:
- Stage-2 configuration governance should stop depending only on process
  environment variables.
- A dedicated service keeps parsing and fallback rules out of API handlers,
  workflow nodes, and tool registries.
"""

from __future__ import annotations

from typing import Any

from app.config import (
    get_allowed_tools,
    is_recovery_llm_degrade_to_mock_enabled,
    is_recovery_tool_soft_fail_enabled,
    get_upload_allowed_kinds,
    get_upload_max_bytes,
    get_workflow_arbitration_role_instruction,
    get_workflow_arbitration_role_name,
    get_workflow_critic_role_instruction,
    get_workflow_critic_role_name,
    get_workflow_challenge_role_instruction,
    get_workflow_challenge_role_name,
    get_workflow_deliberation_keywords,
    get_workflow_support_role_instruction,
    get_workflow_support_role_name,
    is_auth_enabled,
    is_idempotency_enabled,
    is_rate_limit_enabled,
    is_workflow_deliberation_enabled,
)
from app.domain.models import RuntimeConfigRecord
from app.infrastructure.persistence.repositories import SQLiteRuntimeConfigRepository


class RuntimeConfigService:
    """
    What this is:
    - The orchestration-facing runtime configuration center.

    What it does:
    - Loads persisted overrides from `sys_runtime_config`.
    - Provides typed effective config values for workflow and security domains.

    Why this is done this way:
    - Runtime configuration needs one place that knows override precedence and
      value parsing; otherwise different layers would drift.
    """

    def __init__(self, repository: SQLiteRuntimeConfigRepository | None = None) -> None:
        self.repository = repository or SQLiteRuntimeConfigRepository()

    def list_configs(self, *, scope: str | None = None) -> list[RuntimeConfigRecord]:
        return self.repository.list_configs(scope=scope)

    def upsert_config(
        self,
        *,
        scope: str,
        key: str,
        value: str,
        value_type: str,
        description: str,
        updated_by: str,
    ) -> RuntimeConfigRecord:
        return self.repository.upsert_config(
            scope=scope,
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            updated_by=updated_by,
        )

    def get_effective_workflow_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("workflow")
        return {
            "deliberation_enabled": self._as_bool(
                overrides.get("deliberation_enabled"),
                is_workflow_deliberation_enabled(),
            ),
            "deliberation_keywords": self._as_csv(
                overrides.get("deliberation_keywords"),
                get_workflow_deliberation_keywords(),
            ),
            "support_role_name": self._as_str(
                overrides.get("support_role_name"),
                get_workflow_support_role_name(),
            ),
            "support_role_instruction": self._as_str(
                overrides.get("support_role_instruction"),
                get_workflow_support_role_instruction(),
            ),
            "challenge_role_name": self._as_str(
                overrides.get("challenge_role_name"),
                get_workflow_challenge_role_name(),
            ),
            "challenge_role_instruction": self._as_str(
                overrides.get("challenge_role_instruction"),
                get_workflow_challenge_role_instruction(),
            ),
            "arbitration_role_name": self._as_str(
                overrides.get("arbitration_role_name"),
                get_workflow_arbitration_role_name(),
            ),
            "arbitration_role_instruction": self._as_str(
                overrides.get("arbitration_role_instruction"),
                get_workflow_arbitration_role_instruction(),
            ),
            "critic_role_name": self._as_str(
                overrides.get("critic_role_name"),
                get_workflow_critic_role_name(),
            ),
            "critic_role_instruction": self._as_str(
                overrides.get("critic_role_instruction"),
                get_workflow_critic_role_instruction(),
            ),
        }

    def get_workflow_role_overrides(self) -> dict[str, str | None]:
        """
        What this is:
        - A narrow workflow-role override snapshot.

        What it does:
        - Returns only the role-related keys stored in `sys_runtime_config`.
        - Does not apply environment defaults.

        Why this is done this way:
        - Workflow role master data now lives in `sys_workflow_role`.
        - Runtime config should only override that master data when an explicit
          database override exists, otherwise role-table values must remain
          visible to orchestration and API queries.
        """

        overrides = self._load_scope_overrides("workflow")
        return {
            "support_role_name": overrides.get("support_role_name"),
            "support_role_instruction": overrides.get("support_role_instruction"),
            "challenge_role_name": overrides.get("challenge_role_name"),
            "challenge_role_instruction": overrides.get("challenge_role_instruction"),
            "arbitration_role_name": overrides.get("arbitration_role_name"),
            "arbitration_role_instruction": overrides.get("arbitration_role_instruction"),
            "critic_role_name": overrides.get("critic_role_name"),
            "critic_role_instruction": overrides.get("critic_role_instruction"),
        }

    def get_effective_security_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("security")
        return {
            "allowed_tools": self._as_csv(overrides.get("allowed_tools"), get_allowed_tools()),
            "upload_allowed_kinds": self._as_csv(
                overrides.get("upload_allowed_kinds"),
                get_upload_allowed_kinds(),
            ),
            "upload_max_bytes": self._as_int(
                overrides.get("upload_max_bytes"),
                get_upload_max_bytes(),
            ),
            "auth_enabled": self._as_bool(overrides.get("auth_enabled"), is_auth_enabled()),
            "rate_limit_enabled": self._as_bool(
                overrides.get("rate_limit_enabled"),
                is_rate_limit_enabled(),
            ),
            "idempotency_enabled": self._as_bool(
                overrides.get("idempotency_enabled"),
                is_idempotency_enabled(),
            ),
        }

    def get_effective_recovery_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("recovery")
        return {
            "llm_degrade_to_mock": self._as_bool(
                overrides.get("llm_degrade_to_mock"),
                is_recovery_llm_degrade_to_mock_enabled(),
            ),
            "tool_soft_fail": self._as_bool(
                overrides.get("tool_soft_fail"),
                is_recovery_tool_soft_fail_enabled(),
            ),
        }

    def _load_scope_overrides(self, scope: str) -> dict[str, str]:
        rows = self.repository.list_configs(scope=scope)
        return {row["config_key"]: row["config_value"] for row in rows}

    @staticmethod
    def _as_bool(raw_value: str | None, fallback: bool) -> bool:
        if raw_value is None:
            return fallback
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _as_int(raw_value: str | None, fallback: int) -> int:
        if raw_value is None:
            return fallback
        try:
            return max(1, int(raw_value.strip()))
        except ValueError:
            return fallback

    @staticmethod
    def _as_csv(raw_value: str | None, fallback: list[str]) -> list[str]:
        if raw_value is None:
            return fallback
        values = [item.strip() for item in raw_value.split(",") if item.strip()]
        return values or fallback

    @staticmethod
    def _as_str(raw_value: str | None, fallback: str) -> str:
        if raw_value is None:
            return fallback
        return raw_value.strip() or fallback
