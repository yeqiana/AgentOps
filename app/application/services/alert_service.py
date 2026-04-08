"""
Alert service wrapper.

What this is:
- An application-layer facade for runtime alert queries.

What it does:
- Exposes alert list and detail queries for API handlers.

Why this is done this way:
- API handlers should depend on an application service instead of talking to
  persistence repositories directly.
"""

from __future__ import annotations

from app.domain.models import AlertEventRecord
from app.infrastructure.alert import AlertService as InfrastructureAlertService


class AlertService:
    def __init__(self, service: InfrastructureAlertService | None = None) -> None:
        self.service = service or InfrastructureAlertService()

    def list_alerts(
        self,
        *,
        severity: str | None = None,
        source_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AlertEventRecord]:
        return self.service.list_alerts(
            severity=severity,
            source_type=source_type,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
        )

    def get_alert(self, alert_id: str) -> AlertEventRecord | None:
        return self.service.get_alert(alert_id)
