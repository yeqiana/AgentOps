"""
Routing snapshot tests for runtime configuration service.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.application.services.config_service import RuntimeConfigService


class RuntimeConfigRoutingSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "agent.db"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"

    def tearDown(self) -> None:
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_routing_snapshot_and_template_items_are_centralized(self) -> None:
        service = RuntimeConfigService()
        service.upsert_config(
            scope="routing",
            key="contextual_message_threshold",
            value="5",
            value_type="int",
            description="routing threshold",
            updated_by="tester",
        )

        snapshot = service.get_routing_config_snapshot()
        template_items = service.list_routing_config_template_items()

        self.assertEqual(snapshot["image_route"]["route_name"], "image_analysis")
        self.assertEqual(snapshot["contextual_route"]["message_threshold"], 5)
        self.assertTrue(snapshot["contextual_route"]["enabled"])
        self.assertEqual(template_items[0]["config_key"], "image_route_name")
        template_map = {item["config_key"]: item for item in template_items}
        self.assertEqual(template_map["deliberation_enabled"]["value_type"], "bool")
