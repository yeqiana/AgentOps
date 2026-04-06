"""
API 工厂测试。
这是什么：
- 这是阶段 1 API 入口的单元测试文件。
做什么：
- 验证 API 工厂可以正常创建应用。
为什么这么做：
- 一旦切到 schema 化协议，最先要保证工厂本身稳定可导入。
"""

import unittest

from app.presentation.api.app import create_app


class ApiAppTests(unittest.TestCase):
    """
    API 工厂测试用例。
    这是什么：
    - `unittest.TestCase` 子类。
    做什么：
    - 验证 create_app 正常返回 FastAPI 应用。
    为什么这么做：
    - 这能尽早发现 API 入口级别的导入或依赖问题。
    """

    def test_create_app_returns_application(self) -> None:
        app = create_app()
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, "routes"))
