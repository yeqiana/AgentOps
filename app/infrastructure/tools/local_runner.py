"""
本地工具执行器。
这是什么：
- 这是最小的本地命令执行封装。
做什么：
- 执行命令。
- 捕获 stdout / stderr。
- 统一返回成功与失败结果。
为什么这么做：
- 工具能力是后续 OCR、ASR、视频处理等本地软件接入的基础。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.domain.errors import ToolError
from app.domain.models import ToolExecutionResult


class LocalToolRunner:
    """
    本地工具执行器。
    这是什么：
    - 对 `subprocess.run` 的稳定封装。
    做什么：
    - 执行本地命令并返回统一结构。
    为什么这么做：
    - 让上层不用关心 stdout、stderr、退出码和超时细节。
    """

    def run(
        self,
        command: list[str],
        *,
        trace_id: str,
        timeout_seconds: int = 30,
        cwd: str | None = None,
        input_text: str | None = None,
    ) -> ToolExecutionResult:
        try:
            completed = subprocess.run(
                command,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                cwd=Path(cwd) if cwd else None,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                "本地工具执行超时。",
                trace_id=trace_id,
                details={"command": " ".join(command), "timeout_seconds": str(timeout_seconds)},
            ) from error
        except OSError as error:
            raise ToolError(
                "本地工具执行失败。",
                trace_id=trace_id,
                details={"command": " ".join(command), "reason": str(error)},
            ) from error

        return {
            "tool_name": command[0],
            "trace_id": trace_id,
            "success": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
