"""
SQLite persistence bootstrap.

What this is:
- The shared database initialization module for the current runtime.

What it does:
- Resolves the SQLite location.
- Creates system and business tables.
- Applies compatibility migrations from earlier table names.
- Creates indexes and records the active schema version.

Why this is done this way:
- Stage-2 governance now needs a stable schema contract, not ad-hoc table
  creation spread across repositories.
- The project still uses SQLite, so schema rules, audit fields, and migration
  compatibility need to be enforced centrally before PostgreSQL evolution.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.domain.errors import PersistenceError


DEFAULT_DATABASE_URL = "sqlite:///data/agent.db"
SCHEMA_VERSION = "2026_04_08_05"

TABLE_SYS_SCHEMA_VERSION = "sys_schema_version"
TABLE_SYS_USER = "sys_user"
TABLE_SYS_REQUEST_TRACE = "sys_request_trace"
TABLE_SYS_RUNTIME_CONFIG = "sys_runtime_config"
TABLE_SYS_WORKFLOW_ROLE = "sys_workflow_role"
TABLE_SYS_ALERT_EVENT = "sys_alert_event"

TABLE_BIZ_SESSION = "biz_session"
TABLE_BIZ_MESSAGE = "biz_message"
TABLE_BIZ_ASSET = "biz_asset"
TABLE_BIZ_TASK = "biz_task"
TABLE_BIZ_TOOL_RESULT = "biz_tool_result"

AUDIT_FIELD_SQL = """
        created_by TEXT NOT NULL,
        updated_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        ext_data1 TEXT NOT NULL DEFAULT '',
        ext_data2 TEXT NOT NULL DEFAULT '',
        ext_data3 TEXT NOT NULL DEFAULT '',
        ext_data4 TEXT NOT NULL DEFAULT '',
        ext_data5 TEXT NOT NULL DEFAULT ''
"""

SCHEMA_STATEMENTS = (
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_SCHEMA_VERSION} (
        id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL UNIQUE,
        version_note TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_USER} (
        id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL UNIQUE,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_RUNTIME_CONFIG} (
        id TEXT PRIMARY KEY,
        config_scope TEXT NOT NULL,
        config_key TEXT NOT NULL,
        config_value TEXT NOT NULL,
        value_type TEXT NOT NULL,
        config_source TEXT NOT NULL,
        description TEXT NOT NULL,
{AUDIT_FIELD_SQL},
        UNIQUE(config_scope, config_key)
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_WORKFLOW_ROLE} (
        id TEXT PRIMARY KEY,
        role_key TEXT NOT NULL UNIQUE,
        role_name TEXT NOT NULL,
        role_instruction TEXT NOT NULL,
        is_enabled INTEGER NOT NULL,
        sort_order INTEGER NOT NULL,
        role_type TEXT NOT NULL,
        description TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_ALERT_EVENT} (
        id TEXT PRIMARY KEY,
        trace_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_name TEXT NOT NULL,
        severity TEXT NOT NULL,
        event_code TEXT NOT NULL,
        message TEXT NOT NULL,
        payload_json TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_BIZ_SESSION} (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        last_trace_id TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_BIZ_MESSAGE} (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_BIZ_ASSET} (
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
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_BIZ_TASK} (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        status TEXT NOT NULL,
        user_input TEXT NOT NULL,
        route_name TEXT NOT NULL DEFAULT '',
        route_reason TEXT NOT NULL DEFAULT '',
        plan TEXT NOT NULL,
        debate_summary TEXT NOT NULL DEFAULT '',
        arbitration_summary TEXT NOT NULL DEFAULT '',
        answer TEXT NOT NULL,
        critic_summary TEXT NOT NULL DEFAULT '',
        review_status TEXT NOT NULL DEFAULT '',
        review_summary TEXT NOT NULL DEFAULT '',
        tool_count INTEGER NOT NULL,
        error_message TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_BIZ_TOOL_RESULT} (
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
{AUDIT_FIELD_SQL}
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SYS_REQUEST_TRACE} (
        trace_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        method TEXT NOT NULL,
        path TEXT NOT NULL,
        auth_subject TEXT NOT NULL,
        auth_type TEXT NOT NULL,
        session_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        status_code INTEGER NOT NULL,
        error_code TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        rate_limited INTEGER NOT NULL,
        started_at TEXT NOT NULL,
{AUDIT_FIELD_SQL}
    )
    """,
)

INDEX_STATEMENTS = (
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_SCHEMA_VERSION}_updated_at ON {TABLE_SYS_SCHEMA_VERSION}(updated_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_RUNTIME_CONFIG}_scope_key ON {TABLE_SYS_RUNTIME_CONFIG}(config_scope, config_key)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_RUNTIME_CONFIG}_updated_at ON {TABLE_SYS_RUNTIME_CONFIG}(updated_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_WORKFLOW_ROLE}_enabled_order ON {TABLE_SYS_WORKFLOW_ROLE}(is_enabled, sort_order ASC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_ALERT_EVENT}_severity_created ON {TABLE_SYS_ALERT_EVENT}(severity, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_ALERT_EVENT}_trace_created ON {TABLE_SYS_ALERT_EVENT}(trace_id, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_ALERT_EVENT}_source_created ON {TABLE_SYS_ALERT_EVENT}(source_type, source_name, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_SESSION}_updated_at ON {TABLE_BIZ_SESSION}(updated_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_SESSION}_user_id ON {TABLE_BIZ_SESSION}(user_id, updated_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_MESSAGE}_session_turn ON {TABLE_BIZ_MESSAGE}(session_id, created_at ASC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_MESSAGE}_trace ON {TABLE_BIZ_MESSAGE}(trace_id)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_ASSET}_session_created ON {TABLE_BIZ_ASSET}(session_id, created_at ASC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_ASSET}_kind_created ON {TABLE_BIZ_ASSET}(kind, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_TASK}_session_status_updated ON {TABLE_BIZ_TASK}(session_id, status, updated_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_TASK}_trace ON {TABLE_BIZ_TASK}(trace_id)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_TASK}_created_at ON {TABLE_BIZ_TASK}(created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_TOOL_RESULT}_task_created ON {TABLE_BIZ_TOOL_RESULT}(task_id, created_at ASC)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_BIZ_TOOL_RESULT}_trace ON {TABLE_BIZ_TOOL_RESULT}(trace_id)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_REQUEST_TRACE}_task_id ON {TABLE_SYS_REQUEST_TRACE}(task_id)",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_SYS_REQUEST_TRACE}_path_status ON {TABLE_SYS_REQUEST_TRACE}(path, status_code, updated_at DESC)",
)

LEGACY_TABLE_MAPPINGS = (
    ("users", TABLE_SYS_USER),
    ("sessions", TABLE_BIZ_SESSION),
    ("messages", TABLE_BIZ_MESSAGE),
    ("assets", TABLE_BIZ_ASSET),
    ("tasks", TABLE_BIZ_TASK),
    ("tool_results", TABLE_BIZ_TOOL_RESULT),
    ("request_traces", TABLE_SYS_REQUEST_TRACE),
    ("sys_request_traces", TABLE_SYS_REQUEST_TRACE),
)

AUDIT_COLUMN_MIGRATIONS = {
    TABLE_SYS_SCHEMA_VERSION: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_SCHEMA_VERSION} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_SYS_USER: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_USER} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_SYS_RUNTIME_CONFIG: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_RUNTIME_CONFIG} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_SYS_WORKFLOW_ROLE: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_WORKFLOW_ROLE} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_SYS_ALERT_EVENT: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_ALERT_EVENT} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_BIZ_SESSION: (
        ("created_by", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_BIZ_SESSION} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_BIZ_MESSAGE: (
        ("created_by", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_BIZ_MESSAGE} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_BIZ_ASSET: (
        ("created_by", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_BIZ_ASSET} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_BIZ_TASK: (
        ("created_by", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_BIZ_TASK} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_BIZ_TOOL_RESULT: (
        ("created_by", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_BIZ_TOOL_RESULT} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
    TABLE_SYS_REQUEST_TRACE: (
        ("created_by", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN created_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("updated_by", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN updated_by TEXT NOT NULL DEFAULT 'system_migration'"),
        ("created_at", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"),
        ("updated_at", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"),
        ("ext_data1", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN ext_data1 TEXT NOT NULL DEFAULT ''"),
        ("ext_data2", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN ext_data2 TEXT NOT NULL DEFAULT ''"),
        ("ext_data3", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN ext_data3 TEXT NOT NULL DEFAULT ''"),
        ("ext_data4", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN ext_data4 TEXT NOT NULL DEFAULT ''"),
        ("ext_data5", f"ALTER TABLE {TABLE_SYS_REQUEST_TRACE} ADD COLUMN ext_data5 TEXT NOT NULL DEFAULT ''"),
    ),
}


def get_database_url() -> str:
    database_url = os.getenv("APP_DATABASE_URL", DEFAULT_DATABASE_URL).strip()
    return database_url or DEFAULT_DATABASE_URL


def _resolve_sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise PersistenceError(
            "当前阶段仅支持 sqlite:/// 开头的数据库地址。",
            details={"database_url": database_url},
        )
    return Path(database_url[len(prefix) :])


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _copy_legacy_data(
    connection: sqlite3.Connection,
    *,
    source_table: str,
    target_table: str,
    target_columns: tuple[str, ...],
    source_columns: tuple[str, ...],
    computed_values: dict[str, str] | None = None,
) -> None:
    if not _table_exists(connection, source_table) or not _table_exists(connection, target_table):
        return
    existing_count = connection.execute(f"SELECT COUNT(1) FROM {target_table}").fetchone()[0]
    if existing_count > 0:
        return

    computed_values = computed_values or {}
    select_parts: list[str] = []
    for column in target_columns:
        if column in source_columns:
            select_parts.append(column)
        elif column in computed_values:
            select_parts.append(f"{computed_values[column]} AS {column}")
        else:
            raise PersistenceError(
                "迁移旧表数据失败，缺少必要列映射。",
                details={"source_table": source_table, "target_table": target_table, "column": column},
            )

    connection.execute(
        f"INSERT INTO {target_table} ({', '.join(target_columns)}) SELECT {', '.join(select_parts)} FROM {source_table}"
    )


def _migrate_legacy_tables(connection: sqlite3.Connection) -> None:
    migration_actor = "'system_migration'"
    empty_text = "''"

    _copy_legacy_data(
        connection,
        source_table="users",
        target_table=TABLE_SYS_USER,
        target_columns=(
            "id", "user_name", "created_by", "updated_by", "created_at", "updated_at",
            "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=("id", "user_name", "created_at"),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "updated_at": "created_at",
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    _copy_legacy_data(
        connection,
        source_table="sessions",
        target_table=TABLE_BIZ_SESSION,
        target_columns=(
            "id", "user_id", "title", "last_trace_id", "created_by", "updated_by",
            "created_at", "updated_at", "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=("id", "user_id", "title", "last_trace_id", "created_at", "updated_at"),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    _copy_legacy_data(
        connection,
        source_table="messages",
        target_table=TABLE_BIZ_MESSAGE,
        target_columns=(
            "id", "session_id", "turn_id", "trace_id", "role", "content",
            "created_by", "updated_by", "created_at", "updated_at",
            "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=("id", "session_id", "turn_id", "trace_id", "role", "content", "created_at"),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "updated_at": "created_at",
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    _copy_legacy_data(
        connection,
        source_table="assets",
        target_table=TABLE_BIZ_ASSET,
        target_columns=(
            "id", "session_id", "turn_id", "trace_id", "kind", "name", "source", "content",
            "storage_mode", "locator", "mime_type", "created_by", "updated_by", "created_at", "updated_at",
            "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=(
            "id", "session_id", "turn_id", "trace_id", "kind", "name", "source", "content",
            "storage_mode", "locator", "mime_type", "created_at",
        ),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "updated_at": "created_at",
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    _copy_legacy_data(
        connection,
        source_table="tasks",
        target_table=TABLE_BIZ_TASK,
        target_columns=(
            "id", "session_id", "turn_id", "trace_id", "status", "user_input", "route_name",
            "route_reason", "plan", "debate_summary", "arbitration_summary", "answer",
            "critic_summary", "review_status", "review_summary", "tool_count", "error_message",
            "created_by", "updated_by", "created_at", "updated_at",
            "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=(
            "id", "session_id", "turn_id", "trace_id", "status", "user_input", "route_name",
            "route_reason", "plan", "debate_summary", "arbitration_summary", "answer",
            "critic_summary", "review_status", "review_summary", "tool_count", "error_message",
            "created_at", "updated_at",
        ),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    _copy_legacy_data(
        connection,
        source_table="tool_results",
        target_table=TABLE_BIZ_TOOL_RESULT,
        target_columns=(
            "id", "task_id", "session_id", "turn_id", "trace_id", "tool_name", "success", "exit_code",
            "stdout", "stderr", "created_by", "updated_by", "created_at", "updated_at",
            "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
        ),
        source_columns=(
            "id", "task_id", "session_id", "turn_id", "trace_id", "tool_name", "success", "exit_code",
            "stdout", "stderr", "created_at",
        ),
        computed_values={
            "created_by": migration_actor,
            "updated_by": migration_actor,
            "updated_at": "created_at",
            "ext_data1": empty_text,
            "ext_data2": empty_text,
            "ext_data3": empty_text,
            "ext_data4": empty_text,
            "ext_data5": empty_text,
        },
    )
    for trace_source in ("request_traces", "sys_request_traces"):
        _copy_legacy_data(
            connection,
            source_table=trace_source,
            target_table=TABLE_SYS_REQUEST_TRACE,
            target_columns=(
                "trace_id", "request_id", "method", "path", "auth_subject", "auth_type", "session_id",
                "turn_id", "task_id", "status_code", "error_code", "idempotency_key", "rate_limited",
                "created_by", "updated_by", "created_at", "started_at", "updated_at",
                "ext_data1", "ext_data2", "ext_data3", "ext_data4", "ext_data5",
            ),
            source_columns=(
                "trace_id", "request_id", "method", "path", "auth_subject", "auth_type", "session_id",
                "turn_id", "task_id", "status_code", "error_code", "idempotency_key", "rate_limited",
                "started_at", "updated_at",
            ),
            computed_values={
                "created_by": "CASE WHEN auth_subject = '' THEN 'system_migration' ELSE auth_subject END",
                "updated_by": "CASE WHEN auth_subject = '' THEN 'system_migration' ELSE auth_subject END",
                "created_at": "started_at",
                "ext_data1": empty_text,
                "ext_data2": empty_text,
                "ext_data3": empty_text,
                "ext_data4": empty_text,
                "ext_data5": empty_text,
            },
        )


def _ensure_audit_columns(connection: sqlite3.Connection) -> None:
    for table_name, migrations in AUDIT_COLUMN_MIGRATIONS.items():
        if not _table_exists(connection, table_name):
            continue
        existing_columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}
        for column_name, statement in migrations:
            if column_name not in existing_columns:
                connection.execute(statement)


def _drop_redundant_legacy_tables(connection: sqlite3.Connection) -> None:
    for source_table, target_table in LEGACY_TABLE_MAPPINGS:
        if source_table == target_table:
            continue
        if _table_exists(connection, source_table) and _table_exists(connection, target_table):
            connection.execute(f"DROP TABLE {source_table}")


def _upsert_schema_version(connection: sqlite3.Connection) -> None:
    timestamp = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
    connection.execute(
        f"""
        INSERT INTO {TABLE_SYS_SCHEMA_VERSION} (
            id, schema_version, version_note, created_by, updated_by, created_at, updated_at,
            ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
        ) VALUES (
            'schema_version_current', ?, ?,
            'system', 'system', {timestamp}, {timestamp},
            '', '', '', '', ''
        )
        ON CONFLICT(id) DO UPDATE SET
            schema_version = excluded.schema_version,
            version_note = excluded.version_note,
            updated_by = excluded.updated_by,
            updated_at = {timestamp}
        """,
        (
            SCHEMA_VERSION,
            "Extend stage-2 workflow role protocol with planner, executor, and reviewer roles.",
        ),
    )


def _seed_default_workflow_roles(connection: sqlite3.Connection) -> None:
    timestamp = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
    default_roles = (
        (
            "workflow_role_support",
            "support",
            "支持方代理",
            "优先指出当前规划与最终回答应保留的强项和有效路径。",
            1,
            10,
            "debate",
            "默认支持方角色",
        ),
        (
            "workflow_role_challenge",
            "challenge",
            "质疑方代理",
            "优先指出当前规划可能遗漏的风险、限制、反例或需要澄清的地方。",
            1,
            20,
            "debate",
            "默认质疑方角色",
        ),
        (
            "workflow_role_arbitration",
            "arbitration",
            "仲裁代理",
            "优先整理支持与质疑两方的观点，并给出最终可执行的取舍与输出要点。",
            1,
            30,
            "review",
            "默认仲裁角色",
        ),
        (
            "workflow_role_critic",
            "critic",
            "批评代理",
            "优先指出答案的遗漏、风险和说明不足，并给出最关键的修改建议。",
            1,
            40,
            "review",
            "默认批评角色",
        ),
    )
    for role in default_roles:
        connection.execute(
            f"""
            INSERT INTO {TABLE_SYS_WORKFLOW_ROLE} (
                id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                created_by, updated_by, created_at, updated_at,
                ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                'system', 'system', {timestamp}, {timestamp},
                '', '', '', '', ''
            )
            ON CONFLICT(role_key) DO NOTHING
            """,
            role,
        )


def _seed_additional_workflow_roles(connection: sqlite3.Connection) -> None:
    """
    What this is:
    - A schema-versioned seed extension for formal stage-2 workflow roles.

    What it does:
    - Inserts planner, executor, and reviewer roles when they are missing.

    Why this is done this way:
    - Earlier stage-2 schemas only seeded support/challenge/arbitration/critic.
    - A dedicated additive seed keeps compatibility with existing databases
      while extending the role protocol without destructive migration logic.
    """

    timestamp = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
    additional_roles = (
        (
            "workflow_role_planner",
            "planner",
            "规划代理",
            "优先梳理用户目标、上下文约束、工具结果与执行路径，生成可执行计划。",
            1,
            25,
            "execution",
            "正式规划角色",
        ),
        (
            "workflow_role_executor",
            "executor",
            "执行代理",
            "优先依据规划、工具结果和仲裁结论生成最终可执行回答。",
            1,
            35,
            "execution",
            "正式执行角色",
        ),
        (
            "workflow_role_reviewer",
            "reviewer",
            "复核代理",
            "优先根据答案、工具结果和批评摘要给出复核结论与发布建议。",
            1,
            50,
            "review",
            "正式复核角色",
        ),
    )
    for role in additional_roles:
        connection.execute(
            f"""
            INSERT INTO {TABLE_SYS_WORKFLOW_ROLE} (
                id, role_key, role_name, role_instruction, is_enabled, sort_order, role_type, description,
                created_by, updated_by, created_at, updated_at,
                ext_data1, ext_data2, ext_data3, ext_data4, ext_data5
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                'system', 'system', {timestamp}, {timestamp},
                '', '', '', '', ''
            )
            ON CONFLICT(role_key) DO NOTHING
            """,
            role,
        )


def ensure_database_initialized() -> None:
    database_path = _resolve_sqlite_path(get_database_url())
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _ensure_audit_columns(connection)
        _migrate_legacy_tables(connection)
        _drop_redundant_legacy_tables(connection)
        _upsert_schema_version(connection)
        _seed_default_workflow_roles(connection)
        _seed_additional_workflow_roles(connection)
        for statement in INDEX_STATEMENTS:
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
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
