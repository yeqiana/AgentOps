"""
资产仓储抽象。
这是什么：
- 多模态输入资产的领域层访问接口。
做什么：
- 规定资产写入和按会话查询的最小能力。
为什么这么做：
- 多模态输入一旦进入后端系统，就不应该只存在当前内存状态里。
"""

from __future__ import annotations

from typing import Protocol

from app.domain.models import AssetRecord


class AssetRepository(Protocol):
    def create_many(self, assets: list[AssetRecord]) -> None:
        ...

    def list_by_session(self, session_id: str) -> list[AssetRecord]:
        ...
