"""
持久化与会话服务测试。
这是什么：
- 这是阶段 1 持久化底座的集成测试文件。
做什么：
- 验证成功任务和失败任务都能被正确落库。
为什么这么做：
- 只测成功路径不够，底座是否可排障取决于失败路径是不是也能查到。
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.domain.errors import AgentError
from app.infrastructure.tools.registry import build_default_tool_registry


class PersistenceServiceTests(unittest.TestCase):
    """
    持久化与会话服务测试用例。
    这是什么：
    - `unittest.TestCase` 子类。
    做什么：
    - 组织数据库和会话服务相关断言。
    为什么这么做：
    - 这能覆盖“会话创建 -> 执行 -> 落库 -> 查询”的关键闭环。
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "agent.db"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"
        self.session_service = SessionService()
        self.task_service = TaskService(build_default_tool_registry())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_session_service_persists_messages_assets_and_task(self) -> None:
        state = self.session_service.create_state(user_name="integration-user", title="Integration Session")
        current_state = self.task_service.prepare_turn_state(
            state,
            "请总结这段文本",
            [
                {
                    "kind": "text",
                    "name": "text_input",
                    "content": "请总结这段文本",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ],
        )
        current_state["plan"] = "先理解任务，再总结文本。"
        current_state["answer"] = "这是总结结果。"
        current_state["route_name"] = "direct_chat"
        current_state["route_reason"] = "普通文本任务。"
        current_state["debate_summary"] = "当前路由未启用多 Agent 辩论。"
        current_state["arbitration_summary"] = "当前路由未启用仲裁。"
        current_state["critic_summary"] = "批评代理认为当前结果可交付。"
        current_state["review_status"] = "approved"
        current_state["review_summary"] = "结果可交付。"
        current_state["messages"] = [
            {"role": "user", "content": "请总结这段文本"},
            {"role": "assistant", "content": "这是总结结果。"},
        ]
        current_state["tool_results"] = [
            {
                "tool_name": "python_echo",
                "trace_id": current_state["trace_id"],
                "success": True,
                "exit_code": 0,
                "stdout": "tool output",
                "stderr": "",
            }
        ]

        self.session_service.persist_turn(current_state)
        bundle = self.session_service.get_session_bundle(current_state["session_id"])
        task = self.session_service.get_task(current_state["task_id"])

        self.assertIsNotNone(bundle["session"])
        self.assertEqual(len(bundle["messages"]), 2)
        self.assertEqual(len(bundle["assets"]), 1)
        self.assertEqual(bundle["messages"][0]["trace_id"], current_state["trace_id"])
        self.assertIsNotNone(task)
        self.assertEqual(task["task"]["id"], current_state["task_id"])
        self.assertEqual(task["task"]["status"], "completed")
        self.assertEqual(task["task"]["session_id"], current_state["session_id"])
        self.assertEqual(task["task"]["route_name"], "direct_chat")
        self.assertEqual(task["task"]["debate_summary"], "当前路由未启用多 Agent 辩论。")
        self.assertEqual(task["task"]["arbitration_summary"], "当前路由未启用仲裁。")
        self.assertEqual(task["task"]["critic_summary"], "批评代理认为当前结果可交付。")
        self.assertEqual(task["task"]["review_status"], "approved")
        self.assertEqual(len(task["task_events"]), 1)
        self.assertEqual(task["task_events"][0]["event_type"], "completed")
        self.assertEqual(len(task["tool_results"]), 1)
        self.assertEqual(task["tool_results"][0]["tool_name"], "python_echo")
        self.assertEqual(len(task["route_decisions"]), 1)
        self.assertEqual(task["route_decisions"][0]["route_name"], "direct_chat")

    def test_session_service_persists_failed_task(self) -> None:
        state = self.session_service.create_state(user_name="integration-user", title="Failed Session")
        current_state = self.task_service.prepare_turn_state(
            state,
            "请分析这张图片",
            [
                {
                    "kind": "image",
                    "name": "sample.png",
                    "content": "sample image",
                    "source": "test",
                    "storage_mode": "local_path",
                    "local_path": "D:/fake/sample.png",
                }
            ],
        )
        current_state["messages"] = [{"role": "user", "content": "请分析这张图片"}]
        current_state["route_name"] = "multimodal_analysis"
        current_state["route_reason"] = "检测到图片输入。"
        current_state["debate_summary"] = "当前路由未启用多 Agent 辩论。"
        current_state["arbitration_summary"] = "当前路由未启用仲裁。"
        current_state["critic_summary"] = "批评代理认为任务失败，需要人工处理。"
        current_state["review_status"] = "needs_attention"
        current_state["review_summary"] = "任务失败，需人工复核。"
        current_state["tool_results"] = [
            {
                "tool_name": "ocr_tesseract",
                "trace_id": current_state["trace_id"],
                "success": False,
                "exit_code": 1,
                "stdout": "",
                "stderr": "tool failed",
            }
        ]

        error = AgentError(
            "system",
            "unexpected_error",
            "graph invoke failed",
            trace_id=current_state["trace_id"],
        )

        self.session_service.persist_failed_turn(current_state, error)
        task = self.session_service.get_task(current_state["task_id"])
        bundle = self.session_service.get_session_bundle(current_state["session_id"])

        self.assertIsNotNone(task)
        self.assertEqual(task["task"]["status"], "failed")
        self.assertEqual(task["task"]["error_message"], "graph invoke failed")
        self.assertEqual(task["task"]["route_name"], "multimodal_analysis")
        self.assertEqual(task["task"]["debate_summary"], "当前路由未启用多 Agent 辩论。")
        self.assertEqual(task["task"]["arbitration_summary"], "当前路由未启用仲裁。")
        self.assertEqual(task["task"]["critic_summary"], "批评代理认为任务失败，需要人工处理。")
        self.assertEqual(task["task"]["review_status"], "needs_attention")
        self.assertEqual(len(task["task_events"]), 1)
        self.assertEqual(task["task_events"][0]["event_type"], "failed")
        self.assertEqual(len(task["tool_results"]), 1)
        self.assertEqual(task["tool_results"][0]["tool_name"], "ocr_tesseract")
        self.assertEqual(len(task["route_decisions"]), 1)
        self.assertEqual(task["route_decisions"][0]["route_name"], "multimodal_analysis")
        self.assertEqual(len(bundle["messages"]), 1)
        self.assertEqual(bundle["messages"][0]["role"], "user")
