"""
Retry policy helpers.

What this is:
- Shared retry helpers for model and tool execution.

What it does:
- Executes an operation with bounded retry attempts and fixed backoff.
- Restricts retries to known transient failure categories.

Why this is done this way:
- Stage 2 needs a centralized retry policy so retries do not become ad-hoc and
  inconsistent across model and tool code paths.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from app.domain.errors import AgentError
from app.infrastructure.logger import get_logger


T = TypeVar("T")
logger = get_logger("infrastructure.tools.retry_policy")


def execute_with_retry(
    operation: Callable[[], T],
    *,
    attempts: int,
    backoff_ms: int,
    should_retry: Callable[[Exception], bool],
    on_retry: Callable[[Exception, int], None] | None = None,
) -> T:
    last_error: Exception | None = None
    total_attempts = max(1, attempts)
    for attempt in range(1, total_attempts + 1):
        try:
            return operation()
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt >= total_attempts or not should_retry(error):
                raise
            if on_retry:
                on_retry(error, attempt)
            logger.warning("执行重试 attempt=%s/%s error=%s", attempt, total_attempts, error)
            time.sleep(max(0, backoff_ms) / 1000)
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry policy reached an invalid state")
