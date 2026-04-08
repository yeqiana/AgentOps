"""
Failure recovery helpers.

What this is:
- Shared circuit-breaker helpers for model and tool execution.

What it does:
- Tracks consecutive failures in memory.
- Opens a circuit after a configured threshold.
- Provides a fast-fail degradation mode until the recovery window passes.

Why this is done this way:
- Stage 2 needs more than retries. Once a dependency is clearly unstable, the
  runtime should degrade quickly instead of repeatedly amplifying failure.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    failure_threshold: int
    recovery_seconds: int
    failure_count: int = 0
    opened_until: float = 0.0

    def allow_request(self) -> bool:
        if self.opened_until <= 0:
            return True
        if time.time() >= self.opened_until:
            self.failure_count = 0
            self.opened_until = 0.0
            return True
        return False

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_until = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= max(1, self.failure_threshold):
            self.opened_until = time.time() + max(1, self.recovery_seconds)


_BREAKERS: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(key: str, *, failure_threshold: int, recovery_seconds: int) -> CircuitBreaker:
    if key not in _BREAKERS:
        _BREAKERS[key] = CircuitBreaker(
            failure_threshold=max(1, failure_threshold),
            recovery_seconds=max(1, recovery_seconds),
        )
    return _BREAKERS[key]


def reset_circuit_breakers() -> None:
    _BREAKERS.clear()
