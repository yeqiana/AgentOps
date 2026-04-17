"""
Streaming chat Markdown tests.

What this is:
- Regression coverage for preserving Markdown text during streaming aggregation.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.application.services.chat_service import ChatService


class ChatServiceStreamingTests(unittest.TestCase):
    def test_stream_turn_events_keeps_final_answer_newlines_verbatim(self) -> None:
        markdown = (
            "# 标题\n\n"
            "## 小节\n\n"
            "* 项目 A\n"
            "* 项目 B\n\n"
            "```js\n"
            'console.log("hello")\n'
            "```\n\n"
            "| 字段 | 内容 |\n"
            "| -- | -- |\n"
            "| 名称 | 示例 |"
        )
        chunks = ["# 标题", "\n\n", "## 小节\n\n", "* 项目 A\n* 项目 B\n\n", "```js\n", 'console.log("hello")\n', "```\n\n", "| 字段 | 内容 |\n| -- | -- |\n| 名称 | 示例 |"]
        state = {
            "session_id": "session_test",
            "turn_id": "turn_test",
            "task_id": "task_test",
            "trace_id": "trace_test",
            "route_name": "default",
            "route_reason": "test",
            "execution_mode": "standard",
            "protocol_summary": "test",
            "output_format": "markdown",
            "input_assets": [],
            "messages": [],
        }

        def with_review(current_state):
            return {**current_state, "review_status": "passed", "review_summary": "ok"}

        service = ChatService.__new__(ChatService)
        registry = SimpleNamespace(
            executor_role=SimpleNamespace(name="executor", stance_instruction="answer"),
        )

        with patch("app.application.services.chat_service.tool_node", side_effect=lambda item: item), patch(
            "app.application.services.chat_service.router_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.protocol_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.plan_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.debate_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.arbitration_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.critic_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.review_node",
            side_effect=with_review,
        ), patch(
            "app.application.services.chat_service.build_workflow_policy_registry",
            return_value=registry,
        ), patch(
            "app.application.services.chat_service.build_answer_prompt",
            return_value="prompt",
        ), patch(
            "app.application.services.chat_service.stream_llm",
            return_value=iter(chunks),
        ):
            events = list(service.stream_turn_events(state))  # type: ignore[arg-type]

        delta_text = "".join(event["delta"] for event in events if event["type"] == "answer_delta")
        done_event = events[-1]

        self.assertEqual(delta_text, markdown)
        self.assertEqual(done_event["answer"], markdown)
        self.assertEqual(done_event["state"]["answer"], markdown)

    def test_stream_turn_events_repairs_compact_markdown_markers_in_final_answer(self) -> None:
        compact = "###量子计算通俗解释 传统电脑使用比特。###核心差异 1.叠加态 2.量子纠缠"
        state = {
            "session_id": "session_test",
            "turn_id": "turn_test",
            "task_id": "task_test",
            "trace_id": "trace_test",
            "route_name": "default",
            "route_reason": "test",
            "execution_mode": "standard",
            "protocol_summary": "test",
            "output_format": "markdown",
            "input_assets": [],
            "messages": [],
        }

        def with_review(current_state):
            return {**current_state, "review_status": "passed", "review_summary": "ok"}

        service = ChatService.__new__(ChatService)
        registry = SimpleNamespace(
            executor_role=SimpleNamespace(name="executor", stance_instruction="answer"),
        )

        with patch("app.application.services.chat_service.tool_node", side_effect=lambda item: item), patch(
            "app.application.services.chat_service.router_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.protocol_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.plan_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.debate_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.arbitration_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.critic_node",
            side_effect=lambda item: item,
        ), patch(
            "app.application.services.chat_service.review_node",
            side_effect=with_review,
        ), patch(
            "app.application.services.chat_service.build_workflow_policy_registry",
            return_value=registry,
        ), patch(
            "app.application.services.chat_service.build_answer_prompt",
            return_value="prompt",
        ), patch(
            "app.application.services.chat_service.stream_llm",
            return_value=iter([compact]),
        ):
            events = list(service.stream_turn_events(state))  # type: ignore[arg-type]

        answer = events[-1]["answer"]

        self.assertIn("### 量子计算通俗解释", answer)
        self.assertIn("\n\n### 核心差异", answer)
        self.assertIn("\n1. 叠加态", answer)
        self.assertIn("\n2. 量子纠缠", answer)


if __name__ == "__main__":
    unittest.main()
