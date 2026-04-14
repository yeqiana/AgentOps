from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.domain.errors import TraceConsistencyError
from app.infrastructure.alert import AlertService, get_alert_service
from app.infrastructure.tools.failure_recovery import emit_recovery_alert
from app.infrastructure.trace import TraceService


class AlertServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'agent.db'}"
        get_alert_service.cache_clear()
        self.trace_service = TraceService()
        self.alert_service = AlertService(trace_service=self.trace_service)

    def tearDown(self) -> None:
        get_alert_service.cache_clear()
        self.temp_dir.cleanup()
        os.environ.pop("APP_DATABASE_URL", None)

    def test_create_alert_accepts_existing_trace(self) -> None:
        trace = self.trace_service.start_trace(source_type="http", method="POST", path="/chat")

        alert = self.alert_service.create_alert(
            trace_id=trace["trace_id"],
            source_type="llm",
            source_name="mock",
            severity="warning",
            event_code="test_alert",
            message="alert",
        )

        self.assertEqual(alert["trace_id"], trace["trace_id"])

    def test_create_alert_rejects_dirty_or_missing_trace_id(self) -> None:
        for trace_id in ["", "none", "test", "trace_missing"]:
            with self.subTest(trace_id=trace_id):
                with self.assertRaises(TraceConsistencyError):
                    self.alert_service.create_alert(
                        trace_id=trace_id,
                        source_type="llm",
                        source_name="mock",
                        severity="warning",
                        event_code="invalid_alert",
                        message="alert",
                    )

    def test_emit_recovery_alert_without_trace_creates_system_trace(self) -> None:
        emit_recovery_alert(
            trace_id="",
            source_type="llm",
            source_name="mock",
            severity="warning",
            event_code="system_recovery_alert",
            message="alert",
        )

        alerts = get_alert_service().list_alerts(source_type="llm", limit=10, offset=0)
        self.assertEqual(len(alerts), 1)
        self.assertNotEqual(alerts[0]["trace_id"], "none")
        trace = self.trace_service.get_trace(alerts[0]["trace_id"])
        self.assertIsNotNone(trace)
        self.assertEqual(trace["method"], "SYSTEM")
        self.assertEqual(trace["path"], "system://alert")


if __name__ == "__main__":
    unittest.main()
