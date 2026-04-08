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
import os
import tempfile
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
        self.assertEqual(task_payload["task"]["route_name"], payload["route_name"])
        self.assertEqual(task_payload["task"]["debate_summary"], payload["debate_summary"])
        self.assertEqual(task_payload["task"]["arbitration_summary"], payload["arbitration_summary"])
        self.assertEqual(task_payload["task"]["critic_summary"], payload["critic_summary"])
        self.assertEqual(task_payload["task"]["review_status"], payload["review_status"])
        self.assertIn("tool_results", task_payload)
        self.assertIsInstance(task_payload["tool_results"], list)

        tasks_response = self.client.get("/tasks?status=completed")
        self.assertEqual(tasks_response.status_code, 200)
        tasks_payload = tasks_response.json()
        self.assertGreaterEqual(len(tasks_payload["tasks"]), 1)
        self.assertEqual(tasks_payload["tasks"][0]["task"]["status"], "completed")

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
