"""
持久化基础设施包。
这是什么：
- 这是数据库连接和 Repository 实现的统一挂载位置。
做什么：
- 暴露数据库初始化和 SQLite Repository 实现。
为什么这么做：
- 阶段 1 先固定持久化落点，后面切换到更复杂实现时不会打散结构。
"""

from app.infrastructure.persistence.database import ensure_database_initialized, get_connection

__all__ = ["ensure_database_initialized", "get_connection"]
