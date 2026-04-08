"""
Tool registry tests.

What this is:
- Unit tests for the stage-2 tool gateway and local runner.

What it does:
- Verifies tool registration, whitelist behavior, retries, circuit breaking,
  and alert persistence for tool failures.

Why this is done this way:
- Tool execution is part of the runtime contract. Once alerts are added to the
  recovery flow, failures need to be observable as well as recoverable.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.domain.errors import ToolError
from app.infrastructure.alert import get_alert_service
from app.infrastructure.tools.failure_recovery import reset_circuit_breakers
from app.infrastructure.tools.local_runner import LocalToolRunner
from app.infrastructure.tools.registry import ToolRegistry, build_default_tool_registry


class ToolRegistryTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_alert_service.cache_clear()
        reset_circuit_breakers()

    def test_default_registry_can_execute_tool(self) -> None:
        registry = build_default_tool_registry()
        result = registry.execute("python_echo", "trace_test", {"message": "hello"})
        self.assertTrue(result["success"])
        self.assertEqual(result["stdout"], "hello")
        self.assertEqual(result["tool_name"], "python_echo")

    def test_execute_unknown_tool_raises_tool_error(self) -> None:
        registry = ToolRegistry()
        with self.assertRaises(ToolError):
            registry.execute("missing_tool", "trace_test")

    def test_registry_registers_real_tool_when_env_points_to_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "fake_ocr.cmd"
            script_path.write_text("@echo off\r\necho OCR READY\r\n", encoding="utf-8")

            with patch.dict(os.environ, {"OCR_TOOL_PATH": str(script_path)}, clear=False):
                registry = build_default_tool_registry()

            self.assertIn("ocr_tesseract", registry.list_tool_names())

    def test_registry_can_be_built_without_real_tools(self) -> None:
        cleared_env = dict(os.environ)
        cleared_env.pop("OCR_TOOL_PATH", None)
        cleared_env.pop("ASR_TOOL_PATH", None)
        cleared_env.pop("VIDEO_PROBE_TOOL_PATH", None)
        cleared_env.pop("VIDEO_FRAME_TOOL_PATH", None)
        cleared_env.pop("APP_ALLOWED_TOOLS", None)

        with patch.dict(os.environ, cleared_env, clear=True):
            registry = build_default_tool_registry()

        self.assertIn("python_echo", registry.list_tool_names())

    def test_registry_respects_allowed_tools_whitelist(self) -> None:
        with patch.dict(os.environ, {"APP_ALLOWED_TOOLS": "python_echo"}, clear=False):
            registry = build_default_tool_registry()
        self.assertEqual(registry.list_tool_names(), ["python_echo"])

    def test_local_runner_retries_transient_os_error(self) -> None:
        runner = LocalToolRunner()
        completed_process = type("CompletedProcessLike", (), {"returncode": 0, "stdout": "ok\n", "stderr": ""})()

        with patch("app.infrastructure.tools.local_runner.is_tool_retry_enabled", return_value=True), patch(
            "app.infrastructure.tools.local_runner.get_tool_retry_attempts",
            return_value=2,
        ), patch(
            "app.infrastructure.tools.local_runner.get_tool_retry_backoff_ms",
            return_value=0,
        ), patch(
            "app.infrastructure.tools.local_runner.subprocess.run",
            side_effect=[OSError("temporary"), completed_process],
        ):
            result = runner.run(["fake-tool"], trace_id="trace_test")

        self.assertTrue(result["success"])
        self.assertEqual(result["stdout"], "ok")

    def test_local_runner_does_not_retry_disabled_mode(self) -> None:
        runner = LocalToolRunner()
        with patch("app.infrastructure.tools.local_runner.is_tool_retry_enabled", return_value=False), patch(
            "app.infrastructure.tools.local_runner.subprocess.run",
            side_effect=OSError("permanent"),
        ):
            with self.assertRaises(ToolError):
                runner.run(["fake-tool"], trace_id="trace_test")

    def test_local_runner_opens_circuit_after_transient_failures(self) -> None:
        runner = LocalToolRunner()
        with patch("app.infrastructure.tools.local_runner.is_tool_retry_enabled", return_value=False), patch(
            "app.infrastructure.tools.local_runner.is_tool_circuit_enabled",
            return_value=True,
        ), patch(
            "app.infrastructure.tools.local_runner.get_tool_circuit_failure_threshold",
            return_value=1,
        ), patch(
            "app.infrastructure.tools.local_runner.get_tool_circuit_recovery_seconds",
            return_value=30,
        ), patch(
            "app.infrastructure.tools.local_runner.subprocess.run",
            side_effect=OSError("temporary"),
        ):
            with self.assertRaises(ToolError):
                runner.run(["fake-tool"], trace_id="trace_test")

            with self.assertRaises(ToolError) as second_error:
                runner.run(["fake-tool"], trace_id="trace_test")

        self.assertIn("熔断已开启", str(second_error.exception))
        alerts = get_alert_service().list_alerts(source_type="tool")
        self.assertGreaterEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["source_type"], "tool")
