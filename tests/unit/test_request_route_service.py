"""
请求路由服务测试。

这是什么：
- `RequestRouteService` 的单元测试文件。

做什么：
- 验证入口路由服务可以基于输入资产和文本生成稳定路由决策。

为什么这么做：
- 请求路由中台最小版首先要保证路由决策可以脱离 workflow 节点独立复用。
"""

import unittest
import os
import shutil
import uuid
from pathlib import Path

from app.application.services.config_service import RuntimeConfigService
from app.application.services.request_route_service import RequestRouteService


class RequestRouteServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path.cwd() / ".tmp-tests" / f"request-route-{uuid.uuid4().hex}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        database_path = self.temp_dir / "agent.db"
        os.environ["APP_DATABASE_URL"] = f"sqlite:///{database_path}"

    def tearDown(self) -> None:
        os.environ.pop("APP_DATABASE_URL", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_decide_returns_image_analysis_for_image_asset(self) -> None:
        service = RequestRouteService()

        decision = service.decide(
            user_input="请分析这张图片",
            input_assets=[
                {
                    "kind": "image",
                    "name": "demo.png",
                    "content": "图片摘要",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ],
        )

        self.assertEqual(decision["route_name"], "image_analysis")
        self.assertIn("图片", decision["route_reason"])

    def test_decide_returns_deliberation_route_for_compare_prompt(self) -> None:
        service = RequestRouteService()

        decision = service.decide(
            user_input="请比较两个方案的优缺点并给出建议",
            input_assets=[
                {
                    "kind": "text",
                    "name": "text_input",
                    "content": "请比较两个方案的优缺点并给出建议",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ],
        )

        self.assertEqual(decision["route_name"], "deliberation_chat")
        self.assertIn("比较", decision["route_reason"])

    def test_decide_returns_semantic_route_for_decision_prompt(self) -> None:
        service = RequestRouteService()

        decision = service.decide(
            user_input="模型网关自研还是采购云服务，哪个更合适",
            input_assets=[
                {
                    "kind": "text",
                    "name": "text_input",
                    "content": "模型网关自研还是采购云服务，哪个更合适",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ],
        )

        self.assertEqual(decision["route_name"], "deliberation_chat")
        self.assertIn("语义意图", decision["route_reason"])

    def test_decide_uses_database_backed_routing_override(self) -> None:
        config_service = RuntimeConfigService()
        config_service.upsert_config(
            scope="routing",
            key="image_route_name",
            value="custom_image_flow",
            value_type="str",
            description="route override",
            updated_by="tester",
        )
        config_service.upsert_config(
            scope="routing",
            key="image_route_reason",
            value="命中数据库配置的图片路由。",
            value_type="str",
            description="route override",
            updated_by="tester",
        )

        service = RequestRouteService(config_service)
        decision = service.decide(
            user_input="请分析这张图片",
            input_assets=[
                {
                    "kind": "image",
                    "name": "demo.png",
                    "content": "图片摘要",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ],
        )

        self.assertEqual(decision["route_name"], "custom_image_flow")
        self.assertEqual(decision["route_reason"], "命中数据库配置的图片路由。")
