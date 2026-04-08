"""
Workflow nodes.

What this is:
- The LangGraph node implementation layer.

What it does:
- Runs tool selection/execution, planning, and final answering.
- Reads state, invokes tools or model calls, and writes results back into state.

Why this is done this way:
- Nodes should stay thin and orchestration-oriented.
- Asset parsing, storage, and prompt construction should stay in their own
  layers so the workflow can evolve without duplicating logic.
"""

from __future__ import annotations

from pathlib import Path

from app.application.image_service import create_image_asset_from_reference
from app.application.prompt_builder import (
    build_answer_prompt,
    build_arbitration_prompt,
    build_critic_prompt,
    build_debate_prompt,
    build_plan_prompt,
)
from app.config import ensure_upload_download_dir
from app.domain.errors import ToolError
from app.domain.models import AgentState, InputAsset, Message, ToolExecutionResult
from app.infrastructure.llm.client import call_llm, sanitize_text
from app.infrastructure.logger import get_logger
from app.infrastructure.tools.registry import build_default_tool_registry
from app.workflow.policies import decide_route, review_answer
from app.workflow.registry import build_workflow_policy_registry


logger = get_logger("workflow.nodes")


def append_assistant_message(messages: list[Message], answer: str) -> list[Message]:
    """
    What this is:
    - A workflow helper for assistant-message persistence.

    What it does:
    - Appends the latest assistant reply into conversation history.

    Why this is done this way:
    - Multi-turn conversation depends on a complete message history, including
      model replies.
    """

    return [*messages, {"role": "assistant", "content": sanitize_text(answer)}]


def _resolve_local_asset_path(asset: InputAsset) -> str | None:
    """
    What this is:
    - A local file locator helper for tool routing.

    What it does:
    - Returns a resolved local file path only when the asset really points to an
      existing local file.

    Why this is done this way:
    - OCR, ASR, and video CLI tools currently work on local paths, so URL and
      object-storage assets must not accidentally be routed into them.
    """

    local_path = sanitize_text(asset.get("local_path", ""))
    locator = sanitize_text(asset.get("locator", ""))
    candidate = local_path or locator
    if not candidate:
        return None

    path = Path(candidate)
    if not path.exists() or not path.is_file():
        return None
    return str(path.resolve())


def _build_primary_tool_parameters(asset: InputAsset, local_path: str) -> tuple[str, dict[str, str]] | None:
    """
    What this is:
    - The first-pass asset-to-tool routing helper.

    What it does:
    - Maps image/audio/video assets to their primary local tools.

    Why this is done this way:
    - The workflow should decide routing from normalized asset kind instead of
      hard-coding command decisions throughout the node body.
    """

    if asset["kind"] == "image":
        return "ocr_tesseract", {"image_path": local_path}
    if asset["kind"] == "audio":
        return "asr_whisper", {"audio_path": local_path, "model": "tiny"}
    if asset["kind"] == "video":
        return "video_ffprobe", {"video_path": local_path}
    return None


def _build_video_frame_output_path(trace_id: str, video_path: str) -> str:
    """
    What this is:
    - A deterministic frame-output helper for video post-processing.

    What it does:
    - Creates a stable output path for ffmpeg frame extraction inside the
      configured local upload/download root.

    Why this is done this way:
    - Video post-processing must reuse the same configurable local storage
      policy as uploads and OCR-style local tooling.
    """

    frame_dir = ensure_upload_download_dir() / "video_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(video_path).stem or "video"
    return str((frame_dir / f"{stem}_{trace_id}_frame.jpg").resolve())


def _build_video_audio_output_path(trace_id: str, video_path: str) -> str:
    """
    What this is:
    - A deterministic audio-output helper for video post-processing.

    What it does:
    - Creates a stable WAV output path for extracted audio inside the configured
      upload/download root.

    Why this is done this way:
    - Video-derived audio should follow the same local storage policy as uploads
      and generated frames so downstream tools can always find it.
    """

    audio_dir = ensure_upload_download_dir() / "video_audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(video_path).stem or "video"
    return str((audio_dir / f"{stem}_{trace_id}_audio.wav").resolve())


def _summarize_tool_results(tool_results: list[ToolExecutionResult]) -> str:
    """
    What this is:
    - A task-state summarizer for tool execution.

    What it does:
    - Compresses structured tool results into a short, readable status summary.

    Why this is done this way:
    - Planning and answer stages need a compact summary, not only raw stdout.
    """

    if not tool_results:
        return "当前轮未触发工具调用。"

    lines: list[str] = []
    for result in tool_results:
        status = "成功" if result["success"] else "失败"
        summary = sanitize_text(result["stdout"] or result["stderr"] or "无输出")
        lines.append(f"{result['tool_name']}：{status}；摘要：{summary[:200]}")
    return "\n".join(lines)


def tool_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The minimal automated tool-execution node.

    What it does:
    - Detects eligible local assets and triggers OCR, ASR, and video tools.
    - Extends video handling into probe-plus-frame-extraction post-processing.
    - Injects generated frame assets back into `input_assets` so downstream
      planning and answering can see them directly.

    Why this is done this way:
    - This is the point where the project stops being a tool registry demo and
      becomes an agent runtime that can automatically use tools from assets.
    """

    tool_registry = build_default_tool_registry()
    available_tools = set(tool_registry.list_tool_names())
    tool_results: list[ToolExecutionResult] = []
    generated_assets: list[InputAsset] = []

    logger.info(
        "进入 tool_node trace_id=%s 输入资产数=%s 可用工具=%s",
        state["trace_id"],
        len(state["input_assets"]),
        sorted(available_tools),
    )

    for asset in state["input_assets"]:
        local_path = _resolve_local_asset_path(asset)
        if not local_path:
            continue

        primary = _build_primary_tool_parameters(asset, local_path)
        if primary is None:
            continue

        tool_name, parameters = primary
        if tool_name in available_tools:
            try:
                result = tool_registry.execute(tool_name, state["trace_id"], parameters)
                tool_results.append(result)
            except ToolError as error:
                logger.warning("tool_node 工具执行失败 trace_id=%s tool=%s", state["trace_id"], tool_name)
                tool_results.append(
                    {
                        "tool_name": tool_name,
                        "trace_id": state["trace_id"],
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": sanitize_text(str(error)),
                    }
                )

        if asset["kind"] != "video" or "video_ffmpeg_frame" not in available_tools:
            if asset["kind"] != "video":
                continue

        if asset["kind"] == "video" and "video_ffmpeg_frame" in available_tools:
            frame_output_path = _build_video_frame_output_path(state["trace_id"], local_path)
            try:
                frame_result = tool_registry.execute(
                    "video_ffmpeg_frame",
                    state["trace_id"],
                    {"video_path": local_path, "output_path": frame_output_path},
                )
                tool_results.append(frame_result)
                frame_path = Path(frame_output_path)
                if frame_result["success"] and frame_path.exists():
                    _, frame_asset = create_image_asset_from_reference(str(frame_path))
                    frame_asset["source"] = "video_frame"
                    frame_asset["content"] = sanitize_text(
                        f"这是从视频 {Path(local_path).name} 自动抽取的关键帧。\n{frame_asset['content']}"
                    )
                    generated_assets.append(frame_asset)

                    if "ocr_tesseract" in available_tools:
                        ocr_result = tool_registry.execute(
                            "ocr_tesseract",
                            state["trace_id"],
                            {"image_path": str(frame_path)},
                        )
                        tool_results.append(ocr_result)
            except ToolError as error:
                logger.warning("tool_node 视频抽帧失败 trace_id=%s video=%s", state["trace_id"], local_path)
                tool_results.append(
                    {
                        "tool_name": "video_ffmpeg_frame",
                        "trace_id": state["trace_id"],
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": sanitize_text(str(error)),
                    }
                )

        if asset["kind"] == "video" and "video_ffmpeg_audio" in available_tools:
            audio_output_path = _build_video_audio_output_path(state["trace_id"], local_path)
            try:
                audio_result = tool_registry.execute(
                    "video_ffmpeg_audio",
                    state["trace_id"],
                    {"video_path": local_path, "output_path": audio_output_path},
                )
                tool_results.append(audio_result)
                audio_path = Path(audio_output_path)
                if audio_result["success"] and audio_path.exists() and "asr_whisper" in available_tools:
                    asr_result = tool_registry.execute(
                        "asr_whisper",
                        state["trace_id"],
                        {"audio_path": str(audio_path), "model": "tiny"},
                    )
                    tool_results.append(asr_result)
            except ToolError as error:
                logger.warning("tool_node 视频抽音轨失败 trace_id=%s video=%s", state["trace_id"], local_path)
                tool_results.append(
                    {
                        "tool_name": "video_ffmpeg_audio",
                        "trace_id": state["trace_id"],
                        "success": False,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": sanitize_text(str(error)),
                    }
                )

    logger.info(
        "tool_node 执行完成 trace_id=%s 触发工具数=%s 生成资产数=%s",
        state["trace_id"],
        len(tool_results),
        len(generated_assets),
    )
    return {
        **state,
        "input_assets": [*state["input_assets"], *generated_assets],
        "tool_results": tool_results,
        "task_state": _summarize_tool_results(tool_results),
    }


def router_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The stage-2 routing node.

    What it does:
    - Produces a stable route decision before planning.

    Why this is done this way:
    - Routing should become explicit and queryable before the workflow grows
      into multi-graph or multi-agent orchestration.
    """

    route_name, route_reason = decide_route(
        user_input=state["user_input"],
        input_assets=state["input_assets"],
        tool_results=state["tool_results"],
        message_count=len(state["messages"]),
        registry=build_workflow_policy_registry(),
    )
    logger.info("router_node 执行完成 trace_id=%s route=%s", state["trace_id"], route_name)
    return {
        **state,
        "route_name": route_name,
        "route_reason": route_reason,
    }


def plan_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The planning node.

    What it does:
    - Builds the planning prompt and calls the LLM for a task plan.

    Why this is done this way:
    - Planning before answering stabilizes behavior and lets the model reason
      over tool outputs and generated frame assets.
    """

    registry = build_workflow_policy_registry()
    prompt = build_plan_prompt(
        state,
        role_name=registry.planner_role.name,
        stance_instruction=registry.planner_role.stance_instruction,
    )
    logger.info(
        "进入 plan_node trace_id=%s 历史消息数=%s 输入资产数=%s 工具结果数=%s",
        state["trace_id"],
        len(state["messages"]),
        len(state["input_assets"]),
        len(state["tool_results"]),
    )
    plan = call_llm(prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    logger.info("plan_node 执行完成 trace_id=%s", state["trace_id"])

    return {
        **state,
        "user_input": sanitize_text(state["user_input"]),
        "plan": plan,
    }


def debate_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The stage-2 multi-agent debate node.

    What it does:
    - Runs two explicit roles over the same task: a supporting perspective and
      a challenging perspective.

    Why this is done this way:
    - Multi-agent orchestration should begin with controlled role separation so
      the runtime can compare perspectives before answering.
    """

    if state["route_name"] != "deliberation_chat":
        return {
            **state,
            "debate_summary": "当前路由未启用多 Agent 辩论。",
        }

    registry = build_workflow_policy_registry()
    support_prompt = build_debate_prompt(
        state,
        role_name=registry.support_role.name,
        stance_instruction=registry.support_role.stance_instruction,
    )
    challenge_prompt = build_debate_prompt(
        state,
        role_name=registry.challenge_role.name,
        stance_instruction=registry.challenge_role.stance_instruction,
    )
    logger.info("进入 debate_node trace_id=%s route=%s", state["trace_id"], state["route_name"])
    support_summary = call_llm(support_prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    challenge_summary = call_llm(challenge_prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    debate_summary = (
        f"{registry.support_role.name}：{sanitize_text(support_summary)}\n"
        f"{registry.challenge_role.name}：{sanitize_text(challenge_summary)}"
    )
    logger.info("debate_node 执行完成 trace_id=%s", state["trace_id"])
    return {
        **state,
        "debate_summary": debate_summary,
    }


def arbitration_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The stage-2 arbitration node.

    What it does:
    - Summarizes and resolves the debate before the answer node runs.

    Why this is done this way:
    - Debate alone does not improve answer quality unless the system can turn
      multiple viewpoints into a single execution decision.
    """

    if state["route_name"] != "deliberation_chat":
        return {
            **state,
            "arbitration_summary": "当前路由未启用仲裁。",
        }

    registry = build_workflow_policy_registry()
    prompt = build_arbitration_prompt(
        state,
        role_name=registry.arbitration_role.name,
        stance_instruction=registry.arbitration_role.stance_instruction,
    )
    logger.info("进入 arbitration_node trace_id=%s route=%s", state["trace_id"], state["route_name"])
    arbitration_summary = call_llm(prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    logger.info("arbitration_node 执行完成 trace_id=%s", state["trace_id"])
    return {
        **state,
        "arbitration_summary": arbitration_summary,
    }


def answer_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The final answer node.

    What it does:
    - Builds the answer prompt, calls the LLM, and appends the assistant reply.

    Why this is done this way:
    - The answer stage needs the full state: conversation history, planning
      output, tool results, and generated multimodal assets.
    """

    registry = build_workflow_policy_registry()
    prompt = build_answer_prompt(
        state,
        role_name=registry.executor_role.name,
        stance_instruction=registry.executor_role.stance_instruction,
    )
    logger.info(
        "进入 answer_node trace_id=%s 历史消息数=%s 输入资产数=%s 工具结果数=%s",
        state["trace_id"],
        len(state["messages"]),
        len(state["input_assets"]),
        len(state["tool_results"]),
    )
    answer = call_llm(prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    updated_messages = append_assistant_message(state["messages"], answer)
    logger.info("answer_node 执行完成 trace_id=%s", state["trace_id"])

    return {
        **state,
        "answer": answer,
        "messages": updated_messages,
    }


def critic_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The stage-2 critic node.

    What it does:
    - Uses a dedicated critic prompt to produce a second-agent quality note.

    Why this is done this way:
    - Multi-agent orchestration starts with explicit role separation. The critic
      role should be independently queryable before adding debate graphs.
    """

    registry = build_workflow_policy_registry()
    prompt = build_critic_prompt(
        state,
        role_name=registry.critic_role.name,
        stance_instruction=registry.critic_role.stance_instruction,
    )
    logger.info("进入 critic_node trace_id=%s route=%s", state["trace_id"], state["route_name"] or "unknown")
    critic_summary = call_llm(prompt, input_assets=state["input_assets"], trace_id=state["trace_id"])
    logger.info("critic_node 执行完成 trace_id=%s", state["trace_id"])
    return {
        **state,
        "critic_summary": critic_summary,
    }


def review_node(state: AgentState) -> AgentState:
    """
    What this is:
    - The stage-2 review node.

    What it does:
    - Evaluates the final answer and writes a concise review result into state.

    Why this is done this way:
    - Review becomes a first-class part of the execution trace, which makes the
      workflow easier to audit and prepares the graph for future review agents.
    """

    registry = build_workflow_policy_registry()
    review_status, review_summary = review_answer(
        answer=state["answer"],
        tool_results=state["tool_results"],
        critic_summary=state["critic_summary"],
        arbitration_summary=state["arbitration_summary"],
    )
    review_summary = f"{registry.reviewer_role.name}：{review_summary}"
    logger.info("review_node 执行完成 trace_id=%s review_status=%s", state["trace_id"], review_status)
    return {
        **state,
        "review_status": review_status,
        "review_summary": review_summary,
    }
