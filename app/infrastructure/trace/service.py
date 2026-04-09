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

from datetime import datetime, timezone

from app.infrastructure.persistence.repositories import SQLiteTraceRepository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceService:
    def __init__(self) -> None:
        self.repository = SQLiteTraceRepository()

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
        timestamp = _now_iso()
        subject = auth_subject or "anonymous"
        self.repository.create_or_update(
            {
                "trace_id": trace_id,
                "request_id": request_id,
                "method": method,
                "path": path,
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
                "ext_data1": "",
                "ext_data2": "",
                "ext_data3": "",
                "ext_data4": "",
                "ext_data5": "",
            }
        )

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
            return
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
            return
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
