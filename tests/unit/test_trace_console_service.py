import unittest
from unittest.mock import Mock

from app.application.services.trace_console_service import TraceConsoleService


class TraceConsoleServiceTests(unittest.TestCase):
    def test_list_console_traces_maps_stable_fields_and_pagination(self) -> None:
        trace_service = Mock()
        trace_service.list_console_traces.return_value = [
            {
                "trace_id": "trace_1",
                "request_id": "req_1",
                "method": "POST",
                "path": "/chat",
                "status_code": 200,
                "error_code": "",
                "rate_limited": False,
                "started_at": "2026-04-10T10:00:00+00:00",
                "updated_at": "2026-04-10T10:00:03+00:00",
                "session_id": "session_1",
                "turn_id": "turn_1",
                "task_id": "task_1",
                "route_name": "direct_chat",
                "route_source": "request_entry",
                "execution_mode": "delegated",
                "review_status": "pass",
                "alert_count": 1,
                "last_event_at": "2026-04-10T10:00:03+00:00",
            }
        ]
        trace_service.count_console_traces.return_value = 3
        service = TraceConsoleService(
            trace_service=trace_service,
            session_service=Mock(),
            alert_service=Mock(),
        )

        payload = service.list_console_traces(page=2, page_size=1)

        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["page_size"], 1)
        self.assertEqual(payload["total"], 3)
        self.assertTrue(payload["has_next"])
        self.assertEqual(payload["items"][0]["trace_id"], "trace_1")
        self.assertEqual(payload["items"][0]["route_name"], "direct_chat")
        self.assertEqual(payload["items"][0]["execution_mode"], "delegated")
        self.assertEqual(payload["items"][0]["alert_count"], 1)

    def test_get_trace_viewer_builds_console_payload(self) -> None:
        trace_service = Mock()
        trace_service.get_trace.return_value = {
            "trace_id": "trace_1",
            "request_id": "req_1",
            "method": "POST",
            "path": "/chat",
            "auth_subject": "tester",
            "auth_type": "api_key",
            "session_id": "session_1",
            "turn_id": "turn_1",
            "task_id": "task_1",
            "status_code": 200,
            "error_code": "",
            "idempotency_key": "",
            "rate_limited": False,
            "started_at": "2026-04-10T10:00:00+00:00",
            "updated_at": "2026-04-10T10:00:03+00:00",
        }
        session_service = Mock()
        session_service.get_task.return_value = {
            "task": {
                "id": "task_1",
                "session_id": "session_1",
                "turn_id": "turn_1",
                "trace_id": "trace_1",
                "status": "completed",
                "user_input": "hello",
                "execution_mode": "delegated",
                "protocol_summary": "planner -> executor -> reviewer",
                "route_name": "direct_chat",
                "route_reason": "default",
                "route_source": "request_entry",
                "plan": "",
                "debate_summary": "",
                "arbitration_summary": "",
                "answer": "ok",
                "critic_summary": "",
                "review_status": "pass",
                "review_summary": "approved",
                "tool_count": 0,
                "error_message": "",
                "created_at": "2026-04-10T10:00:01+00:00",
                "updated_at": "2026-04-10T10:00:03+00:00",
            },
            "task_events": [
                {
                    "id": "event_1",
                    "task_id": "task_1",
                    "session_id": "session_1",
                    "turn_id": "turn_1",
                    "trace_id": "trace_1",
                    "event_type": "completed",
                    "event_message": "done",
                    "event_payload_json": "{}",
                    "created_at": "2026-04-10T10:00:03+00:00",
                }
            ],
            "tool_results": [],
            "route_decisions": [
                {
                    "id": "route_1",
                    "task_id": "task_1",
                    "session_id": "session_1",
                    "turn_id": "turn_1",
                    "trace_id": "trace_1",
                    "route_name": "direct_chat",
                    "route_reason": "default",
                    "route_source": "request_entry",
                    "created_at": "2026-04-10T10:00:01+00:00",
                }
            ],
        }
        alert_service = Mock()
        alert_service.list_alerts.return_value = [
            {
                "id": "alert_1",
                "trace_id": "trace_1",
                "source_type": "llm",
                "source_name": "mock",
                "severity": "warning",
                "event_code": "viewer_test",
                "message": "warn",
                "payload_json": "{}",
                "created_at": "2026-04-10T10:00:02+00:00",
                "updated_at": "2026-04-10T10:00:02+00:00",
            }
        ]
        service = TraceConsoleService(
            trace_service=trace_service,
            session_service=session_service,
            alert_service=alert_service,
        )

        payload = service.get_trace_viewer("trace_1")

        self.assertIsNotNone(payload)
        viewer = payload["viewer"]
        self.assertEqual(viewer["trace"]["trace_id"], "trace_1")
        self.assertEqual(viewer["summary"]["task"]["id"], "task_1")
        self.assertEqual(viewer["alerts"][0]["event_code"], "viewer_test")
        self.assertIn("timeline", viewer)
        self.assertIn("graph_nodes", viewer)
        self.assertIn("graph_edges", viewer)
        self.assertTrue(any(item["node_type"] == "route" for item in viewer["graph_nodes"]))


if __name__ == "__main__":
    unittest.main()
