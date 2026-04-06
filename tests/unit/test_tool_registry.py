"""
工具网关测试。
这是什么：
- 这是阶段 1 工具网关的单元测试文件。
做什么：
- 验证工具注册、执行和环境发现逻辑。
为什么这么做：
- 如果工具网关一开始就不稳定，后面再接 OCR、ASR 和视频处理时会更难排障。
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.domain.errors import ToolError
from app.infrastructure.tools.registry import ToolRegistry, build_default_tool_registry


class ToolRegistryTests(unittest.TestCase):
    """
    工具网关测试用例。
    这是什么：
    - `unittest.TestCase` 子类。
    做什么：
    - 组织工具注册和执行相关断言。
    为什么这么做：
    - 当前阶段只做最小工具网关，所以更要验证这个最小闭环真的可用。
    """

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

        with patch.dict(os.environ, cleared_env, clear=True):
            registry = build_default_tool_registry()

        self.assertIn("python_echo", registry.list_tool_names())
