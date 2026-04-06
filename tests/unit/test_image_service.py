"""
图片服务测试。

这是什么：
- 这是对真实图片入口的自动化测试文件。

做什么：
- 验证字节、流、本地路径和对象存储 URI 能被转换成统一图片资产。

为什么这么做：
- 真实图片入口是这次改造的核心能力，必须单独覆盖，避免以后重构把入口打断。
"""

import base64
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from app.application.image_service import (
    create_image_asset_from_binary,
    create_image_asset_from_reference,
    create_image_asset_from_stream,
)


SMALL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAgMBAp0XG6kAAAAASUVORK5CYII="
)


class ImageServiceTests(unittest.TestCase):
    """
    图片服务测试用例。

    这是什么：
    - 这是 `unittest.TestCase` 子类。

    做什么：
    - 检查不同图片入口是否都能产生统一的图片资产结构。

    为什么这么做：
    - 统一资产结构是多模态底座稳定工作的前提。
    """

    def test_create_image_asset_from_binary(self) -> None:
        image_bytes = base64.b64decode(SMALL_PNG_BASE64)
        user_prompt, asset = create_image_asset_from_binary(image_bytes, name="tiny.png")

        self.assertIn("请分析这张图片", user_prompt)
        self.assertEqual(asset["kind"], "image")
        self.assertEqual(asset["storage_mode"], "bytes")
        self.assertEqual(asset["mime_type"], "image/png")
        self.assertTrue(asset["data_base64"])

    def test_create_image_asset_from_stream(self) -> None:
        image_bytes = base64.b64decode(SMALL_PNG_BASE64)
        user_prompt, asset = create_image_asset_from_stream(BytesIO(image_bytes), name="tiny.png")

        self.assertIn("请分析这张图片", user_prompt)
        self.assertEqual(asset["kind"], "image")
        self.assertEqual(asset["storage_mode"], "bytes")

    def test_create_image_asset_from_local_path(self) -> None:
        image_bytes = base64.b64decode(SMALL_PNG_BASE64)
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "tiny.png"
            image_path.write_bytes(image_bytes)

            user_prompt, asset = create_image_asset_from_reference(str(image_path))

        self.assertIn("请分析这张图片", user_prompt)
        self.assertEqual(asset["kind"], "image")
        self.assertEqual(asset["storage_mode"], "local_path")
        self.assertTrue(asset["local_path"].endswith("tiny.png"))

    def test_create_image_asset_from_object_storage_uri(self) -> None:
        user_prompt, asset = create_image_asset_from_reference("oss://bucket/path/demo.png")

        self.assertIn("请分析这张图片", user_prompt)
        self.assertEqual(asset["kind"], "image")
        self.assertEqual(asset["storage_mode"], "object_uri")
        self.assertEqual(asset["locator"], "oss://bucket/path/demo.png")


if __name__ == "__main__":
    unittest.main()
