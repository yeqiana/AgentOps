"""
Workflow registry tests.

What this is:
- Unit tests for the stage-2 workflow policy registry.

What it does:
- Verifies default role registration.
- Verifies environment overrides for all registered workflow roles.

Why this is done this way:
- Once role registration becomes part of orchestration, the registry must stay
  predictable and queryable.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.workflow.registry import build_workflow_policy_registry


class WorkflowRegistryTests(unittest.TestCase):
    def test_registry_returns_defaults(self) -> None:
        registry = build_workflow_policy_registry()
        self.assertTrue(registry.deliberation_enabled)
        self.assertTrue(registry.deliberation_keywords)
        self.assertTrue(registry.support_role.name)
        self.assertTrue(registry.challenge_role.name)
        self.assertTrue(registry.arbitration_role.name)
        self.assertTrue(registry.critic_role.name)

    def test_registry_respects_environment_overrides(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_WORKFLOW_DELIBERATION_ENABLED": "true",
                "APP_WORKFLOW_DELIBERATION_KEYWORDS": "对比,评估",
                "APP_WORKFLOW_SUPPORT_ROLE_NAME": "正方代理",
                "APP_WORKFLOW_SUPPORT_ROLE_INSTRUCTION": "优先说明方案价值。",
                "APP_WORKFLOW_CHALLENGE_ROLE_NAME": "反方代理",
                "APP_WORKFLOW_CHALLENGE_ROLE_INSTRUCTION": "优先说明方案风险。",
                "APP_WORKFLOW_ARBITRATION_ROLE_NAME": "仲裁代理",
                "APP_WORKFLOW_ARBITRATION_ROLE_INSTRUCTION": "优先整合双方观点。",
                "APP_WORKFLOW_CRITIC_ROLE_NAME": "批评代理",
                "APP_WORKFLOW_CRITIC_ROLE_INSTRUCTION": "优先指出答案缺陷。",
            },
            clear=False,
        ):
            registry = build_workflow_policy_registry()

        self.assertEqual(registry.deliberation_keywords, ["对比", "评估"])
        self.assertEqual(registry.support_role.name, "正方代理")
        self.assertEqual(registry.challenge_role.name, "反方代理")
        self.assertEqual(registry.arbitration_role.name, "仲裁代理")
        self.assertEqual(registry.critic_role.name, "批评代理")
