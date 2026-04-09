"""
Workflow registry.

What this is:
- A small configuration-backed registry for workflow policies and agent roles.

What it does:
- Exposes the current route keywords for deliberation.
- Exposes the current debate-role definitions used by the multi-agent workflow.

Why this is done this way:
- Stage-2 orchestration should stop relying on hidden constants inside nodes.
- A registry makes the current strategy inspectable by API, tests, and future
  admin tooling without introducing a full configuration center yet.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from app.application.services.config_service import RuntimeConfigService
from app.application.services.workflow_role_service import WorkflowRoleService


@dataclass(frozen=True)
class DebateRoleDefinition:
    name: str
    stance_instruction: str


@dataclass(frozen=True)
class WorkflowPolicyRegistry:
    execution_mode: str
    deliberation_enabled: bool
    deliberation_keywords: list[str]
    support_role: DebateRoleDefinition
    challenge_role: DebateRoleDefinition
    planner_role: DebateRoleDefinition
    executor_role: DebateRoleDefinition
    arbitration_role: DebateRoleDefinition
    critic_role: DebateRoleDefinition
    reviewer_role: DebateRoleDefinition

    def to_dict(self) -> dict[str, object]:
        return {
            "execution_mode": self.execution_mode,
            "deliberation_enabled": self.deliberation_enabled,
            "deliberation_keywords": list(self.deliberation_keywords),
            "support_role": asdict(self.support_role),
            "challenge_role": asdict(self.challenge_role),
            "planner_role": asdict(self.planner_role),
            "executor_role": asdict(self.executor_role),
            "arbitration_role": asdict(self.arbitration_role),
            "critic_role": asdict(self.critic_role),
            "reviewer_role": asdict(self.reviewer_role),
        }


def _get_env_override(env_key: str) -> str | None:
    """
    What this is:
    - A small helper for explicit environment-based role overrides.

    What it does:
    - Returns a trimmed environment value only when the variable is explicitly
      present and non-empty.

    Why this is done this way:
    - Workflow role defaults are seeded into `sys_workflow_role`, so merely
      reading "effective" values is not enough to tell whether an operator
      intentionally overrode a role via environment variables.
    """

    raw_value = os.getenv(env_key)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def build_workflow_policy_registry(
    config_service: RuntimeConfigService | None = None,
    workflow_role_service: WorkflowRoleService | None = None,
) -> WorkflowPolicyRegistry:
    runtime_config_service = config_service or RuntimeConfigService()
    effective_config = runtime_config_service.get_effective_workflow_config()
    role_overrides = runtime_config_service.get_workflow_role_overrides()
    effective_roles = (workflow_role_service or WorkflowRoleService()).get_effective_roles()
    return WorkflowPolicyRegistry(
        execution_mode=effective_config["execution_mode"],
        deliberation_enabled=effective_config["deliberation_enabled"],
        deliberation_keywords=effective_config["deliberation_keywords"],
        support_role=DebateRoleDefinition(
            name=role_overrides["support_role_name"]
            or _get_env_override("APP_WORKFLOW_SUPPORT_ROLE_NAME")
            or effective_roles["support"]["role_name"],
            stance_instruction=role_overrides["support_role_instruction"]
            or _get_env_override("APP_WORKFLOW_SUPPORT_ROLE_INSTRUCTION")
            or effective_roles["support"]["role_instruction"],
        ),
        challenge_role=DebateRoleDefinition(
            name=role_overrides["challenge_role_name"]
            or _get_env_override("APP_WORKFLOW_CHALLENGE_ROLE_NAME")
            or effective_roles["challenge"]["role_name"],
            stance_instruction=role_overrides["challenge_role_instruction"]
            or _get_env_override("APP_WORKFLOW_CHALLENGE_ROLE_INSTRUCTION")
            or effective_roles["challenge"]["role_instruction"],
        ),
        planner_role=DebateRoleDefinition(
            name=role_overrides["planner_role_name"]
            or _get_env_override("APP_WORKFLOW_PLANNER_ROLE_NAME")
            or effective_roles["planner"]["role_name"],
            stance_instruction=role_overrides["planner_role_instruction"]
            or _get_env_override("APP_WORKFLOW_PLANNER_ROLE_INSTRUCTION")
            or effective_roles["planner"]["role_instruction"],
        ),
        executor_role=DebateRoleDefinition(
            name=role_overrides["executor_role_name"]
            or _get_env_override("APP_WORKFLOW_EXECUTOR_ROLE_NAME")
            or effective_roles["executor"]["role_name"],
            stance_instruction=role_overrides["executor_role_instruction"]
            or _get_env_override("APP_WORKFLOW_EXECUTOR_ROLE_INSTRUCTION")
            or effective_roles["executor"]["role_instruction"],
        ),
        arbitration_role=DebateRoleDefinition(
            name=role_overrides["arbitration_role_name"]
            or _get_env_override("APP_WORKFLOW_ARBITRATION_ROLE_NAME")
            or effective_roles["arbitration"]["role_name"],
            stance_instruction=role_overrides["arbitration_role_instruction"]
            or _get_env_override("APP_WORKFLOW_ARBITRATION_ROLE_INSTRUCTION")
            or effective_roles["arbitration"]["role_instruction"],
        ),
        critic_role=DebateRoleDefinition(
            name=role_overrides["critic_role_name"]
            or _get_env_override("APP_WORKFLOW_CRITIC_ROLE_NAME")
            or effective_roles["critic"]["role_name"],
            stance_instruction=role_overrides["critic_role_instruction"]
            or _get_env_override("APP_WORKFLOW_CRITIC_ROLE_INSTRUCTION")
            or effective_roles["critic"]["role_instruction"],
        ),
        reviewer_role=DebateRoleDefinition(
            name=role_overrides["reviewer_role_name"]
            or _get_env_override("APP_WORKFLOW_REVIEWER_ROLE_NAME")
            or effective_roles["reviewer"]["role_name"],
            stance_instruction=role_overrides["reviewer_role_instruction"]
            or _get_env_override("APP_WORKFLOW_REVIEWER_ROLE_INSTRUCTION")
            or effective_roles["reviewer"]["role_instruction"],
        ),
    )
