"""
Trace service.

What this is:
- The stage-2 request trace persistence service.

What it does:
- Creates and updates request-level trace records.
- Attaches execution context such as session, turn, and task IDs.
- Provides trace queries for API troubleshooting.

Why this is done this way:
- Stage 2 needs trace data to become a first-class backend capability instead of
  only an ID echoed in logs and responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.errors import TraceConsistencyError
from app.domain.models import TraceRecord
from app.infrastructure.logger import get_logger
from app.infrastructure.persistence.repositories import SQLiteTraceRepository


logger = get_logger("infrastructure.trace")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceService:
    def __init__(self) -> None:
        self.repository = SQLiteTraceRepository()

    def start_trace(
        self,
        *,
        source_type: str,
        existing_trace_id: str | None = None,
        request_id: str | None = None,
        method: str = "",
        path: str = "",
        auth_subject: str = "",
        auth_type: str = "",
        idempotency_key: str = "",
        created_by: str = "",
    ) -> TraceRecord:
        normalized_source = (source_type or "").strip().lower()
        if normalized_source not in {"http", "cli", "background", "system"}:
            raise TraceConsistencyError(
                "trace source_type must be one of: http, cli, background, system.",
                details={"source_type": source_type or ""},
            )

        if existing_trace_id:
            existing = self.repository.get_by_trace_id(existing_trace_id)
            if not existing:
                raise TraceConsistencyError(
                    "existing_trace_id does not exist in sys_request_trace.",
                    trace_id=existing_trace_id,
                    details={"source_type": normalized_source},
                )
            return existing

        normalized_method, normalized_path = self._normalize_source_context(
            normalized_source,
            method=method,
            path=path,
        )
        timestamp = _now_iso()
        subject = created_by or auth_subject or normalized_source
        trace: TraceRecord = {
            "trace_id": f"trace_{uuid.uuid4().hex}",
            "request_id": request_id or f"req_{uuid.uuid4().hex}",
            "method": normalized_method,
            "path": normalized_path,
            "auth_subject": auth_subject,
            "auth_type": auth_type,
            "session_id": "",
            "turn_id": "",
            "task_id": "",
            "status_code": 0,
            "error_code": "",
            "idempotency_key": idempotency_key,
            "rate_limited": False,
            "created_by": subject,
            "updated_by": subject,
            "created_at": timestamp,
            "started_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": normalized_source,
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }
        self.repository.create_or_update(trace)
        return trace

    def _normalize_source_context(self, source_type: str, *, method: str, path: str) -> tuple[str, str]:
        if source_type == "http":
            return (method or "HTTP").strip().upper(), (path or "http://unknown").strip()
        if source_type == "cli":
            return "CLI", path or "cli://chat"
        if source_type == "background":
            return "BACKGROUND", path or "background://task"
        return "SYSTEM", path or "system://alert"

    def begin_request(
        self,
        *,
        trace_id: str,
        request_id: str,
        method: str,
        path: str,
        auth_subject: str,
        auth_type: str,
        idempotency_key: str,
    ) -> None:
        existing = self.repository.get_by_trace_id(trace_id)
        if not existing:
            raise TraceConsistencyError(
                "begin_request no longer creates trace records. Call TraceService.start_trace(...) to create trace_id.",
                trace_id=trace_id,
            )
        existing["request_id"] = request_id or existing["request_id"]
        existing["method"] = (method or existing["method"]).upper()
        existing["path"] = path or existing["path"]
        existing["auth_subject"] = auth_subject or existing["auth_subject"]
        existing["auth_type"] = auth_type or existing["auth_type"]
        existing["idempotency_key"] = idempotency_key or existing["idempotency_key"]
        existing["updated_by"] = existing["auth_subject"] or existing["updated_by"]
        existing["updated_at"] = _now_iso()
        self.repository.create_or_update(existing)

    def attach_execution_context(
        self,
        trace_id: str,
        *,
        session_id: str = "",
        turn_id: str = "",
        task_id: str = "",
    ) -> None:
        existing = self.repository.get_by_trace_id(trace_id)
        if not existing:
            logger.error(
                "trace execution context attach failed: missing trace_id=%s session_id=%s turn_id=%s task_id=%s",
                trace_id,
                session_id,
                turn_id,
                task_id,
            )
            raise TraceConsistencyError(
                "trace_id does not exist in sys_request_trace. Call TraceService.start_trace(...) before attaching execution context.",
                trace_id=trace_id,
                details={
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "task_id": task_id,
                },
            )
        existing["session_id"] = session_id or existing["session_id"]
        existing["turn_id"] = turn_id or existing["turn_id"]
        existing["task_id"] = task_id or existing["task_id"]
        existing["updated_by"] = existing["auth_subject"] or existing["updated_by"]
        existing["updated_at"] = _now_iso()
        self.repository.create_or_update(existing)

    def finish_request(
        self,
        trace_id: str,
        *,
        status_code: int,
        error_code: str = "",
        rate_limited: bool = False,
    ) -> None:
        existing = self.repository.get_by_trace_id(trace_id)
        if not existing:
            logger.error("trace finish failed: missing trace_id=%s", trace_id)
            raise TraceConsistencyError(
                "trace_id does not exist in sys_request_trace. Call TraceService.start_trace(...) before finishing trace.",
                trace_id=trace_id,
            )
        existing["status_code"] = status_code
        existing["error_code"] = error_code
        existing["rate_limited"] = rate_limited
        existing["updated_by"] = existing["auth_subject"] or existing["updated_by"]
        existing["updated_at"] = _now_iso()
        self.repository.create_or_update(existing)

    def get_trace(self, trace_id: str):
        return self.repository.get_by_trace_id(trace_id)

    def list_trace_stats(
        self,
        *,
        method: str | None = None,
        path: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        """
        Expose grouped trace statistics for control-plane APIs.

        What this is:
        - A small facade over trace aggregate queries.

        What it does:
        - Returns grouped trace counts by request method/path/status.

        Why this is done this way:
        - API handlers should continue depending on the trace service instead of
          reaching directly into persistence repositories.
        """
        return self.repository.list_stats(
            method=method,
            path=path,
            limit=limit,
            offset=offset,
        )

    def list_console_traces(
        self,
        *,
        trace_id: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        path: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        route_name: str | None = None,
        started_from: str | None = None,
        started_to: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self.repository.list_console_traces(
            trace_id=trace_id,
            task_id=task_id,
            session_id=session_id,
            path=path,
            method=method,
            status_code=status_code,
            route_name=route_name,
            started_from=started_from,
            started_to=started_to,
            limit=limit,
            offset=offset,
        )

    def count_console_traces(
        self,
        *,
        trace_id: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        path: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        route_name: str | None = None,
        started_from: str | None = None,
        started_to: str | None = None,
    ) -> int:
        return self.repository.count_console_traces(
            trace_id=trace_id,
            task_id=task_id,
            session_id=session_id,
            path=path,
            method=method,
            status_code=status_code,
            route_name=route_name,
            started_from=started_from,
            started_to=started_to,
        )
