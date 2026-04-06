"""
用户仓储抽象。
这是什么：
- 用户数据的领域层访问接口。
做什么：
- 规定用户创建和查询的最小能力。
为什么这么做：
- 即使当前只有单机默认用户，后面做多用户平台时也不用推翻接口。
"""

from __future__ import annotations

from typing import Protocol

from app.domain.models import UserRecord


class UserRepository(Protocol):
    def get_or_create(self, user_name: str) -> UserRecord:
        ...

    def get_by_id(self, user_id: str) -> UserRecord | None:
        ...
