"""
请求路由服务。

这是什么：
- 应用层的最小请求路由服务。

做什么：
- 基于输入、资产、工具结果和上下文生成统一路由决策。
- 将路由决策写回共享状态，供入口层和工作流层复用。

为什么这么做：
- 请求路由不应只内聚在 workflow 节点里。
- 先抽出最小独立服务，后续才能平滑演进为请求路由中台。
"""

from __future__ import annotations

from app.application.services.config_service import RuntimeConfigService
from app.domain.models import AgentState, InputAsset
from app.infrastructure.llm.client import sanitize_text
class RouteDecision(dict):
    """
    请求路由决策对象。

    这是什么：
    - 路由服务输出的最小结构化结果。

    做什么：
    - 保存路由名称、路由原因和决策来源。

    为什么这么做：
    - 明确路由输出格式，避免入口层和工作流层继续传裸元组。
    """

    route_name: str
    route_reason: str
    route_source: str


class RequestRouteService:
    """
    请求路由服务。

    这是什么：
    - 应用层的统一路由决策服务。

    做什么：
    - 对入口请求和工作流状态生成统一路由决策。

    为什么这么做：
    - 最小路由中台的第一步应先把路由逻辑从 workflow 节点中抽成可复用服务。
    """

    def __init__(self, config_service: RuntimeConfigService | None = None) -> None:
        self.config_service = config_service or RuntimeConfigService()

    def decide(
        self,
        *,
        user_input: str,
        input_assets: list[InputAsset],
        tool_results: list[dict[str, object]] | None = None,
        message_count: int = 0,
        route_source: str = "request_entry",
    ) -> RouteDecision:
        cleaned_input = sanitize_text(user_input).lower()
        asset_kinds = {str(asset["kind"]) for asset in input_assets}
        effective_config = self.config_service.get_effective_routing_config()

        if "video" in asset_kinds:
            route_name = effective_config["video_route_name"]
            route_reason = effective_config["video_route_reason"]
        elif "audio" in asset_kinds:
            route_name = effective_config["audio_route_name"]
            route_reason = effective_config["audio_route_reason"]
        elif "file" in asset_kinds:
            route_name = effective_config["file_route_name"]
            route_reason = effective_config["file_route_reason"]
        elif "image" in asset_kinds:
            route_name = effective_config["image_route_name"]
            route_reason = effective_config["image_route_reason"]
        elif tool_results:
            route_name = effective_config["tool_augmented_route_name"]
            route_reason = effective_config["tool_augmented_route_reason"]
        elif effective_config["deliberation_enabled"] and any(
            keyword.lower() in cleaned_input for keyword in effective_config["deliberation_keywords"]
        ):
            route_name = effective_config["deliberation_route_name"]
            route_reason = effective_config["deliberation_route_reason"]
        elif message_count >= effective_config["contextual_message_threshold"]:
            route_name = effective_config["contextual_route_name"]
            route_reason = effective_config["contextual_route_reason"]
        else:
            route_name = effective_config["default_route_name"]
            route_reason = effective_config["default_route_reason"]

        return RouteDecision(
            route_name=route_name,
            route_reason=route_reason,
            route_source=sanitize_text(route_source) or "request_entry",
        )

    def decide_for_state(
        self,
        state: AgentState,
        *,
        route_source: str = "workflow_router",
    ) -> RouteDecision:
        return self.decide(
            user_input=state["user_input"],
            input_assets=state["input_assets"],
            tool_results=state["tool_results"],
            message_count=len(state["messages"]),
            route_source=route_source,
        )

    def apply_to_state(
        self,
        state: AgentState,
        *,
        route_source: str = "request_entry",
    ) -> AgentState:
        decision = self.decide_for_state(state, route_source=route_source)
        return {
            **state,
            "route_name": decision["route_name"],
            "route_reason": decision["route_reason"],
            "route_source": decision["route_source"],
        }
