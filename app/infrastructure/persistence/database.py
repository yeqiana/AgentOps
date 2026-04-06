"""
SQLite 持久化基础设施。
这是什么：
- 当前阶段的数据库连接和建表入口。
做什么：
- 解析数据库配置。
- 创建 SQLite 连接。
- 初始化阶段 1 需要的核心表。
为什么这么做：
- 标准库自带 sqlite3，适合现在先把状态底座打稳。
- 等后面切 PostgreSQL 时，只需要替换这里和 Repository 实现。
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.domain.errors import PersistenceError


DEFAULT_DATABASE_URL = "sqlite:///data/agent.db"

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        last_trace_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        name TEXT NOT NULL,
        source TEXT NOT NULL,
        content TEXT NOT NULL,
        storage_mode TEXT NOT NULL,
        locator TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        status TEXT NOT NULL,
        user_input TEXT NOT NULL,
        plan TEXT NOT NULL,
        answer TEXT NOT NULL,
        tool_count INTEGER NOT NULL,
        error_message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tool_results (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        success INTEGER NOT NULL,
        exit_code INTEGER NOT NULL,
        stdout TEXT NOT NULL,
        stderr TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """,
)


def get_database_url() -> str:
    """
    读取数据库地址。
    这是什么：
    - 数据库配置读取函数。
    做什么：
    - 返回当前数据库 URL。
    为什么这么做：
    - 把配置读取统一放在一起，后面切数据库实现时不需要到处找环境变量。
    """
    return os.getenv("APP_DATABASE_URL", DEFAULT_DATABASE_URL).strip() or DEFAULT_DATABASE_URL


def _resolve_sqlite_path(database_url: str) -> Path:
    """
    解析 SQLite 路径。
    这是什么：
    - 数据库 URL 到文件路径的转换函数。
    做什么：
    - 从 `sqlite:///...` 格式中解析出真实路径。
    为什么这么做：
    - 当前只做 SQLite，先把最小配置约定固定下来即可。
    """
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise PersistenceError(
            "当前阶段仅支持 sqlite:/// 开头的数据库地址。",
            details={"database_url": database_url},
        )
    return Path(database_url[len(prefix) :])


def ensure_database_initialized() -> None:
    """
    初始化数据库。
    这是什么：
    - 阶段 1 的数据库建表入口。
    做什么：
    - 确保数据库文件目录存在，并执行核心表建表语句。
    为什么这么做：
    - 当前不依赖 ORM 和迁移工具，先让持久化底座跑起来。
    """
    database_path = _resolve_sqlite_path(get_database_url())
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    获取数据库连接。
    这是什么：
    - SQLite 连接上下文管理器。
    做什么：
    - 保证调用方总能在建表完成后拿到可用连接，并自动提交和关闭。
    为什么这么做：
    - 简单的上下文封装对初学者更容易理解，也能减少忘记提交和关闭的错误。
    """
    ensure_database_initialized()
    database_path = _resolve_sqlite_path(get_database_url())
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except sqlite3.Error as error:
        raise PersistenceError("数据库操作失败。", details={"reason": str(error)}) from error
    finally:
        connection.close()
