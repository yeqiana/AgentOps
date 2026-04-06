"""
Local tool adapters.

What this is:
- The adapter layer for OCR, ASR, and video-processing local tools.

What it does:
- Discovers commands from environment variables or PATH.
- Builds concrete CLI invocations for each supported tool.
- Returns unified tool execution results through `LocalToolRunner`.

Why this is done this way:
- The registry should only handle registration and dispatch.
- Command construction belongs in adapters so tool protocols stay isolated from
  workflow and service code.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from app.domain.errors import ToolError
from app.domain.models import ToolExecutionResult
from app.infrastructure.tools.local_runner import LocalToolRunner


def _resolve_command(explicit_env_name: str, default_command: str) -> str | None:
    configured = os.getenv(explicit_env_name, "").strip()
    if configured:
        return configured
    return shutil.which(default_command)


@dataclass(frozen=True)
class ToolAdapterDefinition:
    """
    What this is:
    - A registration-time definition for one local tool.

    What it does:
    - Stores the logical tool name, description, and resolved command path.

    Why this is done this way:
    - The registry needs a stable structure for conditional registration based on
      what the current machine actually has installed.
    """

    name: str
    description: str
    command: str | None

    @property
    def is_available(self) -> bool:
        return bool(self.command)


def build_ocr_definition() -> ToolAdapterDefinition:
    return ToolAdapterDefinition(
        name="ocr_tesseract",
        description="使用 Tesseract 对本地图像执行 OCR 识别。",
        command=_resolve_command("OCR_TOOL_PATH", "tesseract"),
    )


def build_asr_definition() -> ToolAdapterDefinition:
    return ToolAdapterDefinition(
        name="asr_whisper",
        description="使用 Whisper CLI 对本地音频执行语音转写。",
        command=_resolve_command("ASR_TOOL_PATH", "whisper"),
    )


def build_video_probe_definition() -> ToolAdapterDefinition:
    return ToolAdapterDefinition(
        name="video_ffprobe",
        description="使用 ffprobe 读取本地视频流信息。",
        command=_resolve_command("VIDEO_PROBE_TOOL_PATH", "ffprobe"),
    )


def build_video_frame_definition() -> ToolAdapterDefinition:
    return ToolAdapterDefinition(
        name="video_ffmpeg_frame",
        description="使用 ffmpeg 为本地视频抽取关键帧。",
        command=_resolve_command("VIDEO_FRAME_TOOL_PATH", "ffmpeg"),
    )


def build_video_audio_definition() -> ToolAdapterDefinition:
    return ToolAdapterDefinition(
        name="video_ffmpeg_audio",
        description="使用 ffmpeg 从本地视频中抽取音轨。",
        command=_resolve_command("VIDEO_AUDIO_TOOL_PATH", "ffmpeg"),
    )


def run_ocr_tool(runner: LocalToolRunner, command: str, trace_id: str, parameters: dict[str, str]) -> ToolExecutionResult:
    image_path = parameters.get("image_path", "").strip()
    if not image_path:
        raise ToolError("OCR 工具需要 `image_path` 参数。", trace_id=trace_id)
    return runner.run([command, image_path, "stdout"], trace_id=trace_id)


def run_asr_tool(runner: LocalToolRunner, command: str, trace_id: str, parameters: dict[str, str]) -> ToolExecutionResult:
    audio_path = parameters.get("audio_path", "").strip()
    model = parameters.get("model", "base")
    if not audio_path:
        raise ToolError("ASR 工具需要 `audio_path` 参数。", trace_id=trace_id)
    return runner.run([command, audio_path, "--model", model], trace_id=trace_id, timeout_seconds=300)


def run_video_probe_tool(
    runner: LocalToolRunner,
    command: str,
    trace_id: str,
    parameters: dict[str, str],
) -> ToolExecutionResult:
    video_path = parameters.get("video_path", "").strip()
    if not video_path:
        raise ToolError("视频探测工具需要 `video_path` 参数。", trace_id=trace_id)
    return runner.run(
        [command, "-v", "error", "-show_format", "-show_streams", video_path],
        trace_id=trace_id,
        timeout_seconds=120,
    )


def run_video_frame_tool(
    runner: LocalToolRunner,
    command: str,
    trace_id: str,
    parameters: dict[str, str],
) -> ToolExecutionResult:
    video_path = parameters.get("video_path", "").strip()
    output_path = parameters.get("output_path", "").strip()
    if not video_path or not output_path:
        raise ToolError("视频抽帧工具需要 `video_path` 和 `output_path` 参数。", trace_id=trace_id)
    return runner.run(
        [command, "-y", "-i", video_path, "-frames:v", "1", output_path],
        trace_id=trace_id,
        timeout_seconds=300,
    )


def run_video_audio_tool(
    runner: LocalToolRunner,
    command: str,
    trace_id: str,
    parameters: dict[str, str],
) -> ToolExecutionResult:
    video_path = parameters.get("video_path", "").strip()
    output_path = parameters.get("output_path", "").strip()
    if not video_path or not output_path:
        raise ToolError("视频抽音轨工具需要 `video_path` 和 `output_path` 参数。", trace_id=trace_id)
    return runner.run(
        [command, "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", output_path],
        trace_id=trace_id,
        timeout_seconds=300,
    )
