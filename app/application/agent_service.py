"""
Agent 应用服务模块。
这是什么：
- 这是负责状态初始化、输入解析和会话辅助逻辑的应用层模块。
做什么：
- 创建初始状态。
- 追加用户消息。
- 解析命令行或 API 输入到统一输入资产结构。
- 格式化对话历史。
为什么这么做：
- 这些逻辑属于应用编排，不应该塞进 CLI，也不应该下沉到模型或数据库层。
"""

from __future__ import annotations

import uuid

from app.application.audio_service import create_audio_asset_from_base64, create_audio_asset_from_reference
from app.application.file_service import create_file_asset_from_base64, create_file_asset_from_reference
from app.application.image_service import create_image_asset_from_base64, create_image_asset_from_reference
from app.application.video_service import create_video_asset_from_base64, create_video_asset_from_reference
from app.config import (
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TASK_STATE,
    DEFAULT_TONE_STYLE,
    DEFAULT_USER_PROFILE,
    DEFAULT_VERBOSITY_LEVEL,
    create_default_runtime_context,
)
from app.domain.errors import ParsingError
from app.domain.models import AgentState, InputAsset, Message
from app.infrastructure.llm.client import sanitize_text


REAL_IMAGE_PREFIXES = {
    "/image-file": "reference",
    "/image-url": "reference",
    "/image-object": "reference",
    "/image-base64": "base64",
}

REAL_AUDIO_PREFIXES = {
    "/audio-file": "reference",
    "/audio-url": "reference",
    "/audio-object": "reference",
    "/audio-base64": "base64",
}

REAL_VIDEO_PREFIXES = {
    "/video-file": "reference",
    "/video-url": "reference",
    "/video-object": "reference",
    "/video-base64": "base64",
}

REAL_FILE_PREFIXES = {
    "/file-path": "reference",
    "/file-url": "reference",
    "/file-object": "reference",
    "/file-base64": "base64",
}

SIMULATED_PREFIXES = {
    "/image": "image",
    "/audio": "audio",
    "/video": "video",
    "/file": "file",
}


def _generate_identifier(prefix: str) -> str:
    """
    生成带前缀的唯一标识。
    这是什么：
    - 状态和执行链路使用的 ID 工具函数。
    做什么：
    - 为 session、turn、task、trace 生成唯一字符串。
    为什么这么做：
    - 阶段 1 先用最简单的 UUID 方案，就足够把执行链路打通。
    """
    return f"{prefix}_{uuid.uuid4().hex}"


def create_initial_state(user_id: str = "local-user") -> AgentState:
    """
    创建初始状态。
    这是什么：
    - AgentState 工厂函数。
    做什么：
    - 返回一份带默认运行时配置和会话标识的初始状态。
    为什么这么做：
    - 初始状态不应该在 CLI 或 API 中手写，集中在应用层最清晰。
    """
    return {
        "user_id": user_id,
        "session_id": _generate_identifier("session"),
        "turn_id": "",
        "task_id": "",
        "trace_id": "",
        "user_input": "",
        "route_name": "",
        "route_reason": "",
        "plan": "",
        "debate_summary": "",
        "arbitration_summary": "",
        "answer": "",
        "critic_summary": "",
        "review_status": "",
        "review_summary": "",
        "messages": [],
        "input_assets": [],
        "tool_results": [],
        "runtime_context": create_default_runtime_context(),
        "user_profile": DEFAULT_USER_PROFILE,
        "task_state": DEFAULT_TASK_STATE,
        "output_format": DEFAULT_OUTPUT_FORMAT,
        "tone_style": DEFAULT_TONE_STYLE,
        "verbosity_level": DEFAULT_VERBOSITY_LEVEL,
        "last_error": None,
    }


def append_user_message(messages: list[Message], user_input: str) -> list[Message]:
    """
    追加用户消息。
    这是什么：
    - 会话历史更新函数。
    做什么：
    - 把当前轮用户输入写入消息历史。
    为什么这么做：
    - 多轮上下文要成立，前提就是每轮输入都进入历史。
    """
    return [*messages, {"role": "user", "content": sanitize_text(user_input)}]


def _build_text_asset(user_input: str) -> tuple[str, list[InputAsset]]:
    cleaned_input = sanitize_text(user_input)
    return cleaned_input, [
        {
            "kind": "text",
            "name": "text_input",
            "content": cleaned_input,
            "source": "command_line",
            "storage_mode": "inline_text",
        }
    ]


def _split_reference_and_prompt(payload: str) -> tuple[str, str]:
    if "|" not in payload:
        return sanitize_text(payload), ""

    reference, prompt = payload.split("|", 1)
    return sanitize_text(reference), sanitize_text(prompt)


def _ensure_reference(reference: str, asset_label: str) -> str:
    if not reference:
        raise ParsingError(f"{asset_label} 引用不能为空。")
    return reference


def _build_real_image_asset(prefix_kind: str, payload: str) -> tuple[str, list[InputAsset]]:
    reference, user_prompt = _split_reference_and_prompt(payload)
    reference = _ensure_reference(reference, "图片")
    if prefix_kind == "base64":
        default_prompt, asset = create_image_asset_from_base64(reference)
    else:
        default_prompt, asset = create_image_asset_from_reference(reference)
    return user_prompt or default_prompt, [asset]


def _build_real_audio_asset(prefix_kind: str, payload: str) -> tuple[str, list[InputAsset]]:
    reference, user_prompt = _split_reference_and_prompt(payload)
    reference = _ensure_reference(reference, "音频")
    if prefix_kind == "base64":
        default_prompt, asset = create_audio_asset_from_base64(reference)
    else:
        default_prompt, asset = create_audio_asset_from_reference(reference)
    return user_prompt or default_prompt, [asset]


def _build_real_video_asset(prefix_kind: str, payload: str) -> tuple[str, list[InputAsset]]:
    reference, user_prompt = _split_reference_and_prompt(payload)
    reference = _ensure_reference(reference, "视频")
    if prefix_kind == "base64":
        default_prompt, asset = create_video_asset_from_base64(reference)
    else:
        default_prompt, asset = create_video_asset_from_reference(reference)
    return user_prompt or default_prompt, [asset]


def _build_real_file_asset(prefix_kind: str, payload: str) -> tuple[str, list[InputAsset]]:
    reference, user_prompt = _split_reference_and_prompt(payload)
    reference = _ensure_reference(reference, "文件")
    if prefix_kind == "base64":
        default_prompt, asset = create_file_asset_from_base64(reference)
    else:
        default_prompt, asset = create_file_asset_from_reference(reference)
    return user_prompt or default_prompt, [asset]


def _build_simulated_asset(kind: str, payload: str) -> tuple[str, list[InputAsset]]:
    content = sanitize_text(payload) or "用户声明存在该模态输入，但未提供更多描述。"
    return content, [
        {
            "kind": kind,
            "name": f"{kind}_asset",
            "content": content,
            "source": "command_line_prefix",
            "storage_mode": "inline_text",
        }
    ]


def parse_input_assets(raw_input: str) -> tuple[str, list[InputAsset]]:
    """
    解析输入资产。
    这是什么：
    - 命令行和 API 输入到统一资产结构的转换函数。
    做什么：
    - 支持文本、模拟多模态输入和真实多模态引用输入。
    为什么这么做：
    - 上层入口应该简单，系统内部必须拿到稳定的结构化输入。
    """
    cleaned_input = sanitize_text(raw_input)
    lowered_input = cleaned_input.lower()

    try:
        for prefix, prefix_kind in REAL_IMAGE_PREFIXES.items():
            if lowered_input.startswith(prefix):
                payload = cleaned_input[len(prefix) :].strip()
                return _build_real_image_asset(prefix_kind, payload)

        for prefix, prefix_kind in REAL_AUDIO_PREFIXES.items():
            if lowered_input.startswith(prefix):
                payload = cleaned_input[len(prefix) :].strip()
                return _build_real_audio_asset(prefix_kind, payload)

        for prefix, prefix_kind in REAL_VIDEO_PREFIXES.items():
            if lowered_input.startswith(prefix):
                payload = cleaned_input[len(prefix) :].strip()
                return _build_real_video_asset(prefix_kind, payload)

        for prefix, prefix_kind in REAL_FILE_PREFIXES.items():
            if lowered_input.startswith(prefix):
                payload = cleaned_input[len(prefix) :].strip()
                return _build_real_file_asset(prefix_kind, payload)

        for prefix, kind in SIMULATED_PREFIXES.items():
            if lowered_input.startswith(prefix):
                payload = cleaned_input[len(prefix) :].strip()
                return _build_simulated_asset(kind, payload)
    except ParsingError:
        raise
    except Exception as error:
        raise ParsingError("输入解析失败。", details={"reason": sanitize_text(str(error))}) from error

    return _build_text_asset(cleaned_input)


def format_conversation_history(messages: list[Message]) -> str:
    """
    格式化对话历史。
    这是什么：
    - 历史消息到调试文本的转换函数。
    做什么：
    - 按“用户 / 助手”的格式输出完整会话历史。
    为什么这么做：
    - 日志和排障时看一段完整文本，比看原始列表更直接。
    """
    if not messages:
        return "暂无历史对话。"

    return "\n".join(
        f"{'用户' if message['role'] == 'user' else '助手'}：{sanitize_text(message['content'])}"
        for message in messages
    )
