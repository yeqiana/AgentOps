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

from app.domain.errors import AgentError
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
        self.temp_dir.cleanup()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

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
