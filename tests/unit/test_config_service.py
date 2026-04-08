"""
Runtime configuration service tests.

What this is:
- Unit tests for the database-backed runtime configuration center.

What it does:
- Verifies that database overrides beat environment defaults.
- Verifies that workflow role overrides only come from database records.
- Verifies that security config values are parsed into typed snapshots.

Why this is done this way:
- Stage-2 configuration governance only works if override precedence is stable.
- Role master data and runtime override data now have different responsibilities,
  so both behaviors need explicit tests.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.application.services.config_service import RuntimeConfigService


class RuntimeConfigServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "agent.db"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"

    def tearDown(self) -> None:
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_workflow_db_override_beats_environment_default(self) -> None:
        service = RuntimeConfigService()
        service.upsert_config(
            scope="workflow",
            key="support_role_name",
            value="数据库支持代理",
            value_type="str",
            description="test override",
            updated_by="tester",
        )

        with patch.dict(os.environ, {"APP_WORKFLOW_SUPPORT_ROLE_NAME": "环境支持代理"}, clear=False):
            effective = service.get_effective_workflow_config()

        self.assertEqual(effective["support_role_name"], "数据库支持代理")

    def test_workflow_role_overrides_only_return_database_values(self) -> None:
        service = RuntimeConfigService()

        with patch.dict(os.environ, {"APP_WORKFLOW_SUPPORT_ROLE_NAME": "环境支持代理"}, clear=False):
            overrides = service.get_workflow_role_overrides()

        self.assertIsNone(overrides["support_role_name"])

        service.upsert_config(
            scope="workflow",
            key="support_role_name",
            value="数据库支持代理",
            value_type="str",
            description="test override",
            updated_by="tester",
        )

        overrides = service.get_workflow_role_overrides()
        self.assertEqual(overrides["support_role_name"], "数据库支持代理")

    def test_security_db_override_is_parsed_by_type(self) -> None:
        service = RuntimeConfigService()
        service.upsert_config(
            scope="security",
            key="upload_max_bytes",
            value="512",
            value_type="int",
            description="test override",
            updated_by="tester",
        )
        service.upsert_config(
            scope="security",
            key="allowed_tools",
            value="python_echo,ocr_tesseract",
            value_type="csv",
            description="test override",
            updated_by="tester",
        )

        effective = service.get_effective_security_config()

        self.assertEqual(effective["upload_max_bytes"], 512)
        self.assertEqual(effective["allowed_tools"], ["python_echo", "ocr_tesseract"])
