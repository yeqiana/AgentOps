from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.application.agent_service import create_initial_state
from app.application.services.task_service import TaskService
from app.domain.errors import ValidationError
from app.infrastructure.tools.registry import build_default_tool_registry
from app.infrastructure.trace import TraceService


class TaskServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'agent.db'}"
        self.task_service = TaskService(build_default_tool_registry())
        self.trace_service = TraceService()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("APP_DATABASE_URL", None)

    def test_prepare_turn_state_requires_trace_id(self) -> None:
        with self.assertRaises(ValidationError) as context:
            self.task_service.prepare_turn_state(create_initial_state(), "hello", [], trace_id="")

        self.assertIn("TraceService.start_trace", context.exception.message)

    def test_prepare_turn_state_accepts_trace_id_created_by_trace_service(self) -> None:
        trace = self.trace_service.start_trace(source_type="cli")

        state = self.task_service.prepare_turn_state(
            create_initial_state(),
            "hello",
            [],
            trace_id=trace["trace_id"],
        )

        self.assertEqual(state["trace_id"], trace["trace_id"])
        self.assertTrue(state["task_id"])
        self.assertTrue(state["turn_id"])


if __name__ == "__main__":
    unittest.main()
