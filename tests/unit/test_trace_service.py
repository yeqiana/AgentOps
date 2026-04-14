from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.domain.errors import TraceConsistencyError
from app.infrastructure.trace import TraceService


class TraceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'agent.db'}"
        self.trace_service = TraceService()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("APP_DATABASE_URL", None)

    def test_start_trace_creates_http_cli_and_system_records(self) -> None:
        http_trace = self.trace_service.start_trace(source_type="http", method="POST", path="/chat")
        cli_trace = self.trace_service.start_trace(source_type="cli")
        system_trace = self.trace_service.start_trace(source_type="system")

        self.assertEqual(self.trace_service.get_trace(http_trace["trace_id"])["path"], "/chat")
        self.assertEqual(self.trace_service.get_trace(cli_trace["trace_id"])["method"], "CLI")
        self.assertEqual(self.trace_service.get_trace(cli_trace["trace_id"])["path"], "cli://chat")
        self.assertEqual(self.trace_service.get_trace(system_trace["trace_id"])["method"], "SYSTEM")
        self.assertEqual(self.trace_service.get_trace(system_trace["trace_id"])["path"], "system://alert")

    def test_start_trace_reuses_existing_trace_id_only_when_record_exists(self) -> None:
        trace = self.trace_service.start_trace(source_type="background")

        reused = self.trace_service.start_trace(source_type="background", existing_trace_id=trace["trace_id"])

        self.assertEqual(reused["trace_id"], trace["trace_id"])
        with self.assertRaises(TraceConsistencyError):
            self.trace_service.start_trace(source_type="background", existing_trace_id="trace_missing")

    def test_attach_execution_context_updates_existing_trace_and_rejects_missing_trace(self) -> None:
        trace = self.trace_service.start_trace(source_type="http", method="POST", path="/chat")

        self.trace_service.attach_execution_context(
            trace["trace_id"],
            session_id="session_1",
            turn_id="turn_1",
            task_id="task_1",
        )

        updated = self.trace_service.get_trace(trace["trace_id"])
        self.assertEqual(updated["session_id"], "session_1")
        self.assertEqual(updated["turn_id"], "turn_1")
        self.assertEqual(updated["task_id"], "task_1")
        with self.assertRaises(TraceConsistencyError):
            self.trace_service.attach_execution_context("trace_missing", session_id="s", turn_id="t", task_id="task")


if __name__ == "__main__":
    unittest.main()
