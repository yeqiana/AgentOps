"""
API integration tests.

What this is:
- Integration tests for the FastAPI HTTP layer.

What it does:
- Verifies success paths, structured error responses, task/session queries, and
  the new multipart upload endpoint.

Why this is done this way:
- The API is the shared entrypoint for external clients, so protocol stability
- and end-to-end behavior matter more than isolated unit assertions alone.
"""

from __future__ import annotations

import base64
from concurrent.futures import Future
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app.infrastructure.alert import get_alert_service
from app.domain.errors import AgentError
from app.infrastructure.trace import TraceService
from app.presentation.api import create_app


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAgMBgF4L3vQAAAAASUVORK5CYII="
)


class ApiHttpTests(unittest.TestCase):
    """
    What this is:
    - A `unittest.TestCase` suite for HTTP-level integration.

    What it does:
    - Exercises the FastAPI app through `TestClient`.

    Why this is done this way:
    - This catches route wiring, schema shape, and persistence side effects in
      one place before running full live-server validation.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        base_path = Path(self.temp_dir.name)
        database_path = base_path / "agent.db"
        upload_path = base_path / "uploads"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"
        os.environ["APP_DOWNLOAD_DIR"] = str(upload_path)
        os.environ["LLM_PROVIDER"] = "mock"
        from fastapi.testclient import TestClient

        self.client = TestClient(create_app())
        self.upload_path = upload_path

    def tearDown(self) -> None:
        for name in [
            "APP_AUTH_ENABLED",
            "APP_RBAC_ENABLED",
            "APP_AUTH_ADMIN_SUBJECTS",
            "APP_API_KEYS",
            "APP_BEARER_TOKENS",
            "APP_RATE_LIMIT_ENABLED",
            "APP_RATE_LIMIT_REQUESTS",
            "APP_RATE_LIMIT_WINDOW_SECONDS",
            "APP_IDEMPOTENCY_ENABLED",
            "APP_IDEMPOTENCY_TTL_SECONDS",
        ]:
            os.environ.pop(name, None)
        get_alert_service.cache_clear()
        self.temp_dir.cleanup()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.headers["X-Trace-Id"])
        self.assertTrue(response.headers["X-Request-Id"])

    def test_tools_endpoints(self) -> None:
        list_response = self.client.get("/tools")
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertGreaterEqual(len(list_payload["tools"]), 1)
        self.assertEqual(list_payload["tools"][0]["name"], "python_echo")

        execute_response = self.client.post(
            "/tools/python_echo/execute",
            json={"parameters": {"message": "hello tool"}},
        )
        self.assertEqual(execute_response.status_code, 200)
        execute_payload = execute_response.json()
        self.assertEqual(execute_payload["result"]["tool_name"], "python_echo")
        self.assertTrue(execute_payload["result"]["success"])
        self.assertEqual(execute_payload["result"]["stdout"], "hello tool")

    def test_workflow_config_endpoint(self) -> None:
        response = self.client.get("/workflow/config")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["workflow"]
        self.assertIn("execution_mode", payload)
        self.assertIn("deliberation_enabled", payload)
        self.assertIn("deliberation_keywords", payload)
        self.assertIn("support_role", payload)
        self.assertIn("challenge_role", payload)
        self.assertIn("planner_role", payload)
        self.assertIn("executor_role", payload)
        self.assertIn("arbitration_role", payload)
        self.assertIn("critic_role", payload)
        self.assertIn("reviewer_role", payload)
        self.assertTrue(payload["support_role"]["name"])

    def test_runtime_config_endpoints_affect_workflow_execution_mode(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "workflow",
                "config_key": "execution_mode",
                "config_value": "standard",
                "value_type": "str",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)

        workflow_response = self.client.get("/workflow/config")
        self.assertEqual(workflow_response.status_code, 200)
        workflow_payload = workflow_response.json()["workflow"]
        self.assertEqual(workflow_payload["execution_mode"], "standard")

    def test_runtime_config_endpoints_affect_routing_decision(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "routing",
                "config_key": "image_route_name",
                "config_value": "custom_image_flow",
                "value_type": "str",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)

        response = self.client.post(
            "/assets/analyze",
            json={
                "input": "/image 这是一张测试图片",
                "run_tools": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["route_name"], "custom_image_flow")

    def test_routing_config_endpoint_returns_visual_snapshot(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "routing",
                "config_key": "contextual_message_threshold",
                "config_value": "5",
                "value_type": "int",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)

        response = self.client.get("/routing/config")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["routing"]
        self.assertEqual(payload["image_route"]["route_name"], "image_analysis")
        self.assertIn("route_reason", payload["file_route"])
        self.assertTrue(payload["deliberation_route"]["enabled"])
        self.assertIsInstance(payload["deliberation_route"]["keywords"], list)
        self.assertEqual(payload["contextual_route"]["message_threshold"], 5)

    def test_routing_config_template_endpoint_returns_supported_keys(self) -> None:
        response = self.client.get("/routing/config/template")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["templates"]
        self.assertGreaterEqual(len(payload), 10)
        self.assertEqual(payload[0]["config_key"], "image_route_name")
        template_map = {item["config_key"]: item for item in payload}
        self.assertEqual(template_map["deliberation_enabled"]["value_type"], "bool")
        self.assertEqual(template_map["contextual_message_threshold"]["value_type"], "int")

    def test_runtime_config_rejects_unknown_routing_key(self) -> None:
        response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "routing",
                "config_key": "unknown_route_key",
                "config_value": "bad_value",
                "value_type": "str",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], "validation_error")
        self.assertIn("不存在", payload["message"])

    def test_runtime_config_rejects_invalid_routing_type(self) -> None:
        response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "routing",
                "config_key": "contextual_message_threshold",
                "config_value": "abc",
                "value_type": "int",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], "validation_error")
        self.assertIn("int", payload["message"])

    def test_route_stats_endpoint_returns_grouped_route_summary(self) -> None:
        first_response = self.client.post(
            "/chat",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "route-stat-user",
                "session_title": "Route Stats Session",
            },
        )
        self.assertEqual(first_response.status_code, 200)
        first_payload = first_response.json()

        second_response = self.client.post(
            "/assets/upload",
            files={"file": ("note.txt", b"hello upload", "text/plain")},
            data={"kind": "file", "prompt": "请总结文档"},
        )
        self.assertEqual(second_response.status_code, 200)
        second_payload = second_response.json()

        stats_response = self.client.get("/routes/stats")
        self.assertEqual(stats_response.status_code, 200)
        stats_payload = stats_response.json()["stats"]
        self.assertGreaterEqual(len(stats_payload), 2)
        route_names = {item["route_name"] for item in stats_payload}
        self.assertIn(first_payload["route_name"], route_names)
        self.assertIn(second_payload["route_name"], route_names)

        filtered_stats_response = self.client.get(f"/routes/stats?trace_id={second_payload['trace_id']}")
        self.assertEqual(filtered_stats_response.status_code, 200)
        filtered_stats = filtered_stats_response.json()["stats"]
        self.assertEqual(len(filtered_stats), 1)
        self.assertEqual(filtered_stats[0]["route_name"], second_payload["route_name"])
        self.assertEqual(filtered_stats[0]["last_trace_id"], second_payload["trace_id"])
        self.assertGreaterEqual(filtered_stats[0]["decision_count"], 1)

    def test_workflow_role_endpoints_can_query_and_update_role(self) -> None:
        list_response = self.client.get("/workflow/roles")
        self.assertEqual(list_response.status_code, 200)
        roles = list_response.json()["roles"]
        self.assertGreaterEqual(len(roles), 7)

        put_response = self.client.put(
            "/workflow/roles/critic",
            json={
                "name": "数据库批评代理",
                "stance_instruction": "优先指出答案中最关键的问题。",
                "is_enabled": True,
                "sort_order": 35,
                "role_type": "review",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)
        payload = put_response.json()["role"]
        self.assertEqual(payload["role_key"], "critic")
        self.assertEqual(payload["name"], "数据库批评代理")

        workflow_response = self.client.get("/workflow/config")
        self.assertEqual(workflow_response.status_code, 200)
        workflow_payload = workflow_response.json()["workflow"]
        self.assertEqual(workflow_payload["critic_role"]["name"], "数据库批评代理")

    def test_security_config_endpoint(self) -> None:
        os.environ["APP_ALLOWED_TOOLS"] = "python_echo"
        os.environ["APP_UPLOAD_ALLOWED_KINDS"] = "image,file"
        os.environ["APP_UPLOAD_MAX_BYTES"] = "1024"
        os.environ["APP_AUTH_ENABLED"] = "true"
        os.environ["APP_API_KEYS"] = "demo-key"
        os.environ["APP_RATE_LIMIT_ENABLED"] = "true"
        os.environ["APP_IDEMPOTENCY_ENABLED"] = "true"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.get("/security/config", headers={"X-API-Key": "demo-key"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()["security"]
        self.assertEqual(payload["allowed_tools"], ["python_echo"])
        self.assertEqual(payload["upload_allowed_kinds"], ["image", "file"])
        self.assertEqual(payload["upload_max_bytes"], 1024)
        self.assertTrue(payload["auth_enabled"])
        self.assertTrue(payload["rate_limit_enabled"])
        self.assertTrue(payload["idempotency_enabled"])
        for name in [
            "APP_ALLOWED_TOOLS",
            "APP_UPLOAD_ALLOWED_KINDS",
            "APP_UPLOAD_MAX_BYTES",
            "APP_AUTH_ENABLED",
            "APP_API_KEYS",
            "APP_RATE_LIMIT_ENABLED",
            "APP_IDEMPOTENCY_ENABLED",
        ]:
            os.environ.pop(name, None)

    def test_runtime_config_endpoints_persist_and_affect_workflow(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "workflow",
                "config_key": "support_role_name",
                "config_value": "数据库支持代理",
                "value_type": "str",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)
        put_payload = put_response.json()["config"]
        self.assertEqual(put_payload["config_scope"], "workflow")
        self.assertEqual(put_payload["config_key"], "support_role_name")

        list_response = self.client.get("/config/runtime?scope=workflow")
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()["configs"]
        self.assertEqual(len(list_payload), 1)
        self.assertEqual(list_payload[0]["config_value"], "数据库支持代理")

        workflow_response = self.client.get("/workflow/config")
        self.assertEqual(workflow_response.status_code, 200)
        workflow_payload = workflow_response.json()["workflow"]
        self.assertEqual(workflow_payload["support_role"]["name"], "数据库支持代理")

        critic_put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "workflow",
                "config_key": "critic_role_name",
                "config_value": "数据库批评代理",
                "value_type": "str",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(critic_put_response.status_code, 200)

        workflow_response = self.client.get("/workflow/config")
        self.assertEqual(workflow_response.status_code, 200)
        workflow_payload = workflow_response.json()["workflow"]
        self.assertEqual(workflow_payload["critic_role"]["name"], "数据库批评代理")

    def test_runtime_config_endpoints_affect_security_snapshot(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "security",
                "config_key": "upload_max_bytes",
                "config_value": "2048",
                "value_type": "int",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)

        security_response = self.client.get("/security/config")
        self.assertEqual(security_response.status_code, 200)
        security_payload = security_response.json()["security"]
        self.assertEqual(security_payload["upload_max_bytes"], 2048)

    def test_runtime_config_endpoints_affect_recovery_snapshot(self) -> None:
        put_response = self.client.put(
            "/config/runtime",
            json={
                "config_scope": "recovery",
                "config_key": "llm_degrade_to_mock",
                "config_value": "true",
                "value_type": "bool",
                "description": "integration test",
                "updated_by": "tester",
            },
        )
        self.assertEqual(put_response.status_code, 200)

        recovery_response = self.client.get("/recovery/config")
        self.assertEqual(recovery_response.status_code, 200)
        recovery_payload = recovery_response.json()["recovery"]
        self.assertTrue(recovery_payload["llm_degrade_to_mock"])

    def test_trace_endpoint_returns_request_trace(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "trace-user",
                "session_title": "Trace Session",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        trace_response = self.client.get(f"/traces/{payload['trace_id']}")
        self.assertEqual(trace_response.status_code, 200)
        trace_payload = trace_response.json()["trace"]
        self.assertEqual(trace_payload["trace_id"], payload["trace_id"])
        self.assertEqual(trace_payload["task_id"], payload["task_id"])
        self.assertEqual(trace_payload["session_id"], payload["session_id"])
        self.assertEqual(trace_payload["status_code"], 200)

    def test_trace_summary_endpoint_returns_aggregated_execution_view(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "trace-summary-user",
                "session_title": "Trace Summary Session",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        get_alert_service().create_alert(
            trace_id=payload["trace_id"],
            source_type="llm",
            source_name="mock",
            severity="warning",
            event_code="summary_test_alert",
            message="trace summary integration test",
            payload={"task_id": payload["task_id"]},
        )

        summary_response = self.client.get(f"/traces/{payload['trace_id']}/summary")
        self.assertEqual(summary_response.status_code, 200)
        summary = summary_response.json()["summary"]
        self.assertEqual(summary["trace"]["trace_id"], payload["trace_id"])
        self.assertEqual(summary["task"]["id"], payload["task_id"])
        self.assertGreaterEqual(len(summary["route_decisions"]), 1)
        self.assertGreaterEqual(len(summary["task_events"]), 1)
        self.assertEqual(summary["task_events"][-1]["event_type"], "completed")
        self.assertEqual(summary["alerts"][0]["event_code"], "summary_test_alert")

    def test_task_summary_endpoint_returns_aggregated_execution_view(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "task-summary-user",
                "session_title": "Task Summary Session",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        get_alert_service().create_alert(
            trace_id=payload["trace_id"],
            source_type="tool",
            source_name="python_echo",
            severity="info",
            event_code="task_summary_test_alert",
            message="task summary integration test",
            payload={"task_id": payload["task_id"]},
        )

        summary_response = self.client.get(f"/tasks/{payload['task_id']}/summary")
        self.assertEqual(summary_response.status_code, 200)
        summary = summary_response.json()["summary"]
        self.assertEqual(summary["task"]["id"], payload["task_id"])
        self.assertEqual(summary["trace"]["trace_id"], payload["trace_id"])
        self.assertGreaterEqual(len(summary["task_events"]), 1)
        self.assertGreaterEqual(len(summary["route_decisions"]), 1)
        self.assertEqual(summary["alerts"][0]["event_code"], "task_summary_test_alert")

    def test_alert_endpoints_can_query_persisted_alerts(self) -> None:
        alert = get_alert_service().create_alert(
            trace_id="trace_alert_test",
            source_type="llm",
            source_name="openai:gpt-4o-mini",
            severity="warning",
            event_code="llm_retry_exhausted",
            message="模型重试后仍失败。",
            payload={"attempts": 2},
        )

        list_response = self.client.get("/alerts?source_type=llm")
        self.assertEqual(list_response.status_code, 200)
        alerts = list_response.json()["alerts"]
        self.assertGreaterEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["source_type"], "llm")

        detail_response = self.client.get(f"/alerts/{alert['id']}")
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()["alert"]
        self.assertEqual(detail_payload["id"], alert["id"])
        self.assertEqual(detail_payload["event_code"], "llm_retry_exhausted")

    def test_trace_alert_endpoint_returns_alerts_for_trace(self) -> None:
        get_alert_service().create_alert(
            trace_id="trace_linked_alert",
            source_type="tool",
            source_name="ffmpeg",
            severity="error",
            event_code="tool_circuit_opened",
            message="工具连续失败已触发熔断。",
            payload={"failure_count": 3},
        )

        trace_service = TraceService()
        trace_service.begin_request(
            trace_id="trace_linked_alert",
            request_id="req_trace_linked",
            method="GET",
            path="/tools",
            auth_subject="tester",
            auth_type="api_key",
            idempotency_key="",
        )
        trace_service.finish_request("trace_linked_alert", status_code=200)

        response = self.client.get("/traces/trace_linked_alert/alerts")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["alerts"]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["trace_id"], "trace_linked_alert")
        self.assertEqual(payload[0]["event_code"], "tool_circuit_opened")

    def test_chat_sessions_and_task_endpoints(self) -> None:
        chat_response = self.client.post(
            "/chat",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "api-test-user",
                "session_title": "API Test Session",
            },
        )
        self.assertEqual(chat_response.status_code, 200)
        payload = chat_response.json()
        self.assertIn("session_id", payload)
        self.assertIn("task_id", payload)
        self.assertIn("trace_id", payload)
        self.assertIn("execution_mode", payload)
        self.assertIn("protocol_summary", payload)
        self.assertIn("route_name", payload)
        self.assertIn("debate_summary", payload)
        self.assertIn("arbitration_summary", payload)
        self.assertIn("critic_summary", payload)
        self.assertIn("review_status", payload)
        self.assertIn("tool_names", payload)

        sessions_response = self.client.get("/sessions")
        self.assertEqual(sessions_response.status_code, 200)
        sessions_payload = sessions_response.json()
        self.assertGreaterEqual(len(sessions_payload["sessions"]), 1)
        self.assertEqual(sessions_payload["sessions"][0]["id"], payload["session_id"])

        paged_sessions_response = self.client.get("/sessions?limit=1&offset=0")
        self.assertEqual(paged_sessions_response.status_code, 200)
        paged_sessions_payload = paged_sessions_response.json()
        self.assertEqual(len(paged_sessions_payload["sessions"]), 1)

        session_response = self.client.get(f"/sessions/{payload['session_id']}")
        self.assertEqual(session_response.status_code, 200)
        session_payload = session_response.json()
        self.assertEqual(session_payload["session"]["id"], payload["session_id"])
        self.assertGreaterEqual(len(session_payload["messages"]), 2)

        session_tasks_response = self.client.get(f"/sessions/{payload['session_id']}/tasks")
        self.assertEqual(session_tasks_response.status_code, 200)
        session_tasks_payload = session_tasks_response.json()
        self.assertGreaterEqual(len(session_tasks_payload["tasks"]), 1)
        self.assertEqual(session_tasks_payload["tasks"][0]["task"]["session_id"], payload["session_id"])

        task_response = self.client.get(f"/tasks/{payload['task_id']}")
        self.assertEqual(task_response.status_code, 200)
        task_payload = task_response.json()
        self.assertEqual(task_payload["task"]["id"], payload["task_id"])
        self.assertEqual(task_payload["task"]["session_id"], payload["session_id"])
        self.assertEqual(task_payload["task"]["status"], "completed")
        self.assertEqual(task_payload["task"]["execution_mode"], payload["execution_mode"])
        self.assertEqual(task_payload["task"]["protocol_summary"], payload["protocol_summary"])
        self.assertEqual(task_payload["task"]["route_name"], payload["route_name"])
        self.assertEqual(task_payload["task"]["debate_summary"], payload["debate_summary"])
        self.assertEqual(task_payload["task"]["arbitration_summary"], payload["arbitration_summary"])
        self.assertEqual(task_payload["task"]["critic_summary"], payload["critic_summary"])
        self.assertEqual(task_payload["task"]["review_status"], payload["review_status"])
        self.assertIn("tool_results", task_payload)
        self.assertIn("route_decisions", task_payload)
        self.assertIsInstance(task_payload["tool_results"], list)
        self.assertIsInstance(task_payload["route_decisions"], list)
        self.assertGreaterEqual(len(task_payload["route_decisions"]), 1)
        self.assertEqual(task_payload["route_decisions"][0]["route_name"], payload["route_name"])

        task_routes_response = self.client.get(f"/tasks/{payload['task_id']}/routes")
        self.assertEqual(task_routes_response.status_code, 200)
        task_routes_payload = task_routes_response.json()
        self.assertGreaterEqual(len(task_routes_payload["route_decisions"]), 1)
        self.assertEqual(task_routes_payload["route_decisions"][0]["task_id"], payload["task_id"])

        filtered_routes_response = self.client.get(f"/routes?trace_id={payload['trace_id']}")
        self.assertEqual(filtered_routes_response.status_code, 200)
        filtered_routes_payload = filtered_routes_response.json()
        self.assertGreaterEqual(len(filtered_routes_payload["route_decisions"]), 1)
        self.assertEqual(filtered_routes_payload["route_decisions"][0]["trace_id"], payload["trace_id"])

        tasks_response = self.client.get("/tasks?status=completed")
        self.assertEqual(tasks_response.status_code, 200)
        tasks_payload = tasks_response.json()
        self.assertGreaterEqual(len(tasks_payload["tasks"]), 1)
        self.assertEqual(tasks_payload["tasks"][0]["task"]["status"], "completed")

    def test_chat_stream_endpoint_returns_sse_events_and_persists_task(self) -> None:
        with self.client.stream(
            "POST",
            "/chat/stream",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "stream-user",
                "session_title": "Stream Session",
            },
        ) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"].split(";")[0], "text/event-stream")
            body = "".join(response.iter_text())

        self.assertIn("event: metadata", body)
        self.assertIn("event: answer_delta", body)
        self.assertIn("event: done", body)

        metadata_line = next(line for line in body.splitlines() if line.startswith("data: {") and '"task_id"' in line)
        metadata = json.loads(metadata_line[len("data: ") :])
        self.assertIn("execution_mode", metadata)
        self.assertIn("protocol_summary", metadata)

        task_response = self.client.get(f"/tasks/{metadata['task_id']}")
        self.assertEqual(task_response.status_code, 200)
        task_payload = task_response.json()
        self.assertEqual(task_payload["task"]["id"], metadata["task_id"])

    def test_async_task_submit_endpoint_queues_and_completes_task(self) -> None:
        runtime_before = self.client.get("/tasks/runtime")
        self.assertEqual(runtime_before.status_code, 200)
        self.assertIn("active_task_count", runtime_before.json()["runtime"])

        response = self.client.post(
            "/tasks/submit",
            json={
                "message": "帮我写一句简短的自我介绍",
                "user_name": "async-user",
                "session_title": "Async Session",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "queued")
        self.assertTrue(payload["task_id"])

        final_status = ""
        final_task_payload: dict[str, object] = {}
        for _ in range(20):
            task_response = self.client.get(f"/tasks/{payload['task_id']}")
            self.assertEqual(task_response.status_code, 200)
            final_task_payload = task_response.json()
            final_status = final_task_payload["task"]["status"]
            if final_status in {"completed", "failed"}:
                break
            time.sleep(0.1)

        self.assertIn(final_status, {"completed", "failed"})
        self.assertEqual(final_task_payload["task"]["id"], payload["task_id"])
        self.assertEqual(final_task_payload["task"]["session_id"], payload["session_id"])
        self.assertGreaterEqual(len(final_task_payload["task_events"]), 2)

        events_response = self.client.get(f"/tasks/{payload['task_id']}/events")
        self.assertEqual(events_response.status_code, 200)
        events_payload = events_response.json()["task_events"]
        event_types = [item["event_type"] for item in events_payload]
        self.assertIn("queued", event_types)
        self.assertIn("running", event_types)
        self.assertTrue(any(item in {"completed", "failed"} for item in event_types))

    def test_async_task_can_be_canceled_while_queued(self) -> None:
        from fastapi.testclient import TestClient

        def fake_submit(self, task_id: str, fn):
            future: Future[None] = Future()
            with self.lock:
                self.futures[task_id] = future
            future.add_done_callback(lambda _: self._cleanup(task_id))
            return future

        with patch("app.presentation.api.app.BackgroundTaskRunner.submit", new=fake_submit):
            client = TestClient(create_app())
            submit_response = client.post(
                "/tasks/submit",
                json={
                    "message": "帮我写一句简短的自我介绍",
                    "user_name": "cancel-user",
                    "session_title": "Cancel Session",
                },
            )

            self.assertEqual(submit_response.status_code, 200)
            payload = submit_response.json()
            self.assertEqual(payload["status"], "queued")

            cancel_response = client.post(f"/tasks/{payload['task_id']}/cancel")
            self.assertEqual(cancel_response.status_code, 200)
            canceled_payload = cancel_response.json()
            self.assertEqual(canceled_payload["task"]["status"], "canceled")
            self.assertEqual(canceled_payload["task"]["error_message"], "任务在排队阶段被取消。")

            events_response = client.get(f"/tasks/{payload['task_id']}/events")
            self.assertEqual(events_response.status_code, 200)
            event_types = [item["event_type"] for item in events_response.json()["task_events"]]
            self.assertIn("queued", event_types)
            self.assertIn("canceled", event_types)

    def test_async_task_can_be_retried_after_cancel(self) -> None:
        from fastapi.testclient import TestClient

        def fake_submit(self, task_id: str, fn):
            future: Future[None] = Future()
            with self.lock:
                self.futures[task_id] = future
            future.add_done_callback(lambda _: self._cleanup(task_id))
            return future

        with patch("app.presentation.api.app.BackgroundTaskRunner.submit", new=fake_submit):
            client = TestClient(create_app())
            submit_response = client.post(
                "/tasks/submit",
                json={
                    "message": "帮我写一句简短的自我介绍",
                    "user_name": "retry-user",
                    "session_title": "Retry Session",
                },
            )
            self.assertEqual(submit_response.status_code, 200)
            payload = submit_response.json()

            cancel_response = client.post(f"/tasks/{payload['task_id']}/cancel")
            self.assertEqual(cancel_response.status_code, 200)

            retry_response = client.post(f"/tasks/{payload['task_id']}/retry")
            self.assertEqual(retry_response.status_code, 200)
            retry_payload = retry_response.json()
            self.assertEqual(retry_payload["session_id"], payload["session_id"])
            self.assertEqual(retry_payload["status"], "queued")
            self.assertNotEqual(retry_payload["task_id"], payload["task_id"])

            retried_task_response = client.get(f"/tasks/{retry_payload['task_id']}")
            self.assertEqual(retried_task_response.status_code, 200)
            retried_task = retried_task_response.json()["task"]
            self.assertEqual(retried_task["status"], "queued")

            retried_events_response = client.get(f"/tasks/{retry_payload['task_id']}/events")
            self.assertEqual(retried_events_response.status_code, 200)
            retried_event_types = [item["event_type"] for item in retried_events_response.json()["task_events"]]
            self.assertIn("queued", retried_event_types)

    def test_task_not_found_returns_structured_error(self) -> None:
        response = self.client.get("/tasks/task_not_exist")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["category"], "validation")
        self.assertEqual(payload["code"], "validation_error")
        self.assertEqual(payload["message"], "任务不存在。")

    def test_failed_chat_persists_failed_task_and_returns_structured_error(self) -> None:
        with patch("app.presentation.api.app.build_graph") as mock_build_graph:
            class FailingGraph:
                def invoke(self, _: dict[str, object]) -> dict[str, object]:
                    raise AgentError("system", "unexpected_error", "mock graph failure")

            mock_build_graph.return_value = FailingGraph()

            from fastapi.testclient import TestClient

            failing_client = TestClient(create_app())
            response = failing_client.post(
                "/chat",
                json={
                    "message": "请处理失败场景",
                    "user_name": "api-test-user",
                    "session_title": "Failed API Session",
                },
            )

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertEqual(payload["category"], "system")
        self.assertEqual(payload["code"], "unexpected_error")
        self.assertEqual(payload["message"], "mock graph failure")
        self.assertTrue(payload["trace_id"])

        sessions_response = self.client.get("/sessions")
        sessions_payload = sessions_response.json()
        failed_session_id = sessions_payload["sessions"][0]["id"]

        session_tasks_response = self.client.get(f"/sessions/{failed_session_id}/tasks")
        session_tasks_payload = session_tasks_response.json()
        self.assertGreaterEqual(len(session_tasks_payload["tasks"]), 1)
        self.assertEqual(session_tasks_payload["tasks"][0]["task"]["status"], "failed")
        self.assertEqual(session_tasks_payload["tasks"][0]["task"]["error_message"], "mock graph failure")

        failed_tasks_response = self.client.get("/tasks?status=failed")
        self.assertEqual(failed_tasks_response.status_code, 200)
        failed_tasks_payload = failed_tasks_response.json()
        self.assertGreaterEqual(len(failed_tasks_payload["tasks"]), 1)
        self.assertEqual(failed_tasks_payload["tasks"][0]["task"]["status"], "failed")

    def test_analyze_asset_can_preview_tool_execution(self) -> None:
        with patch("app.presentation.api.app.parse_input_assets") as mock_parse_input_assets, patch(
            "app.presentation.api.app.tool_node"
        ) as mock_tool_node:
            mock_parse_input_assets.return_value = (
                "请分析图片",
                [
                    {
                        "kind": "image",
                        "name": "demo.png",
                        "content": "preview image",
                        "source": "test",
                        "storage_mode": "local_path",
                        "local_path": "D:/fake/demo.png",
                    }
                ],
            )

            def fake_tool_node(state: dict[str, object]) -> dict[str, object]:
                state["tool_results"] = [
                    {
                        "tool_name": "ocr_tesseract",
                        "trace_id": state["trace_id"],
                        "success": True,
                        "exit_code": 0,
                        "stdout": "HELLO 123",
                        "stderr": "",
                    }
                ]
                state["task_state"] = "ocr_tesseract: 成功；摘要：HELLO 123"
                return state

            mock_tool_node.side_effect = fake_tool_node
            response = self.client.post(
                "/assets/analyze",
                json={
                    "input": "/image-file D:/fake/demo.png | 请分析图片",
                    "run_tools": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["user_input"], "请分析图片")
        self.assertEqual(payload["route_name"], "image_analysis")
        self.assertTrue(payload["route_reason"])
        self.assertEqual(payload["tool_results"][0]["tool_name"], "ocr_tesseract")
        self.assertIn("python_echo", payload["available_tools"])
        self.assertIn("HELLO 123", payload["task_state"])

    def test_upload_asset_uses_configured_directory(self) -> None:
        response = self.client.post(
            "/assets/upload",
            files={"file": ("note.txt", b"hello upload", "text/plain")},
            data={"kind": "file", "prompt": "请总结文档", "run_tools": "false"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["session_id"])
        self.assertTrue(payload["turn_id"])
        self.assertTrue(payload["task_id"])
        self.assertTrue(payload["trace_id"])
        self.assertEqual(payload["inferred_kind"], "file")
        self.assertEqual(payload["user_input"], "请总结文档")
        self.assertEqual(payload["route_name"], "document_analysis")
        self.assertTrue(payload["route_reason"])
        self.assertEqual(payload["upload_dir"], str(self.upload_path))
        self.assertTrue(payload["saved_path"].startswith(str(self.upload_path)))
        self.assertTrue(Path(payload["saved_path"]).exists())
        self.assertEqual(payload["input_assets"][0]["storage_mode"], "local_path")

        task_response = self.client.get(f"/tasks/{payload['task_id']}")
        self.assertEqual(task_response.status_code, 200)
        task_payload = task_response.json()
        self.assertEqual(task_payload["task"]["session_id"], payload["session_id"])

        assets_response = self.client.get(f"/sessions/{payload['session_id']}/assets")
        self.assertEqual(assets_response.status_code, 200)
        assets_payload = assets_response.json()
        self.assertGreaterEqual(len(assets_payload["assets"]), 1)

        asset_id = assets_payload["assets"][0]["id"]
        single_asset_response = self.client.get(f"/assets/{asset_id}")
        self.assertEqual(single_asset_response.status_code, 200)
        single_asset_payload = single_asset_response.json()
        self.assertEqual(single_asset_payload["asset"]["id"], asset_id)

    def test_upload_image_can_preview_tools(self) -> None:
        with patch("app.presentation.api.app.tool_node") as mock_tool_node:
            def fake_tool_node(state: dict[str, object]) -> dict[str, object]:
                local_path = state["input_assets"][0]["local_path"]
                state["tool_results"] = [
                    {
                        "tool_name": "ocr_tesseract",
                        "trace_id": state["trace_id"],
                        "success": True,
                        "exit_code": 0,
                        "stdout": f"OCR from {local_path}",
                        "stderr": "",
                    }
                ]
                state["task_state"] = f"ocr_tesseract: 成功；摘要：OCR from {local_path}"
                return state

            mock_tool_node.side_effect = fake_tool_node
            response = self.client.post(
                "/assets/upload",
                files={"file": ("demo.png", base64.b64decode(PNG_1X1_BASE64), "image/png")},
                data={"run_tools": "true"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["inferred_kind"], "image")
        self.assertEqual(payload["route_name"], "image_analysis")
        self.assertEqual(payload["tool_results"][0]["tool_name"], "ocr_tesseract")
        self.assertIn(str(self.upload_path), payload["saved_path"])
        self.assertIn(payload["saved_path"], payload["tool_results"][0]["stdout"])

    def test_upload_asset_rejects_disallowed_kind(self) -> None:
        os.environ["APP_UPLOAD_ALLOWED_KINDS"] = "image"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.post(
            "/assets/upload",
            files={"file": ("note.txt", b"hello upload", "text/plain")},
            data={"kind": "file"},
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], "validation_error")
        self.assertEqual(payload["message"], "上传文件类型不在允许范围内。")
        os.environ.pop("APP_UPLOAD_ALLOWED_KINDS", None)

    def test_auth_middleware_rejects_missing_credentials(self) -> None:
        os.environ["APP_AUTH_ENABLED"] = "true"
        os.environ["APP_API_KEYS"] = "demo-key"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.get("/tools")
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertEqual(payload["category"], "auth")
        self.assertEqual(payload["code"], "authentication_error")
        os.environ.pop("APP_AUTH_ENABLED", None)
        os.environ.pop("APP_API_KEYS", None)

    def test_auth_middleware_accepts_api_key(self) -> None:
        os.environ["APP_AUTH_ENABLED"] = "true"
        os.environ["APP_API_KEYS"] = "demo-key"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.get("/tools", headers={"X-API-Key": "demo-key"})
        self.assertEqual(response.status_code, 200)
        trace_id = response.headers["X-Trace-Id"]
        trace_response = client.get(f"/traces/{trace_id}", headers={"X-API-Key": "demo-key"})
        self.assertEqual(trace_response.status_code, 200)
        self.assertEqual(trace_response.json()["trace"]["auth_type"], "api_key")
        os.environ.pop("APP_AUTH_ENABLED", None)
        os.environ.pop("APP_API_KEYS", None)

    def test_rate_limit_returns_structured_429(self) -> None:
        os.environ["APP_RATE_LIMIT_ENABLED"] = "true"
        os.environ["APP_RATE_LIMIT_REQUESTS"] = "1"
        os.environ["APP_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        first = client.get("/tools")
        second = client.get("/tools")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        payload = second.json()
        self.assertEqual(payload["category"], "rate_limit")
        self.assertEqual(payload["code"], "rate_limit_error")
        os.environ.pop("APP_RATE_LIMIT_ENABLED", None)
        os.environ.pop("APP_RATE_LIMIT_REQUESTS", None)
        os.environ.pop("APP_RATE_LIMIT_WINDOW_SECONDS", None)

    def test_idempotency_replays_post_response(self) -> None:
        os.environ["APP_IDEMPOTENCY_ENABLED"] = "true"
        os.environ["APP_IDEMPOTENCY_TTL_SECONDS"] = "300"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        headers = {"Idempotency-Key": "same-request-key"}
        first = client.post("/tools/python_echo/execute", headers=headers, json={"parameters": {"message": "hello"}})
        second = client.post("/tools/python_echo/execute", headers=headers, json={"parameters": {"message": "hello"}})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.headers["X-Idempotent-Replay"], "false")
        self.assertEqual(second.headers["X-Idempotent-Replay"], "true")
        os.environ.pop("APP_IDEMPOTENCY_ENABLED", None)
        os.environ.pop("APP_IDEMPOTENCY_TTL_SECONDS", None)

    def test_rbac_admin_can_query_and_assign_roles(self) -> None:
        os.environ["APP_AUTH_ENABLED"] = "true"
        os.environ["APP_RBAC_ENABLED"] = "true"
        os.environ["APP_API_KEYS"] = "demo-key,viewer-key"
        os.environ["APP_AUTH_ADMIN_SUBJECTS"] = "apikey:demo-key"
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        admin_headers = {"X-API-Key": "demo-key"}

        me_response = client.get("/auth/me", headers=admin_headers)
        self.assertEqual(me_response.status_code, 200)
        profile = me_response.json()["profile"]
        self.assertIn("admin", profile["roles"])
        self.assertIn("config.write", profile["permissions"])

        roles_response = client.get("/auth/roles", headers=admin_headers)
        self.assertEqual(roles_response.status_code, 200)
        roles_payload = roles_response.json()
        self.assertGreaterEqual(len(roles_payload["roles"]), 3)
        self.assertGreaterEqual(len(roles_payload["permissions"]), 10)

        assign_response = client.put(
            "/auth/subjects/apikey:viewer-k/roles",
            headers=admin_headers,
            json={"role_keys": ["viewer"], "updated_by": "admin-test"},
        )
        self.assertEqual(assign_response.status_code, 200)
        assign_payload = assign_response.json()
        self.assertEqual(assign_payload["role_keys"], ["viewer"])

        viewer_response = client.get("/auth/me", headers={"X-API-Key": "viewer-key"})
        self.assertEqual(viewer_response.status_code, 200)
        viewer_profile = viewer_response.json()["profile"]
        self.assertEqual(viewer_profile["roles"], ["viewer"])
        self.assertIn("task.read", viewer_profile["permissions"])
        self.assertNotIn("config.write", viewer_profile["permissions"])

        forbidden_response = client.put(
            "/config/runtime",
            headers={"X-API-Key": "viewer-key"},
            json={
                "config_scope": "workflow",
                "config_key": "execution_mode",
                "config_value": "standard",
                "value_type": "str",
                "description": "forbidden",
                "updated_by": "viewer",
            },
        )
        self.assertEqual(forbidden_response.status_code, 403)
        forbidden_payload = forbidden_response.json()
        self.assertEqual(forbidden_payload["code"], "authorization_error")

        for name in ["APP_AUTH_ENABLED", "APP_RBAC_ENABLED", "APP_API_KEYS", "APP_AUTH_ADMIN_SUBJECTS"]:
            os.environ.pop(name, None)
