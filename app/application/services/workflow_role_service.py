"""
Workflow role service.

What this is:
- An application-layer service for stage-2 workflow role registration.

What it does:
- Reads persisted workflow roles from `sys_workflow_role`.
- Merges them with environment-backed defaults when needed.
- Exposes stable role snapshots for orchestration and API queries.

Why this is done this way:
- Multi-agent orchestration should not depend on hard-coded role names.
- A dedicated role service makes role registration explicit and extensible.
"""

from __future__ import annotations

from app.config import (
    get_workflow_arbitration_role_instruction,
    get_workflow_arbitration_role_name,
    get_workflow_challenge_role_instruction,
    get_workflow_challenge_role_name,
    get_workflow_critic_role_instruction,
    get_workflow_critic_role_name,
    get_workflow_support_role_instruction,
    get_workflow_support_role_name,
)
from app.domain.models import WorkflowRoleRecord
from app.infrastructure.persistence.repositories import SQLiteWorkflowRoleRepository


class WorkflowRoleService:
    """
    What this is:
    - The workflow-role registry service used by stage-2 orchestration.

    What it does:
    - Provides current support/challenge/arbitration/critic role definitions.
    - Supports querying and updating persisted role definitions.

    Why this is done this way:
    - This keeps role lookup and fallback rules outside workflow nodes and API
      handlers, which makes future multi-agent expansion manageable.
    """

    def __init__(self, repository: SQLiteWorkflowRoleRepository | None = None) -> None:
        self.repository = repository or SQLiteWorkflowRoleRepository()

    def list_roles(self, *, only_enabled: bool = False) -> list[WorkflowRoleRecord]:
        return self.repository.list_roles(only_enabled=only_enabled)

    def get_effective_roles(self) -> dict[str, WorkflowRoleRecord]:
        records = {item["role_key"]: item for item in self.repository.list_roles()}
        return {
            "support": self._fallback_role(
                records.get("support"),
                role_key="support",
                role_name=get_workflow_support_role_name(),
                role_instruction=get_workflow_support_role_instruction(),
                role_type="debate",
                sort_order=10,
                description="默认支持方角色",
            ),
            "challenge": self._fallback_role(
                records.get("challenge"),
                role_key="challenge",
                role_name=get_workflow_challenge_role_name(),
                role_instruction=get_workflow_challenge_role_instruction(),
                role_type="debate",
                sort_order=20,
                description="默认质疑方角色",
            ),
            "arbitration": self._fallback_role(
                records.get("arbitration"),
                role_key="arbitration",
                role_name=get_workflow_arbitration_role_name(),
                role_instruction=get_workflow_arbitration_role_instruction(),
                role_type="review",
                sort_order=30,
                description="默认仲裁角色",
            ),
            "critic": self._fallback_role(
                records.get("critic"),
                role_key="critic",
                role_name=get_workflow_critic_role_name(),
                role_instruction=get_workflow_critic_role_instruction(),
                role_type="review",
                sort_order=40,
                description="默认批评角色",
            ),
        }

    def upsert_role(
        self,
        *,
        role_key: str,
        role_name: str,
        role_instruction: str,
        is_enabled: bool,
        sort_order: int,
        role_type: str,
        description: str,
        updated_by: str,
    ) -> WorkflowRoleRecord:
        return self.repository.upsert_role(
            role_key=role_key,
            role_name=role_name,
            role_instruction=role_instruction,
            is_enabled=is_enabled,
            sort_order=sort_order,
            role_type=role_type,
            description=description,
            updated_by=updated_by,
        )

    @staticmethod
    def _fallback_role(
        record: WorkflowRoleRecord | None,
        *,
        role_key: str,
        role_name: str,
        role_instruction: str,
        role_type: str,
        sort_order: int,
        description: str,
    ) -> WorkflowRoleRecord:
        if record:
            return record
        return {
            "id": "",
            "role_key": role_key,
            "role_name": role_name,
            "role_instruction": role_instruction,
            "is_enabled": True,
            "sort_order": sort_order,
            "role_type": role_type,
            "description": description,
            "created_by": "env_default",
            "updated_by": "env_default",
            "created_at": "",
            "updated_at": "",
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }
