"""
Workflow role service tests.

What this is:
- Unit tests for the database-backed workflow role service.

What it does:
- Verifies default seeded roles are available.
- Verifies persisted overrides beat environment-backed defaults.

Why this is done this way:
- The role service is now part of stage-2 orchestration. It must remain stable
  before more agent roles are added.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.application.services.workflow_role_service import WorkflowRoleService


class WorkflowRoleServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "agent.db"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"

    def tearDown(self) -> None:
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_default_seeded_roles_exist(self) -> None:
        service = WorkflowRoleService()
        roles = service.list_roles()
        role_keys = [item["role_key"] for item in roles]
        self.assertIn("support", role_keys)
        self.assertIn("challenge", role_keys)
        self.assertIn("arbitration", role_keys)
        self.assertIn("critic", role_keys)

    def test_db_override_beats_environment_role_default(self) -> None:
        service = WorkflowRoleService()
        service.upsert_role(
            role_key="critic",
            role_name="数据库批评代理",
            role_instruction="优先指出数据库覆盖后的问题。",
            is_enabled=True,
            sort_order=40,
            role_type="review",
            description="test override",
            updated_by="tester",
        )

        with patch.dict(os.environ, {"APP_WORKFLOW_CRITIC_ROLE_NAME": "环境批评代理"}, clear=False):
            roles = service.get_effective_roles()

        self.assertEqual(roles["critic"]["role_name"], "数据库批评代理")
