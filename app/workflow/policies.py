"""
Workflow policies.

What this is:
- Shared routing and review policy helpers for stage-2 orchestration.

What it does:
- Produces deterministic route decisions from assets, tool results, and task
  text.
- Produces deterministic review conclusions from final answers, tool outcomes,
  and critic feedback.

Why this is done this way:
- Stage 2 should make orchestration policy explicit before the project grows
  into multiple graphs or external strategy configuration.
"""

from __future__ import annotations

from app.infrastructure.llm.client import sanitize_text
from app.workflow.registry import WorkflowPolicyRegistry, build_workflow_policy_registry


def decide_route(
    *,
    user_input: str,
    input_assets: list[dict[str, object]],
    tool_results: list[dict[str, object]],
    message_count: int,
    registry: WorkflowPolicyRegistry | None = None,
) -> tuple[str, str]:
    current_registry = registry or build_workflow_policy_registry()
    cleaned_input = sanitize_text(user_input).lower()
    asset_kinds = {str(asset["kind"]) for asset in input_assets}

    if "video" in asset_kinds:
        return "video_analysis", "检测到视频资产，优先走视频分析与后处理增强链。"
    if "audio" in asset_kinds:
        return "audio_analysis", "检测到音频资产，优先走音频转写与分析链。"
    if "file" in asset_kinds:
        return "document_analysis", "检测到文档资产，优先走文档解析与总结链。"
    if "image" in asset_kinds:
        return "image_analysis", "检测到图片资产，优先走图片理解与 OCR 增强链。"
    if tool_results:
        return "tool_augmented_chat", "检测到已有工具结果，优先结合工具输出完成回答。"
    if current_registry.deliberation_enabled and any(
        keyword.lower() in cleaned_input for keyword in current_registry.deliberation_keywords
    ):
        return "deliberation_chat", "检测到比较或评审型任务，优先进入更审慎的分析路径。"
    if message_count > 2:
        return "contextual_chat", "检测到多轮上下文，优先保持连续对话一致性。"
    return "direct_chat", "当前是普通文本任务，优先走标准规划与回答链。"


def review_answer(
    *,
    answer: str,
    tool_results: list[dict[str, object]],
    critic_summary: str,
    arbitration_summary: str,
) -> tuple[str, str]:
    cleaned_answer = sanitize_text(answer)
    cleaned_critic = sanitize_text(critic_summary).lower()
    cleaned_arbitration = sanitize_text(arbitration_summary).lower()

    if not cleaned_answer:
        return "rejected", "最终答案为空，未满足交付要求。"

    failed_tools = [result for result in tool_results if not bool(result["success"])]
    if failed_tools and not any(word in cleaned_answer for word in {"失败", "限制", "无法"}):
        return "needs_revision", "存在工具失败记录，但答案中没有充分解释失败影响。"

    if "缺少" in cleaned_critic or "不足" in cleaned_critic or "风险" in cleaned_critic:
        return "needs_revision", "批评代理识别到结果存在信息不足或风险提示，需要修订。"

    if "风险" in cleaned_arbitration or "遗漏" in cleaned_arbitration:
        return "needs_revision", "仲裁代理认为最终答案仍需补充风险或遗漏说明。"

    if len(cleaned_answer) < 10:
        return "needs_attention", "最终答案过短，建议补充更明确的结果说明。"

    return "approved", "结果已通过当前规则复核，可作为默认输出。"
