"""
Tool registry.

What this is:
- The stage-1 minimal tool gateway implementation.

What it does:
- Registers logical tools.
- Executes tools by name.
- Builds a default registry from tools available in the current environment.

Why this is done this way:
- Without a central registry, local tool calls quickly spread across services
  and workflow code.
- A single gateway keeps runtime capability discovery stable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.domain.errors import ToolError
from app.domain.models import ToolExecutionResult
from app.infrastructure.logger import get_logger
from app.infrastructure.tools.adapters import (
    build_asr_definition,
    build_ocr_definition,
    build_video_audio_definition,
    build_video_frame_definition,
    build_video_probe_definition,
    run_asr_tool,
    run_ocr_tool,
    run_video_audio_tool,
    run_video_frame_tool,
    run_video_probe_tool,
)
from app.infrastructure.tools.local_runner import LocalToolRunner


ToolHandler = Callable[[str, dict[str, str]], ToolExecutionResult]
logger = get_logger("infrastructure.tools.registry")


@dataclass
class RegisteredTool:
    name: str
    description: str
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, name: str, description: str, handler: ToolHandler) -> None:
        self._tools[name] = RegisteredTool(name=name, description=description, handler=handler)

    def list_tool_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool_descriptions(self) -> dict[str, str]:
        return {name: tool.description for name, tool in sorted(self._tools.items())}

    def execute(self, name: str, trace_id: str, parameters: dict[str, str] | None = None) -> ToolExecutionResult:
        if name not in self._tools:
            raise ToolError(f"未找到工具 `{name}`。", trace_id=trace_id, details={"tool_name": name})
        result = self._tools[name].handler(trace_id, parameters or {})
        return {**result, "tool_name": name}


def build_default_tool_registry() -> ToolRegistry:
    runner = LocalToolRunner()
    registry = ToolRegistry()

    def run_python_echo(trace_id: str, parameters: dict[str, str]) -> ToolExecutionResult:
        message = parameters.get("message", "")
        return runner.run(
            ["python", "-c", "print(input())"],
            trace_id=trace_id,
            input_text=message,
        )

    registry.register(
        name="python_echo",
        description="使用本地 Python 读取一段输入并原样输出，用于验证工具网关链路。",
        handler=run_python_echo,
    )

    ocr_definition = build_ocr_definition()
    if ocr_definition.is_available and ocr_definition.command:
        registry.register(
            name=ocr_definition.name,
            description=ocr_definition.description,
            handler=lambda trace_id, parameters, command=ocr_definition.command: run_ocr_tool(
                runner,
                command,
                trace_id,
                parameters,
            ),
        )
    else:
        logger.info("未发现 OCR 工具，ocr_tesseract 不注册。")

    asr_definition = build_asr_definition()
    if asr_definition.is_available and asr_definition.command:
        registry.register(
            name=asr_definition.name,
            description=asr_definition.description,
            handler=lambda trace_id, parameters, command=asr_definition.command: run_asr_tool(
                runner,
                command,
                trace_id,
                parameters,
            ),
        )
    else:
        logger.info("未发现 ASR 工具，asr_whisper 不注册。")

    video_probe_definition = build_video_probe_definition()
    if video_probe_definition.is_available and video_probe_definition.command:
        registry.register(
            name=video_probe_definition.name,
            description=video_probe_definition.description,
            handler=lambda trace_id, parameters, command=video_probe_definition.command: run_video_probe_tool(
                runner,
                command,
                trace_id,
                parameters,
            ),
        )
    else:
        logger.info("未发现 ffprobe，video_ffprobe 不注册。")

    video_frame_definition = build_video_frame_definition()
    if video_frame_definition.is_available and video_frame_definition.command:
        registry.register(
            name=video_frame_definition.name,
            description=video_frame_definition.description,
            handler=lambda trace_id, parameters, command=video_frame_definition.command: run_video_frame_tool(
                runner,
                command,
                trace_id,
                parameters,
            ),
        )
    else:
        logger.info("未发现 ffmpeg，video_ffmpeg_frame 不注册。")

    video_audio_definition = build_video_audio_definition()
    if video_audio_definition.is_available and video_audio_definition.command:
        registry.register(
            name=video_audio_definition.name,
            description=video_audio_definition.description,
            handler=lambda trace_id, parameters, command=video_audio_definition.command: run_video_audio_tool(
                runner,
                command,
                trace_id,
                parameters,
            ),
        )
    else:
        logger.info("未发现 ffmpeg，video_ffmpeg_audio 不注册。")

    return registry
