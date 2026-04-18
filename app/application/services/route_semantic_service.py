"""
语义路由服务。

这是什么：
- 应用层的轻量语义路由服务。

做什么：
- 用 intent、example 和简单相似度判断用户输入是否应进入特定路由。
- 只返回已有路由体系中的 route_name 和 route_reason。

为什么这么做：
- 请求路由需要比关键词更柔和的判断能力，但当前阶段不需要引入 embedding 或额外模型调用。
- 先用可解释、低成本、可测试的轻量语义规则补齐最小能力。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.application.services.config_service import RuntimeConfigService
from app.infrastructure.llm.client import sanitize_text


@dataclass(frozen=True)
class SemanticIntent:
    """
    语义意图配置。

    这是什么：
    - 轻量语义路由使用的内部意图定义。

    做什么：
    - 保存意图名称、目标路由配置键、触发样例和核心提示词。

    为什么这么做：
    - intent 和 example 拆开后，后续扩展语义规则不会污染 `RequestRouteService` 主流程。
    """

    name: str
    route_name_key: str
    route_reason_key: str
    examples: tuple[str, ...]
    keywords: tuple[str, ...]
    threshold: float


class RouteSemanticService:
    """
    轻量语义路由服务。

    这是什么：
    - 介于强规则和关键词规则之间的一层语义判断。

    做什么：
    - 对用户输入和少量意图样例做相似度计算。
    - 命中时返回 route_name 和 route_reason。
    - 未命中时返回 None，让后续关键词、上下文和默认路由继续处理。

    为什么这么做：
    - 关键词只能处理显式词面，无法覆盖“怎么选”“是否值得做”这类同义表达。
    - 轻量相似度足以补齐常见语义路由，不增加模型依赖和运行成本。
    """

    def __init__(self, config_service: RuntimeConfigService | None = None) -> None:
        """
        初始化语义路由服务。

        这是什么：
        - 语义路由服务的构造入口。

        做什么：
        - 注入运行时配置服务。
        - 初始化轻量 intent 和 example 配置。

        为什么这么做：
        - 语义层只负责判断意图，最终 route_name 仍然来自配置中心。
        """
        self.config_service = config_service or RuntimeConfigService()
        self.intents = (
            SemanticIntent(
                name="deliberation",
                route_name_key="deliberation_route_name",
                route_reason_key="deliberation_route_reason",
                examples=(
                    "帮我评估两个技术方案哪个更合适",
                    "这个架构方案是否值得投入，请分析风险和收益",
                    "从成本、稳定性和维护难度权衡一下怎么选",
                    "请做一次方案评审并给出取舍建议",
                    "这个决策有哪些利弊和潜在风险",
                    "自研还是采购云服务，哪个更合适",
                ),
                keywords=(
                    "评估",
                    "权衡",
                    "取舍",
                    "利弊",
                    "风险",
                    "收益",
                    "是否值得",
                    "怎么选",
                    "更合适",
                    "应该选",
                    "方案",
                    "评审",
                ),
                threshold=0.20,
            ),
        )

    def decide(self, *, user_input: str) -> dict | None:
        """
        生成语义路由决策。

        这是什么：
        - 语义路由层的唯一公开入口。

        做什么：
        - 清洗输入。
        - 计算用户输入和每个 intent 示例的相似度。
        - 命中阈值后返回 route_name 和 route_reason。

        为什么这么做：
        - `RequestRouteService` 只需要知道是否命中语义路由，不需要理解相似度细节。
        """
        # 1. 清洗输入，空输入不参与语义路由
        cleaned_input = sanitize_text(user_input).lower()
        if not cleaned_input:
            return None

        # 2. 遍历 intent，选择相似度最高且超过阈值的候选
        effective_config = self.config_service.get_effective_routing_config()
        best_intent: SemanticIntent | None = None
        best_score = 0.0
        for intent in self.intents:
            score = self._score_intent(cleaned_input, intent)
            if score > best_score:
                best_intent = intent
                best_score = score

        # 3. 命中则复用配置中的 route；不命中返回 None，交给后续规则兜底
        if best_intent is None or best_score < best_intent.threshold:
            return None

        return {
            "route_name": str(effective_config[best_intent.route_name_key]),
            "route_reason": (
                f"{effective_config[best_intent.route_reason_key]}"
                f" 语义意图：{best_intent.name}，相似度：{best_score:.2f}。"
            ),
        }

    def _score_intent(self, cleaned_input: str, intent: SemanticIntent) -> float:
        """
        计算意图匹配分。

        这是什么：
        - intent 级别的简单相似度计算。

        做什么：
        - 对用户输入和每个 example 计算相似度。
        - 叠加少量关键词命中奖励。

        为什么这么做：
        - example 负责捕捉表达相似性，关键词负责提高核心意图的稳定性。
        """
        # 1. 用所有 example 的最高分代表当前 intent 的语义相似度
        example_score = max(self._similarity(cleaned_input, example.lower()) for example in intent.examples)

        # 2. 关键词只做轻量加分，避免退化成纯关键词匹配
        keyword_hits = sum(1 for keyword in intent.keywords if keyword in cleaned_input)
        keyword_score = min(keyword_hits * 0.06, 0.24)

        # 3. 返回限制到 1.0 以内的最终分数
        return min(example_score + keyword_score, 1.0)

    def _similarity(self, left: str, right: str) -> float:
        """
        计算两个短文本的轻量相似度。

        这是什么：
        - 不依赖 embedding 的简单文本相似度函数。

        做什么：
        - 同时比较词元集合和字符 bigram 集合。
        - 返回 0 到 1 之间的相似度。

        为什么这么做：
        - 中文输入常常没有空格，字符 bigram 比单纯 split 更稳。
        - 英文或混合输入仍可通过词元重叠获得收益。
        """
        # 1. 分别构建词元和字符 bigram 特征
        left_features = self._features(left)
        right_features = self._features(right)
        if not left_features or not right_features:
            return 0.0

        # 2. 使用 Jaccard 相似度衡量重叠程度
        overlap = len(left_features & right_features)
        union = len(left_features | right_features)
        if union == 0:
            return 0.0

        # 3. 返回可解释的轻量相似度分数
        return overlap / union

    def _features(self, text: str) -> set[str]:
        """
        构建文本特征。

        这是什么：
        - 轻量相似度使用的内部特征提取函数。

        做什么：
        - 提取中英文词元。
        - 提取字符 bigram，增强中文短句匹配。

        为什么这么做：
        - 不引入分词器也能获得基本语义近似能力。
        """
        # 1. 归一化空白和标点，减少无意义差异
        normalized = re.sub(r"\s+", "", sanitize_text(text).lower())
        if not normalized:
            return set()

        # 2. 抽取词元，兼容英文、数字和连续中文片段
        tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", normalized))

        # 3. 抽取字符 bigram，覆盖中文同义短句的局部重叠
        bigrams = {normalized[index : index + 2] for index in range(max(len(normalized) - 1, 0))}
        return tokens | bigrams
