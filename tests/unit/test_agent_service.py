"""
应用服务层测试。

这是什么：
- 这是 `app.application.agent_service` 的自动化测试文件。

做什么：
- 验证初始状态创建。
- 验证用户消息追加。
- 验证文本、模拟多模态和真实图片输入解析。

为什么这么做：
- 输入解析和状态初始化是 Agent 底座最基础的行为之一。
- 先把这些纯函数逻辑测稳，后面重构其他层时更不容易引入回归。
"""

import base64
import tempfile
import unittest
import wave
from io import BytesIO
from pathlib import Path

from app.application.agent_service import (
    append_user_message,
    create_initial_state,
    parse_input_assets,
)


SMALL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAgMBAp0XG6kAAAAASUVORK5CYII="
)


class AgentServiceTests(unittest.TestCase):
    """
    Agent 应用服务测试用例。

    这是什么：
    - 这是 `unittest.TestCase` 子类。

    做什么：
    - 组织应用服务层相关断言。

    为什么这么做：
    - `unittest` 是 Python 标准库自带能力，不需要额外引入测试依赖。
    """

    def test_create_initial_state_contains_runtime_context_and_assets(self) -> None:
        state = create_initial_state()
        self.assertIn("runtime_context", state)
        self.assertIn("input_assets", state)
        self.assertEqual(state["messages"], [])
        self.assertIn("video", state["runtime_context"]["input_modalities"])

    def test_append_user_message_appends_message(self) -> None:
        messages = append_user_message([], "你好")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "你好")

    def test_parse_plain_text_input(self) -> None:
        normalized_text, assets = parse_input_assets("帮我总结一下这段话")
        self.assertEqual(normalized_text, "帮我总结一下这段话")
        self.assertEqual(assets[0]["kind"], "text")

    def test_parse_simulated_image_input(self) -> None:
        normalized_text, assets = parse_input_assets("/image 这是一张产品海报")
        self.assertEqual(normalized_text, "这是一张产品海报")
        self.assertEqual(assets[0]["kind"], "image")
        self.assertEqual(assets[0]["storage_mode"], "inline_text")

    def test_parse_video_input(self) -> None:
        normalized_text, assets = parse_input_assets("/video 这是一个演示视频摘要")
        self.assertEqual(normalized_text, "这是一个演示视频摘要")
        self.assertEqual(assets[0]["kind"], "video")

    def test_parse_real_image_file_input(self) -> None:
        image_bytes = base64.b64decode(SMALL_PNG_BASE64)
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "tiny.png"
            image_path.write_bytes(image_bytes)

            normalized_text, assets = parse_input_assets(f"/image-file {image_path} | 请识别图片内容")

        self.assertEqual(normalized_text, "请识别图片内容")
        self.assertEqual(assets[0]["kind"], "image")
        self.assertEqual(assets[0]["storage_mode"], "local_path")
        self.assertEqual(assets[0]["mime_type"], "image/png")
        self.assertTrue(assets[0]["data_base64"])

    def test_parse_real_image_base64_input(self) -> None:
        normalized_text, assets = parse_input_assets(f"/image-base64 {SMALL_PNG_BASE64}")
        self.assertIn("请分析这张图片", normalized_text)
        self.assertEqual(assets[0]["kind"], "image")
        self.assertEqual(assets[0]["storage_mode"], "bytes")

    def test_parse_real_object_storage_input(self) -> None:
        normalized_text, assets = parse_input_assets("/image-object s3://demo-bucket/images/example.png")
        self.assertIn("请分析这张图片", normalized_text)
        self.assertEqual(assets[0]["kind"], "image")
        self.assertEqual(assets[0]["storage_mode"], "object_uri")
        self.assertEqual(assets[0]["locator"], "s3://demo-bucket/images/example.png")

    def test_parse_real_audio_file_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "tiny.wav"
            buffer = BytesIO()
            with wave.open(buffer, "wb") as wave_file:
                wave_file.setnchannels(1)
                wave_file.setsampwidth(2)
                wave_file.setframerate(8000)
                wave_file.writeframes(b"\x00\x00" * 800)
            audio_path.write_bytes(buffer.getvalue())

            normalized_text, assets = parse_input_assets(f"/audio-file {audio_path} | 请分析这个音频")

        self.assertEqual(normalized_text, "请分析这个音频")
        self.assertEqual(assets[0]["kind"], "audio")
        self.assertEqual(assets[0]["storage_mode"], "local_path")
        self.assertIn(assets[0]["mime_type"], {"audio/wav", "audio/x-wav"})

    def test_parse_real_file_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "note.txt"
            file_path.write_text("第一行\n第二行", encoding="utf-8")

            normalized_text, assets = parse_input_assets(f"/file-path {file_path}")

        self.assertIn("请阅读这个文件", normalized_text)
        self.assertEqual(assets[0]["kind"], "file")
        self.assertEqual(assets[0]["storage_mode"], "local_path")
        self.assertIn("第一行", assets[0]["content"])


if __name__ == "__main__":
    unittest.main()
