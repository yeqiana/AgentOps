"""
Prompt 编排层测试。

这是什么：
- 这是 `app.application.prompt_builder` 的自动化测试文件。

做什么：
- 验证多模态模板是否被正确注入。
- 验证规划和执行 Prompt 是否包含核心底座信息。

为什么这么做：
- Prompt 是 Agent 底座最重要的业务资产之一。
- 对 Prompt 编排做基础测试，可以避免重构时把关键上下文拼装丢掉。
"""

import unittest

from app.application.agent_service import create_initial_state
from app.application.prompt_builder import build_answer_prompt, build_plan_prompt


class PromptBuilderTests(unittest.TestCase):
    """
    Prompt 编排测试用例。

    这是什么：
    - 这是 `unittest.TestCase` 子类。

    做什么：
    - 检查 Prompt 关键片段是否存在。

    为什么这么做：
    - Prompt 很难做精确输出测试，但至少可以验证底座信息和模态信息没有被漏掉。
    """

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

        self.assertIn("当前轮规划结果", prompt)
        self.assertIn("先识别关键信息，再给出简明总结。", prompt)
        self.assertIn("[文件输入]", prompt)

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


if __name__ == "__main__":
    unittest.main()
