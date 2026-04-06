"""
会话仓储抽象。
这是什么：
- 会话数据的领域层访问接口。
做什么：
- 规定会话创建、查询和更新的最小能力。
为什么这么做：
- 会话是 Agent 后端底座的核心状态对象，必须先形成稳定抽象。
"""

from __future__ import annotations

from typing import Protocol

from app.domain.models import SessionRecord


class SessionRepository(Protocol):
    def create(self, user_id: str, session_id: str, title: str) -> SessionRecord:
        ...

    def get_by_id(self, session_id: str) -> SessionRecord | None:
        ...

    def update_last_trace(self, session_id: str, trace_id: str) -> None:
        ...
