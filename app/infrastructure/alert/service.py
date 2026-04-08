"""
Alert service.

What this is:
- A small persistence service for runtime governance alerts.

What it does:
- Records recovery and degradation events into `sys_alert_event`.
- Exposes simple query methods for API troubleshooting endpoints.

Why this is done this way:
- Stage-2 recovery work needs stable alert records instead of relying only on
  logs or transient in-memory state.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from app.domain.models import AlertEventRecord
from app.infrastructure.persistence.repositories import SQLiteAlertEventRepository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AlertService:
    def __init__(self, repository: SQLiteAlertEventRepository | None = None) -> None:
        self.repository = repository or SQLiteAlertEventRepository()

    def create_alert(
        self,
        *,
        trace_id: str,
        source_type: str,
        source_name: str,
        severity: str,
        event_code: str,
        message: str,
        payload: dict[str, object] | None = None,
        created_by: str = "system",
    ) -> AlertEventRecord:
        timestamp = _now_iso()
        alert: AlertEventRecord = {
            "id": f"alert_{uuid.uuid4().hex}",
            "trace_id": trace_id,
            "source_type": source_type,
            "source_name": source_name,
            "severity": severity,
            "event_code": event_code,
            "message": message,
            "payload_json": json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
            "created_by": created_by,
            "updated_by": created_by,
            "created_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }
        self.repository.create(alert)
        return alert

    def list_alerts(
        self,
        *,
        severity: str | None = None,
        source_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AlertEventRecord]:
        return self.repository.list_alerts(
            severity=severity,
            source_type=source_type,
            limit=limit,
            offset=offset,
        )

    def get_alert(self, alert_id: str) -> AlertEventRecord | None:
        return self.repository.get_by_id(alert_id)


@lru_cache(maxsize=1)
def get_alert_service() -> AlertService:
    return AlertService()
