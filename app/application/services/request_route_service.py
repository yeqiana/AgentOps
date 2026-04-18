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
from app.application.services.route_semantic_service import RouteSemanticService
from app.domain.models import AgentState, InputAsset
from app.infrastructure.llm.client import sanitize_text


class RouteDecision(dict):
    route_name: str
    route_reason: str
    route_source: str


class RequestRouteService:
    """
    请求路由服务。
    这是应用层的统一路由决策服务。
    对入口请求和工作流状态生成统一路由决策。
    最小路由中台的第一步应先把路由逻辑从 workflow 节点中抽成可复用服务。
    """
    def __init__(self, config_service: RuntimeConfigService | None = None) -> None:
        self.config_service = config_service or RuntimeConfigService()
        self.semantic_service = RouteSemanticService(self.config_service)

    def decide(
        self,
        *,
        user_input: str,
        input_assets: list[InputAsset],
        tool_results: list[dict[str, object]] | None = None,
        message_count: int = 0,
        route_source: str = "request_entry",
    ) -> RouteDecision:
        # 1. cleaned_input 把用户输入清洗、转小写，方便后续匹配
        cleaned_input = sanitize_text(user_input).lower()
        # 2. asset_kinds 看用户发了什么附件：图片 / 文件 / 音频 / 视频
        asset_kinds = {str(asset["kind"]) for asset in input_assets}
        # 3. 读取配置中心已存在的路由规则
        effective_config = self.config_service.get_effective_routing_config()
        # 4. 按优先级执行路由：资产 -> 工具结果 -> 语义 -> 关键词 -> 上下文 -> 默认
        # 4.1 视频、音频、文件、图片路由属于强规则，优先命中
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
        # 4.2 工具调用路由
        elif tool_results:
            route_name = effective_config["tool_augmented_route_name"]
            route_reason = effective_config["tool_augmented_route_reason"]
        # 4.3 语义路由补齐关键词之外的意图表达
        elif semantic_decision := self.semantic_service.decide(user_input=cleaned_input):
            route_name = semantic_decision["route_name"]
            route_reason = semantic_decision["route_reason"]
        # 4.4 深度思考关键词路由
        elif effective_config["deliberation_enabled"] and any(
            keyword.lower() in cleaned_input for keyword in effective_config["deliberation_keywords"]
        ):
            route_name = effective_config["deliberation_route_name"]
            route_reason = effective_config["deliberation_route_reason"]
        # 4.5 长上下文路由
        elif message_count >= effective_config["contextual_message_threshold"]:
            route_name = effective_config["contextual_route_name"]
            route_reason = effective_config["contextual_route_reason"]
        # 4.6 默认路由：普通问题走标准规划与回答链
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
        """
        基于 AgentState 生成路由决策。

        这是什么：
        - workflow 状态到路由决策的适配入口。

        做什么：
        - 从 state 中读取用户输入、输入资产、工具结果和消息数量。
        - 复用 `decide` 生成统一路由决策。

        为什么这么做：
        - workflow 层不应该重复入口层的路由判断逻辑。
        """
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
        """
        将路由决策写回状态。

        这是什么：
        - 路由服务到 AgentState 的写回入口。

        做什么：
        - 生成路由决策。
        - 把 route_name、route_reason 和 route_source 写回新状态。

        为什么这么做：
        - 保持状态不可变式更新，方便入口层和 workflow 层复用。
        """
        decision = self.decide_for_state(state, route_source=route_source)
        return {
            **state,
            "route_name": decision["route_name"],
            "route_reason": decision["route_reason"],
            "route_source": decision["route_source"],
        }
