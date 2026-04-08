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

from app.config import (
    get_tool_circuit_failure_threshold,
    get_tool_circuit_recovery_seconds,
    get_tool_retry_attempts,
    get_tool_retry_backoff_ms,
    is_tool_circuit_enabled,
    is_tool_retry_enabled,
)
from app.domain.errors import ToolError
from app.domain.models import ToolExecutionResult
from app.infrastructure.tools.failure_recovery import emit_recovery_alert, get_circuit_breaker
from app.infrastructure.tools.retry_policy import execute_with_retry


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
        breaker = None
        if is_tool_circuit_enabled():
            breaker = get_circuit_breaker(
                f"tool:{command[0]}",
                failure_threshold=get_tool_circuit_failure_threshold(),
                recovery_seconds=get_tool_circuit_recovery_seconds(),
            )
            if not breaker.allow_request():
                emit_recovery_alert(
                    trace_id=trace_id,
                    source_type="tool",
                    source_name=command[0],
                    severity="warning",
                    event_code="tool_circuit_open_fast_fail",
                    message="本地工具熔断已开启，本次调用进入快速失败。",
                    payload={"command": " ".join(command)},
                )
                raise ToolError(
                    "本地工具熔断已开启，请稍后再试。",
                    trace_id=trace_id,
                    details={"command": " ".join(command), "degrade_mode": "fast_fail"},
                )

        def _invoke() -> subprocess.CompletedProcess[str]:
            try:
                return subprocess.run(
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

        def _should_retry(error: Exception) -> bool:
            if not isinstance(error, ToolError):
                return False
            return error.message in {"本地工具执行超时。", "本地工具执行失败。"}

        try:
            if is_tool_retry_enabled():
                completed = execute_with_retry(
                    _invoke,
                    attempts=get_tool_retry_attempts(),
                    backoff_ms=get_tool_retry_backoff_ms(),
                    should_retry=_should_retry,
                )
            else:
                completed = _invoke()
        except ToolError:
            if breaker is not None:
                breaker.record_failure()
                if breaker.opened_until > 0:
                    emit_recovery_alert(
                        trace_id=trace_id,
                        source_type="tool",
                        source_name=command[0],
                        severity="error",
                        event_code="tool_circuit_opened",
                        message="本地工具连续失败已触发熔断。",
                        payload={"command": " ".join(command), "failure_count": breaker.failure_count},
                    )
                else:
                    emit_recovery_alert(
                        trace_id=trace_id,
                        source_type="tool",
                        source_name=command[0],
                        severity="warning",
                        event_code="tool_retry_exhausted" if is_tool_retry_enabled() else "tool_request_failed",
                        message="本地工具重试后仍失败。" if is_tool_retry_enabled() else "本地工具请求失败。",
                        payload={"command": " ".join(command)},
                    )
            raise

        if breaker is not None:
            breaker.record_success()

        return {
            "tool_name": command[0],
            "trace_id": trace_id,
            "success": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
