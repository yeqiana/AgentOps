"""
SQLite Repository 实现。
这是什么：
- 这是领域仓储接口在 SQLite 上的最小实现。
做什么：
- 提供用户、会话、消息、资产的读写能力。
为什么这么做：
- 现在先把最小状态底座打通，后续再替换成 ORM 或更复杂的数据库实现。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.models import AssetRecord, MessageRecord, SessionRecord, TaskRecord, ToolResultRecord, UserRecord
from app.infrastructure.persistence.database import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteUserRepository:
    def get_or_create(self, user_name: str) -> UserRecord:
        with get_connection() as connection:
            existing = connection.execute(
                "SELECT id, user_name, created_at FROM users WHERE user_name = ?",
                (user_name,),
            ).fetchone()
            if existing:
                return dict(existing)

            user = {
                "id": f"user_{uuid.uuid4().hex}",
                "user_name": user_name,
                "created_at": _now_iso(),
            }
            connection.execute(
                "INSERT INTO users (id, user_name, created_at) VALUES (?, ?, ?)",
                (user["id"], user["user_name"], user["created_at"]),
            )
            return user

    def get_by_id(self, user_id: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, user_name, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None


class SQLiteSessionRepository:
    def create(self, user_id: str, session_id: str, title: str) -> SessionRecord:
        session = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "last_trace_id": "",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO sessions (
                    id, user_id, title, last_trace_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["id"],
                    session["user_id"],
                    session["title"],
                    session["last_trace_id"],
                    session["created_at"],
                    session["updated_at"],
                ),
            )
            row = connection.execute(
                """
                SELECT id, user_id, title, last_trace_id, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return dict(row)

    def get_by_id(self, session_id: str) -> SessionRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, user_id, title, last_trace_id, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_last_trace(self, session_id: str, trace_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE sessions SET last_trace_id = ?, updated_at = ? WHERE id = ?",
                (trace_id, _now_iso(), session_id),
            )

    def list_sessions(self, limit: int = 20, offset: int = 0) -> list[SessionRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, title, last_trace_id, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
                OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteMessageRepository:
    def create(self, message: MessageRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO messages (id, session_id, turn_id, trace_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    message["session_id"],
                    message["turn_id"],
                    message["trace_id"],
                    message["role"],
                    message["content"],
                    message["created_at"],
                ),
            )

    def list_by_session(self, session_id: str) -> list[MessageRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, turn_id, trace_id, role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteAssetRepository:
    def create_many(self, assets: list[AssetRecord]) -> None:
        if not assets:
            return
        with get_connection() as connection:
            connection.executemany(
                """
                INSERT INTO assets (
                    id, session_id, turn_id, trace_id, kind, name, source,
                    content, storage_mode, locator, mime_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        asset["id"],
                        asset["session_id"],
                        asset["turn_id"],
                        asset["trace_id"],
                        asset["kind"],
                        asset["name"],
                        asset["source"],
                        asset["content"],
                        asset["storage_mode"],
                        asset["locator"],
                        asset["mime_type"],
                        asset["created_at"],
                    )
                    for asset in assets
                ],
            )

    def list_by_session(self, session_id: str) -> list[AssetRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, turn_id, trace_id, kind, name, source,
                       content, storage_mode, locator, mime_type, created_at
                FROM assets
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, asset_id: str) -> AssetRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, turn_id, trace_id, kind, name, source,
                       content, storage_mode, locator, mime_type, created_at
                FROM assets
                WHERE id = ?
                """,
                (asset_id,),
            ).fetchone()
            return dict(row) if row else None


class SQLiteTaskRepository:
    def create_or_update(self, task: TaskRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, session_id, turn_id, trace_id, status, user_input, plan,
                    answer, tool_count, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    session_id = excluded.session_id,
                    turn_id = excluded.turn_id,
                    trace_id = excluded.trace_id,
                    status = excluded.status,
                    user_input = excluded.user_input,
                    plan = excluded.plan,
                    answer = excluded.answer,
                    tool_count = excluded.tool_count,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    task["id"],
                    task["session_id"],
                    task["turn_id"],
                    task["trace_id"],
                    task["status"],
                    task["user_input"],
                    task["plan"],
                    task["answer"],
                    task["tool_count"],
                    task["error_message"],
                    task["created_at"],
                    task["updated_at"],
                ),
            )

    def get_by_id(self, task_id: str) -> TaskRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, turn_id, trace_id, status, user_input, plan,
                       answer, tool_count, error_message, created_at, updated_at
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_by_session(self, session_id: str, limit: int = 20, offset: int = 0) -> list[TaskRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, turn_id, trace_id, status, user_input, plan,
                       answer, tool_count, error_message, created_at, updated_at
                FROM tasks
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                OFFSET ?
                """,
                (session_id, limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_tasks(
        self,
        *,
        status: str | None = None,
        session_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TaskRecord]:
        query = """
            SELECT id, session_id, turn_id, trace_id, status, user_input, plan,
                   answer, tool_count, error_message, created_at, updated_at
            FROM tasks
        """
        clauses: list[str] = []
        parameters: list[object] = []

        if status:
            clauses.append("status = ?")
            parameters.append(status)
        if session_id:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        parameters.extend([limit, offset])

        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]


class SQLiteToolResultRepository:
    def replace_for_task(self, task_id: str, results: list[ToolResultRecord]) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM tool_results WHERE task_id = ?", (task_id,))
            if not results:
                return
            connection.executemany(
                """
                INSERT INTO tool_results (
                    id, task_id, session_id, turn_id, trace_id, tool_name,
                    success, exit_code, stdout, stderr, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        result["id"],
                        result["task_id"],
                        result["session_id"],
                        result["turn_id"],
                        result["trace_id"],
                        result["tool_name"],
                        1 if result["success"] else 0,
                        result["exit_code"],
                        result["stdout"],
                        result["stderr"],
                        result["created_at"],
                    )
                    for result in results
                ],
            )

    def list_by_task(self, task_id: str) -> list[ToolResultRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, task_id, session_id, turn_id, trace_id, tool_name,
                       success, exit_code, stdout, stderr, created_at
                FROM tool_results
                WHERE task_id = ?
                ORDER BY created_at ASC
                """,
                (task_id,),
            ).fetchall()
            return [
                {
                    **dict(row),
                    "success": bool(row["success"]),
                }
                for row in rows
            ]
