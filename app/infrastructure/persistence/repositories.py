"""
SQLite Repository 实现。

这是什么：
- 领域仓储接口在 SQLite 上的最小实现。

做什么：
- 提供系统用户、会话、消息、资产、任务、工具结果和请求追踪的读写能力。

为什么这么做：
- 数据库命名规范、审计字段和索引策略都需要在仓储层被稳定消费。
- 当前阶段先用显式 SQL 保持结构透明，便于后续替换 ORM 或 PostgreSQL 实现。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.models import (
    AlertEventRecord,
    AuthPermissionRecord,
    AuthRolePermissionRecord,
    AuthRoleRecord,
    AuthSubjectRoleRecord,
    AssetRecord,
    MessageRecord,
    RouteDecisionRecord,
    RuntimeConfigRecord,
    SessionRecord,
    TaskEventRecord,
    TaskRecord,
    ToolResultRecord,
    TraceRecord,
    UserRecord,
    WorkflowRoleRecord,
)
from app.infrastructure.persistence.database import (
    TABLE_BIZ_ASSET,
    TABLE_BIZ_MESSAGE,
    TABLE_BIZ_ROUTE_DECISION,
    TABLE_BIZ_SESSION,
    TABLE_BIZ_TASK,
    TABLE_BIZ_TASK_EVENT,
    TABLE_BIZ_TOOL_RESULT,
    TABLE_SYS_RUNTIME_CONFIG,
    TABLE_SYS_REQUEST_TRACE,
    TABLE_SYS_USER,
    TABLE_SYS_WORKFLOW_ROLE,
    TABLE_SYS_ALERT_EVENT,
    TABLE_SYS_AUTH_PERMISSION,
    TABLE_SYS_AUTH_ROLE,
    TABLE_SYS_AUTH_ROLE_PERMISSION,
    TABLE_SYS_AUTH_SUBJECT_ROLE,
    get_connection,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteUserRepository:
    def get_or_create(self, user_name: str) -> UserRecord:
        with get_connection() as connection:
            existing = connection.execute(
                f"""
                SELECT id, user_name, created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_USER}
                WHERE user_name = ?
                """,
                (user_name,),
            ).fetchone()
            if existing:
                return dict(existing)

            timestamp = _now_iso()
            user = {
                "id": f"user_{uuid.uuid4().hex}",
                "user_name": user_name,
                "created_by": user_name,
                "updated_by": user_name,
                "created_at": timestamp,
                "updated_at": timestamp,
                "ext_data1": "",
                "ext_data2": "",
                "ext_data3": "",
                "ext_data4": "",
                "ext_data5": "",
            }
            connection.execute(
                f"""
                INSERT INTO {TABLE_SYS_USER} (
                    id, user_name, created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    user["user_name"],
                    user["created_by"],
                    user["updated_by"],
                    user["created_at"],
                    user["updated_at"],
                    user["ext_data1"],
                    user["ext_data2"],
                    user["ext_data3"],
                    user["ext_data4"],
                    user["ext_data5"],
                ),
            )
            return user

    def get_by_id(self, user_id: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, user_name, created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_USER}
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
            return dict(row) if row else None


class SQLiteSessionRepository:
    def create(self, user_id: str, session_id: str, title: str) -> SessionRecord:
        timestamp = _now_iso()
        session = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "last_trace_id": "",
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT OR IGNORE INTO {TABLE_BIZ_SESSION} (
                    id, user_id, title, last_trace_id, created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["id"],
                    session["user_id"],
                    session["title"],
                    session["last_trace_id"],
                    session["created_by"],
                    session["updated_by"],
                    session["created_at"],
                    session["updated_at"],
                    session["ext_data1"],
                    session["ext_data2"],
                    session["ext_data3"],
                    session["ext_data4"],
                    session["ext_data5"],
                ),
            )
            row = connection.execute(
                f"""
                SELECT id, user_id, title, last_trace_id, created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_SESSION}
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return dict(row)

    def get_by_id(self, session_id: str) -> SessionRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, user_id, title, last_trace_id, created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_SESSION}
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_last_trace(self, session_id: str, trace_id: str, *, updated_by: str = "system") -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE {TABLE_BIZ_SESSION}
                SET last_trace_id = ?, updated_at = ?, updated_by = ?
                WHERE id = ?
                """,
                (trace_id, _now_iso(), updated_by, session_id),
            )

    def list_sessions(self, limit: int = 20, offset: int = 0) -> list[SessionRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, user_id, title, last_trace_id, created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_SESSION}
                ORDER BY updated_at DESC
                LIMIT ?
                OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteRuntimeConfigRepository:
    def list_configs(self, *, scope: str | None = None) -> list[RuntimeConfigRecord]:
        query = f"""
            SELECT id, config_scope, config_key, config_value, value_type, config_source, description,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_SYS_RUNTIME_CONFIG}
        """
        parameters: list[object] = []
        if scope:
            query += " WHERE config_scope = ?"
            parameters.append(scope)
        query += " ORDER BY config_scope ASC, config_key ASC"
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]

    def get_config(self, *, scope: str, key: str) -> RuntimeConfigRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, config_scope, config_key, config_value, value_type, config_source, description,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_RUNTIME_CONFIG}
                WHERE config_scope = ? AND config_key = ?
                """,
                (scope, key),
            ).fetchone()
            return dict(row) if row else None

    def upsert_config(
        self,
        *,
        scope: str,
        key: str,
        value: str,
        value_type: str,
        description: str,
        updated_by: str,
    ) -> RuntimeConfigRecord:
        timestamp = _now_iso()
        config_id = f"runtime_config_{uuid.uuid4().hex}"
        with get_connection() as connection:
            existing = connection.execute(
                f"SELECT id, created_at, created_by FROM {TABLE_SYS_RUNTIME_CONFIG} WHERE config_scope = ? AND config_key = ?",
                (scope, key),
            ).fetchone()
            if existing:
                config_id = existing["id"]
                created_at = existing["created_at"]
                created_by = existing["created_by"]
            else:
                created_at = timestamp
                created_by = updated_by

            connection.execute(
                f"""
                INSERT INTO {TABLE_SYS_RUNTIME_CONFIG} (
                    id, config_scope, config_key, config_value, value_type, config_source, description,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(config_scope, config_key) DO UPDATE SET
                    config_value = excluded.config_value,
                    value_type = excluded.value_type,
                    config_source = excluded.config_source,
                    description = excluded.description,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at
                """,
                (
                    config_id,
                    scope,
                    key,
                    value,
                    value_type,
                    "db_override",
                    description,
                    created_by,
                    updated_by,
                    created_at,
                    timestamp,
                    "",
                    "",
                    "",
                    "",
                    "",
                ),
            )
            row = connection.execute(
                f"""
                SELECT id, config_scope, config_key, config_value, value_type, config_source, description,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_RUNTIME_CONFIG}
                WHERE config_scope = ? AND config_key = ?
                """,
                (scope, key),
            ).fetchone()
            return dict(row)


class SQLiteWorkflowRoleRepository:
    def list_roles(self, *, only_enabled: bool = False) -> list[WorkflowRoleRecord]:
        query = f"""
            SELECT id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_SYS_WORKFLOW_ROLE}
        """
        parameters: list[object] = []
        if only_enabled:
            query += " WHERE is_enabled = 1"
        query += " ORDER BY sort_order ASC, role_key ASC"
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [{**dict(row), "is_enabled": bool(row["is_enabled"])} for row in rows]

    def get_by_role_key(self, role_key: str) -> WorkflowRoleRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_WORKFLOW_ROLE}
                WHERE role_key = ?
                """,
                (role_key,),
            ).fetchone()
            return ({**dict(row), "is_enabled": bool(row["is_enabled"])}) if row else None

    def upsert_role(
        self,
        *,
        role_key: str,
        role_name: str,
        role_instruction: str,
        is_enabled: bool,
        sort_order: int,
        role_type: str,
        description: str,
        updated_by: str,
    ) -> WorkflowRoleRecord:
        timestamp = _now_iso()
        role_id = f"workflow_role_{uuid.uuid4().hex}"
        with get_connection() as connection:
            existing = connection.execute(
                f"SELECT id, created_at, created_by FROM {TABLE_SYS_WORKFLOW_ROLE} WHERE role_key = ?",
                (role_key,),
            ).fetchone()
            if existing:
                role_id = existing["id"]
                created_at = existing["created_at"]
                created_by = existing["created_by"]
            else:
                created_at = timestamp
                created_by = updated_by

            connection.execute(
                f"""
                INSERT INTO {TABLE_SYS_WORKFLOW_ROLE} (
                    id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(role_key) DO UPDATE SET
                    role_name = excluded.role_name,
                    role_instruction = excluded.role_instruction,
                    is_enabled = excluded.is_enabled,
                    sort_order = excluded.sort_order,
                    role_type = excluded.role_type,
                    description = excluded.description,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at
                """,
                (
                    role_id,
                    role_key,
                    role_name,
                    role_instruction,
                    1 if is_enabled else 0,
                    sort_order,
                    role_type,
                    description,
                    created_by,
                    updated_by,
                    created_at,
                    timestamp,
                    "",
                    "",
                    "",
                    "",
                    "",
                ),
            )
            row = connection.execute(
                f"""
                SELECT id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_WORKFLOW_ROLE}
                WHERE role_key = ?
                """,
                (role_key,),
            ).fetchone()
            return {**dict(row), "is_enabled": bool(row["is_enabled"])}


class SQLiteAlertEventRepository:
    def create(self, alert: AlertEventRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_SYS_ALERT_EVENT} (
                    id, trace_id, source_type, source_name, severity, event_code, message, payload_json,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["id"],
                    alert["trace_id"],
                    alert["source_type"],
                    alert["source_name"],
                    alert["severity"],
                    alert["event_code"],
                    alert["message"],
                    alert["payload_json"],
                    alert["created_by"],
                    alert["updated_by"],
                    alert["created_at"],
                    alert["updated_at"],
                    alert["ext_data1"],
                    alert["ext_data2"],
                    alert["ext_data3"],
                    alert["ext_data4"],
                    alert["ext_data5"],
                ),
            )

    def list_alerts(
        self,
        *,
        severity: str | None = None,
        source_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AlertEventRecord]:
        query = f"""
            SELECT id, trace_id, source_type, source_name, severity, event_code, message, payload_json,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_SYS_ALERT_EVENT}
        """
        clauses: list[str] = []
        parameters: list[object] = []
        if severity:
            clauses.append("severity = ?")
            parameters.append(severity)
        if source_type:
            clauses.append("source_type = ?")
            parameters.append(source_type)
        if trace_id:
            clauses.append("trace_id = ?")
            parameters.append(trace_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        parameters.extend([limit, offset])
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, alert_id: str) -> AlertEventRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, trace_id, source_type, source_name, severity, event_code, message, payload_json,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_ALERT_EVENT}
                WHERE id = ?
                """,
                (alert_id,),
            ).fetchone()
            return dict(row) if row else None


class SQLiteAuthRoleRepository:
    def list_roles(self, *, only_enabled: bool = False) -> list[AuthRoleRecord]:
        query = f"""
            SELECT id, role_key, role_name, description, is_enabled,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_SYS_AUTH_ROLE}
        """
        parameters: list[object] = []
        if only_enabled:
            query += " WHERE is_enabled = 1"
        query += " ORDER BY role_key ASC"
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [{**dict(row), "is_enabled": bool(row["is_enabled"])} for row in rows]


class SQLiteAuthPermissionRepository:
    def list_permissions(self) -> list[AuthPermissionRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, permission_key, permission_name, description,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_AUTH_PERMISSION}
                ORDER BY permission_key ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteAuthRolePermissionRepository:
    def list_by_role_keys(self, role_keys: list[str]) -> list[AuthRolePermissionRecord]:
        if not role_keys:
            return []
        placeholders = ", ".join(["?"] * len(role_keys))
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, role_key, permission_key,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_AUTH_ROLE_PERMISSION}
                WHERE role_key IN ({placeholders})
                ORDER BY role_key ASC, permission_key ASC
                """,
                tuple(role_keys),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteAuthSubjectRoleRepository:
    def list_by_subject(self, auth_subject: str) -> list[AuthSubjectRoleRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, auth_subject, role_key,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_AUTH_SUBJECT_ROLE}
                WHERE auth_subject = ?
                ORDER BY role_key ASC
                """,
                (auth_subject,),
            ).fetchall()
            return [dict(row) for row in rows]

    def replace_subject_roles(self, *, auth_subject: str, role_keys: list[str], updated_by: str) -> list[AuthSubjectRoleRecord]:
        timestamp = _now_iso()
        with get_connection() as connection:
            connection.execute(f"DELETE FROM {TABLE_SYS_AUTH_SUBJECT_ROLE} WHERE auth_subject = ?", (auth_subject,))
            if not role_keys:
                return []
            rows_to_insert = []
            for role_key in sorted(set(role_keys)):
                rows_to_insert.append(
                    (
                        f"auth_subject_role_{uuid.uuid4().hex}",
                        auth_subject,
                        role_key,
                        updated_by,
                        updated_by,
                        timestamp,
                        timestamp,
                        "",
                        "",
                        "",
                        "",
                        "",
                    )
                )
            connection.executemany(
                f"""
                INSERT INTO {TABLE_SYS_AUTH_SUBJECT_ROLE} (
                    id, auth_subject, role_key,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows_to_insert,
            )
            rows = connection.execute(
                f"""
                SELECT id, auth_subject, role_key,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_AUTH_SUBJECT_ROLE}
                WHERE auth_subject = ?
                ORDER BY role_key ASC
                """,
                (auth_subject,),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteMessageRepository:
    def create(self, message: MessageRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_BIZ_MESSAGE} (
                    id, session_id, turn_id, trace_id, role, content,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    message["session_id"],
                    message["turn_id"],
                    message["trace_id"],
                    message["role"],
                    message["content"],
                    message["created_by"],
                    message["updated_by"],
                    message["created_at"],
                    message["updated_at"],
                    message["ext_data1"],
                    message["ext_data2"],
                    message["ext_data3"],
                    message["ext_data4"],
                    message["ext_data5"],
                ),
            )

    def list_by_session(self, session_id: str) -> list[MessageRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, role, content,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_MESSAGE}
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_by_turn(self, session_id: str, turn_id: str) -> list[MessageRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, role, content,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_MESSAGE}
                WHERE session_id = ? AND turn_id = ?
                ORDER BY created_at ASC
                """,
                (session_id, turn_id),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteAssetRepository:
    def create_many(self, assets: list[AssetRecord]) -> None:
        if not assets:
            return
        with get_connection() as connection:
            connection.executemany(
                f"""
                INSERT INTO {TABLE_BIZ_ASSET} (
                    id, session_id, turn_id, trace_id, kind, name, source,
                    content, storage_mode, locator, mime_type,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        asset["created_by"],
                        asset["updated_by"],
                        asset["created_at"],
                        asset["updated_at"],
                        asset["ext_data1"],
                        asset["ext_data2"],
                        asset["ext_data3"],
                        asset["ext_data4"],
                        asset["ext_data5"],
                    )
                    for asset in assets
                ],
            )

    def list_by_session(self, session_id: str) -> list[AssetRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, kind, name, source,
                       content, storage_mode, locator, mime_type,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_ASSET}
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_by_turn(self, session_id: str, turn_id: str) -> list[AssetRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, kind, name, source,
                       content, storage_mode, locator, mime_type,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_ASSET}
                WHERE session_id = ? AND turn_id = ?
                ORDER BY created_at ASC
                """,
                (session_id, turn_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, asset_id: str) -> AssetRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, kind, name, source,
                       content, storage_mode, locator, mime_type,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_ASSET}
                WHERE id = ?
                """,
                (asset_id,),
            ).fetchone()
            return dict(row) if row else None


class SQLiteTaskRepository:
    def create_or_update(self, task: TaskRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_BIZ_TASK} (
                    id, session_id, turn_id, trace_id, status, user_input, execution_mode, protocol_summary, route_name,
                    route_reason, plan, debate_summary, arbitration_summary, answer,
                    critic_summary, review_status, review_summary, tool_count,
                    error_message, created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    session_id = excluded.session_id,
                    turn_id = excluded.turn_id,
                    trace_id = excluded.trace_id,
                    status = excluded.status,
                    user_input = excluded.user_input,
                    execution_mode = excluded.execution_mode,
                    protocol_summary = excluded.protocol_summary,
                    route_name = excluded.route_name,
                    route_reason = excluded.route_reason,
                    plan = excluded.plan,
                    debate_summary = excluded.debate_summary,
                    arbitration_summary = excluded.arbitration_summary,
                    answer = excluded.answer,
                    critic_summary = excluded.critic_summary,
                    review_status = excluded.review_status,
                    review_summary = excluded.review_summary,
                    tool_count = excluded.tool_count,
                    error_message = excluded.error_message,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at,
                    ext_data1 = excluded.ext_data1,
                    ext_data2 = excluded.ext_data2,
                    ext_data3 = excluded.ext_data3,
                    ext_data4 = excluded.ext_data4,
                    ext_data5 = excluded.ext_data5
                """,
                (
                    task["id"],
                    task["session_id"],
                    task["turn_id"],
                    task["trace_id"],
                    task["status"],
                    task["user_input"],
                    task["execution_mode"],
                    task["protocol_summary"],
                    task["route_name"],
                    task["route_reason"],
                    task["plan"],
                    task["debate_summary"],
                    task["arbitration_summary"],
                    task["answer"],
                    task["critic_summary"],
                    task["review_status"],
                    task["review_summary"],
                    task["tool_count"],
                    task["error_message"],
                    task["created_by"],
                    task["updated_by"],
                    task["created_at"],
                    task["updated_at"],
                    task["ext_data1"],
                    task["ext_data2"],
                    task["ext_data3"],
                    task["ext_data4"],
                    task["ext_data5"],
                ),
            )

    def get_by_id(self, task_id: str) -> TaskRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, status, user_input, execution_mode, protocol_summary, route_name,
                       route_reason, plan, debate_summary, arbitration_summary, answer,
                       critic_summary, review_status, review_summary, tool_count, error_message,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_TASK}
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_status(
        self,
        task_id: str,
        *,
        status: str,
        error_message: str,
        updated_by: str,
    ) -> TaskRecord | None:
        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE {TABLE_BIZ_TASK}
                SET status = ?, error_message = ?, updated_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, error_message, updated_by, _now_iso(), task_id),
            )
            row = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, status, user_input, execution_mode, protocol_summary, route_name,
                       route_reason, plan, debate_summary, arbitration_summary, answer,
                       critic_summary, review_status, review_summary, tool_count, error_message,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_TASK}
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_by_session(self, session_id: str, limit: int = 20, offset: int = 0) -> list[TaskRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, session_id, turn_id, trace_id, status, user_input, execution_mode, protocol_summary, route_name,
                       route_reason, plan, debate_summary, arbitration_summary, answer,
                       critic_summary, review_status, review_summary, tool_count, error_message,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_TASK}
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
        query = f"""
            SELECT id, session_id, turn_id, trace_id, status, user_input, execution_mode, protocol_summary, route_name,
                   route_reason, plan, debate_summary, arbitration_summary, answer,
                   critic_summary, review_status, review_summary, tool_count, error_message,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_BIZ_TASK}
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

    def list_status_stats(
        self,
        *,
        session_id: str | None = None,
    ) -> list[dict[str, object]]:
        """
        聚合任务状态统计。

        What this is:
        - 面向控制台和运维视图的任务状态聚合查询。

        What it does:
        - 按任务状态分组统计数量，并返回该状态最近一次更新时间。

        Why this is done this way:
        - 前端和运维接口更需要“状态分布”而不是扫描全量任务后自行聚合，
          把聚合逻辑下沉到仓储层可以减少重复查询和无效传输。
        """
        query = f"""
            SELECT
                status,
                COUNT(*) AS task_count,
                MAX(updated_at) AS last_updated_at
            FROM {TABLE_BIZ_TASK}
        """
        parameters: list[object] = []
        if session_id:
            query += " WHERE session_id = ?"
            parameters.append(session_id)
        query += """
            GROUP BY status
            ORDER BY task_count DESC, last_updated_at DESC
        """
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]


class SQLiteTaskEventRepository:
    def create(self, event: TaskEventRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_BIZ_TASK_EVENT} (
                    id, task_id, session_id, turn_id, trace_id, event_type, event_message, event_payload_json,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["id"],
                    event["task_id"],
                    event["session_id"],
                    event["turn_id"],
                    event["trace_id"],
                    event["event_type"],
                    event["event_message"],
                    event["event_payload_json"],
                    event["created_by"],
                    event["updated_by"],
                    event["created_at"],
                    event["updated_at"],
                    event["ext_data1"],
                    event["ext_data2"],
                    event["ext_data3"],
                    event["ext_data4"],
                    event["ext_data5"],
                ),
            )

    def list_by_task(self, task_id: str, *, limit: int = 100, offset: int = 0) -> list[TaskEventRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, task_id, session_id, turn_id, trace_id, event_type, event_message, event_payload_json,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_TASK_EVENT}
                WHERE task_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                OFFSET ?
                """,
                (task_id, limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]


class SQLiteToolResultRepository:
    def replace_for_task(self, task_id: str, results: list[ToolResultRecord]) -> None:
        with get_connection() as connection:
            connection.execute(f"DELETE FROM {TABLE_BIZ_TOOL_RESULT} WHERE task_id = ?", (task_id,))
            if not results:
                return
            connection.executemany(
                f"""
                INSERT INTO {TABLE_BIZ_TOOL_RESULT} (
                    id, task_id, session_id, turn_id, trace_id, tool_name,
                    success, exit_code, stdout, stderr,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        result["created_by"],
                        result["updated_by"],
                        result["created_at"],
                        result["updated_at"],
                        result["ext_data1"],
                        result["ext_data2"],
                        result["ext_data3"],
                        result["ext_data4"],
                        result["ext_data5"],
                    )
                    for result in results
                ],
            )

    def list_by_task(self, task_id: str) -> list[ToolResultRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, task_id, session_id, turn_id, trace_id, tool_name,
                       success, exit_code, stdout, stderr,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_TOOL_RESULT}
                WHERE task_id = ?
                ORDER BY created_at ASC
                """,
                (task_id,),
            ).fetchall()
            return [{**dict(row), "success": bool(row["success"])} for row in rows]


class SQLiteRouteDecisionRepository:
    def replace_for_task(self, task_id: str, decisions: list[RouteDecisionRecord]) -> None:
        with get_connection() as connection:
            connection.execute(f"DELETE FROM {TABLE_BIZ_ROUTE_DECISION} WHERE task_id = ?", (task_id,))
            if not decisions:
                return
            connection.executemany(
                f"""
                INSERT INTO {TABLE_BIZ_ROUTE_DECISION} (
                    id, task_id, session_id, turn_id, trace_id, route_name, route_reason, route_source,
                    created_by, updated_by, created_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        decision["id"],
                        decision["task_id"],
                        decision["session_id"],
                        decision["turn_id"],
                        decision["trace_id"],
                        decision["route_name"],
                        decision["route_reason"],
                        decision["route_source"],
                        decision["created_by"],
                        decision["updated_by"],
                        decision["created_at"],
                        decision["updated_at"],
                        decision["ext_data1"],
                        decision["ext_data2"],
                        decision["ext_data3"],
                        decision["ext_data4"],
                        decision["ext_data5"],
                    )
                    for decision in decisions
                ],
            )

    def list_by_task(self, task_id: str) -> list[RouteDecisionRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, task_id, session_id, turn_id, trace_id, route_name, route_reason, route_source,
                       created_by, updated_by, created_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_BIZ_ROUTE_DECISION}
                WHERE task_id = ?
                ORDER BY created_at ASC
                """,
                (task_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_decisions(
        self,
        *,
        task_id: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RouteDecisionRecord]:
        query = f"""
            SELECT id, task_id, session_id, turn_id, trace_id, route_name, route_reason, route_source,
                   created_by, updated_by, created_at, updated_at,
                   ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            FROM {TABLE_BIZ_ROUTE_DECISION}
        """
        clauses: list[str] = []
        parameters: list[object] = []
        if task_id:
            clauses.append("task_id = ?")
            parameters.append(task_id)
        if session_id:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        if trace_id:
            clauses.append("trace_id = ?")
            parameters.append(trace_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        parameters.extend([limit, offset])
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]

    def list_stats(
        self,
        *,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        filters: list[str] = []
        parameters: list[object] = []
        if session_id:
            filters.append("session_id = ?")
            parameters.append(session_id)
        if trace_id:
            filters.append("trace_id = ?")
            parameters.append(trace_id)
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        query = f"""
            WITH filtered AS (
                SELECT id, task_id, session_id, trace_id, route_name, route_source, created_at
                FROM {TABLE_BIZ_ROUTE_DECISION}
                {where_clause}
            ),
            grouped AS (
                SELECT route_name, route_source, COUNT(*) AS decision_count, MAX(created_at) AS last_decided_at
                FROM filtered
                GROUP BY route_name, route_source
            )
            SELECT
                grouped.route_name,
                grouped.route_source,
                grouped.decision_count,
                grouped.last_decided_at,
                COALESCE(filtered.trace_id, '') AS last_trace_id,
                COALESCE(filtered.task_id, '') AS last_task_id
            FROM grouped
            LEFT JOIN filtered
                ON filtered.route_name = grouped.route_name
               AND filtered.route_source = grouped.route_source
               AND filtered.created_at = grouped.last_decided_at
            ORDER BY grouped.decision_count DESC, grouped.last_decided_at DESC
            LIMIT ?
            OFFSET ?
        """
        parameters.extend([limit, offset])
        with get_connection() as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
            return [dict(row) for row in rows]


class SQLiteTraceRepository:
    def create_or_update(self, trace: TraceRecord) -> None:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO {TABLE_SYS_REQUEST_TRACE} (
                    trace_id, request_id, method, path, auth_subject, auth_type,
                    session_id, turn_id, task_id, status_code, error_code,
                    idempotency_key, rate_limited, created_by, updated_by,
                    created_at, started_at, updated_at,
                    ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trace_id) DO UPDATE SET
                    request_id = excluded.request_id,
                    method = excluded.method,
                    path = excluded.path,
                    auth_subject = excluded.auth_subject,
                    auth_type = excluded.auth_type,
                    session_id = excluded.session_id,
                    turn_id = excluded.turn_id,
                    task_id = excluded.task_id,
                    status_code = excluded.status_code,
                    error_code = excluded.error_code,
                    idempotency_key = excluded.idempotency_key,
                    rate_limited = excluded.rate_limited,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at,
                    ext_data1 = excluded.ext_data1,
                    ext_data2 = excluded.ext_data2,
                    ext_data3 = excluded.ext_data3,
                    ext_data4 = excluded.ext_data4,
                    ext_data5 = excluded.ext_data5
                """,
                (
                    trace["trace_id"],
                    trace["request_id"],
                    trace["method"],
                    trace["path"],
                    trace["auth_subject"],
                    trace["auth_type"],
                    trace["session_id"],
                    trace["turn_id"],
                    trace["task_id"],
                    trace["status_code"],
                    trace["error_code"],
                    trace["idempotency_key"],
                    1 if trace["rate_limited"] else 0,
                    trace["created_by"],
                    trace["updated_by"],
                    trace["created_at"],
                    trace["started_at"],
                    trace["updated_at"],
                    trace["ext_data1"],
                    trace["ext_data2"],
                    trace["ext_data3"],
                    trace["ext_data4"],
                    trace["ext_data5"],
                ),
            )

    def get_by_trace_id(self, trace_id: str) -> TraceRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT trace_id, request_id, method, path, auth_subject, auth_type,
                       session_id, turn_id, task_id, status_code, error_code,
                       idempotency_key, rate_limited, created_by, updated_by,
                       created_at, started_at, updated_at,
                       ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
                FROM {TABLE_SYS_REQUEST_TRACE}
                WHERE trace_id = ?
                """,
                (trace_id,),
            ).fetchone()
            if not row:
                return None
            return {**dict(row), "rate_limited": bool(row["rate_limited"])}
