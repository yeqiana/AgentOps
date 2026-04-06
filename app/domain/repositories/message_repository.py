"""
消息仓储抽象。
这是什么：
- 对话消息数据的领域层访问接口。
做什么：
- 规定消息写入和按会话查询的最小能力。
为什么这么做：
- 多轮上下文和排障都依赖消息历史，不能只留在内存里。
"""

from __future__ import annotations

from typing import Protocol

from app.domain.models import MessageRecord


class MessageRepository(Protocol):
    def create(self, message: MessageRecord) -> None:
        ...

    def list_by_session(self, session_id: str) -> list[MessageRecord]:
        ...
