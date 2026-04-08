"""
Prompt builder tests.

What this is:
- Unit tests for prompt composition.

What it does:
- Verifies multimodal context, plan context, and registered role context are
  injected into prompts.

Why this is done this way:
- Prompt composition is critical runtime behavior. Small regressions here can
  silently break orchestration quality.
"""

from __future__ import annotations

import unittest

from app.application.agent_service import create_initial_state
from app.application.prompt_builder import (
    build_answer_prompt,
    build_arbitration_prompt,
    build_critic_prompt,
    build_debate_prompt,
    build_plan_prompt,
)


class PromptBuilderTests(unittest.TestCase):
    def test_plan_prompt_contains_runtime_context_and_video_asset(self) -> None:
        state = create_initial_state()
        state["user_input"] = "帮我分析这个视频摘要"
        state["input_assets"] = [
            {
                "kind": "video",
                "name": "video_asset",
                "content": "这是一个产品演示视频摘要",
                "source": "test",
                "storage_mode": "inline_text",
            }
        ]
        prompt = build_plan_prompt(state)

        self.assertIn("通用 Agent 底座运行时", prompt)
        self.assertIn("[视频输入]", prompt)
        self.assertIn("帮我分析这个视频摘要", prompt)

    def test_answer_prompt_contains_plan_and_file_asset(self) -> None:
        state = create_initial_state()
        state["user_input"] = "帮我总结内容"
        state["plan"] = "先识别关键信息，再给出简明总结。"
        state["route_name"] = "document_analysis"
        state["route_reason"] = "检测到文档输入。"
        state["debate_summary"] = "当前路由未启用多 Agent 辩论。"
        state["arbitration_summary"] = "当前路由未启用仲裁。"
        state["review_status"] = "approved"
        state["review_summary"] = "结果可交付。"
        state["input_assets"] = [
            {
                "kind": "file",
                "name": "file_asset",
                "content": "这是一个文档摘要",
                "source": "test",
                "storage_mode": "inline_text",
            }
        ]
        prompt = build_answer_prompt(state)

        self.assertIn("当前轮规划结果：", prompt)
        self.assertIn("先识别关键信息，再给出简明总结。", prompt)
        self.assertIn("[文件输入]", prompt)
        self.assertIn("当前复核状态：approved", prompt)

    def test_critic_prompt_contains_answer_route_and_role(self) -> None:
        state = create_initial_state()
        state["user_input"] = "请分析这个方案"
        state["route_name"] = "deliberation_chat"
        state["route_reason"] = "检测到比较或评审型任务。"
        state["plan"] = "先梳理方案，再指出优缺点。"
        state["answer"] = "这是当前方案的总结。"

        prompt = build_critic_prompt(
            state,
            role_name="质量批评代理",
            stance_instruction="优先指出方案说明中的遗漏与风险。",
        )

        self.assertIn("当前路由决策：deliberation_chat", prompt)
        self.assertIn("当前最终答案：", prompt)
        self.assertIn("这是当前方案的总结。", prompt)
        self.assertIn("当前批评角色：质量批评代理", prompt)

    def test_debate_and_arbitration_prompts_contain_role_context(self) -> None:
        state = create_initial_state()
        state["user_input"] = "请比较两个方案的优缺点并给出建议"
        state["route_name"] = "deliberation_chat"
        state["route_reason"] = "检测到比较或评审型任务。"
        state["plan"] = "先梳理两个方案，再比较优缺点。"
        state["debate_summary"] = "支持方代理：方案 A 更稳。\n质疑方代理：方案 B 成本更低。"

        debate_prompt = build_debate_prompt(
            state,
            role_name="支持方代理",
            stance_instruction="优先指出当前规划与最终回答应保留的强项和有效路径。",
        )
        arbitration_prompt = build_arbitration_prompt(
            state,
            role_name="仲裁代理",
            stance_instruction="优先整合双方观点。",
        )

        self.assertIn("当前角色是：支持方代理", debate_prompt)
        self.assertIn("先梳理两个方案，再比较优缺点。", debate_prompt)
        self.assertIn("当前辩论摘要：", arbitration_prompt)
        self.assertIn("方案 A 更稳", arbitration_prompt)
        self.assertIn("当前仲裁角色：仲裁代理", arbitration_prompt)

    def test_plan_prompt_contains_real_image_metadata(self) -> None:
        state = create_initial_state()
        state["user_input"] = "请分析这张图片"
        state["input_assets"] = [
            {
                "kind": "image",
                "name": "tiny.png",
                "content": "图片名称：tiny.png；来源：本地文件 D:/tmp/tiny.png；MIME：image/png；大小：68 字节。",
                "source": "local_path",
                "storage_mode": "local_path",
                "mime_type": "image/png",
                "local_path": "D:/tmp/tiny.png",
                "locator": "D:/tmp/tiny.png",
            }
        ]
        prompt = build_plan_prompt(state)

        self.assertIn("[图片输入]", prompt)
        self.assertIn("存储方式：local_path", prompt)
        self.assertIn("MIME：image/png", prompt)
        self.assertIn("D:/tmp/tiny.png", prompt)
