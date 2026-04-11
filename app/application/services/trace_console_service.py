"""
Trace console query service.

What this is:
- An application service for stage-3 trace console query aggregation.

What it does:
- Builds list, summary, timeline, graph, and viewer payloads for console use.

Why this is done this way:
- The API layer should keep parameter/auth concerns and delegate trace console
  aggregation to a reusable service boundary.
"""

from __future__ import annotations

from app.application.services.alert_service import AlertService
from app.application.services.session_service import SessionService
from app.infrastructure.trace import TraceService


class TraceConsoleService:
    def __init__(
        self,
        *,
        trace_service: TraceService | None = None,
        session_service: SessionService | None = None,
        alert_service: AlertService | None = None,
    ) -> None:
        self.trace_service = trace_service or TraceService()
        self.session_service = session_service or SessionService()
        self.alert_service = alert_service or AlertService()

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
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        normalized_page = max(1, page)
        normalized_page_size = max(1, min(page_size, 100))
        offset = (normalized_page - 1) * normalized_page_size
        items = self.trace_service.list_console_traces(
            trace_id=trace_id,
            task_id=task_id,
            session_id=session_id,
            path=path,
            method=method,
            status_code=status_code,
            route_name=route_name,
            started_from=started_from,
            started_to=started_to,
            limit=normalized_page_size,
            offset=offset,
        )
        total = self.trace_service.count_console_traces(
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
        return {
            "items": [self._to_console_list_item(item) for item in items],
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total,
            "has_next": offset + len(items) < total,
        }

    def get_trace_summary(self, trace_id: str) -> dict[str, object] | None:
        trace_bundle = self._load_trace_bundle(trace_id)
        if not trace_bundle:
            return None
        return self._build_trace_summary(trace_bundle)

    def get_trace_timeline(self, trace_id: str) -> dict[str, object] | None:
        trace_bundle = self._load_trace_bundle(trace_id)
        if not trace_bundle:
            return None
        return {
            "trace": self._to_trace_payload(trace_bundle["trace"]),
            "events": self._build_trace_timeline_events(trace_bundle),
        }

    def get_trace_graph(self, trace_id: str) -> dict[str, object] | None:
        trace_bundle = self._load_trace_bundle(trace_id)
        if not trace_bundle:
            return None
        graph_nodes, graph_edges = self._build_trace_graph(trace_bundle)
        return {
            "trace": self._to_trace_payload(trace_bundle["trace"]),
            "nodes": graph_nodes,
            "edges": graph_edges,
        }

    def get_trace_viewer(self, trace_id: str) -> dict[str, object] | None:
        trace_bundle = self._load_trace_bundle(trace_id)
        if not trace_bundle:
            return None
        graph_nodes, graph_edges = self._build_trace_graph(trace_bundle)
        summary = self._build_trace_summary(trace_bundle)
        return {
            "viewer": {
                "trace": summary["trace"],
                "summary": summary,
                "timeline": self._build_trace_timeline_events(trace_bundle),
                "graph_nodes": graph_nodes,
                "graph_edges": graph_edges,
                "alerts": [self._to_alert_payload(item) for item in trace_bundle["alerts"]],
            }
        }

    def _load_trace_bundle(self, trace_id: str) -> dict[str, object] | None:
        trace = self.trace_service.get_trace(trace_id)
        if not trace:
            return None
        task_bundle = self.session_service.get_task(trace["task_id"]) if trace["task_id"] else None
        route_decisions = (
            task_bundle["route_decisions"]
            if task_bundle
            else self.session_service.list_route_decisions(trace_id=trace_id, limit=100, offset=0)
        )
        task_events = task_bundle["task_events"] if task_bundle else []
        tool_results = task_bundle["tool_results"] if task_bundle else []
        alerts = self.alert_service.list_alerts(trace_id=trace_id, limit=100, offset=0)
        return {
            "trace": trace,
            "task_bundle": task_bundle,
            "route_decisions": route_decisions,
            "task_events": task_events,
            "tool_results": tool_results,
            "alerts": alerts,
        }

    def _build_trace_summary(self, trace_bundle: dict[str, object]) -> dict[str, object]:
        task_bundle = trace_bundle["task_bundle"]
        return {
            "trace": self._to_trace_payload(trace_bundle["trace"]),
            "task": self._to_task_payload(task_bundle["task"]) if task_bundle else None,
            "task_events": [self._to_task_event_payload(item) for item in trace_bundle["task_events"]],
            "tool_results": [self._to_tool_result_payload(item) for item in trace_bundle["tool_results"]],
            "route_decisions": [self._to_route_decision_payload(item) for item in trace_bundle["route_decisions"]],
            "alerts": [self._to_alert_payload(item) for item in trace_bundle["alerts"]],
        }

    def _build_trace_timeline_events(self, trace_bundle: dict[str, object]) -> list[dict[str, object]]:
        trace = trace_bundle["trace"]
        task_bundle = trace_bundle["task_bundle"]
        task_events = trace_bundle["task_events"]
        route_decisions = trace_bundle["route_decisions"]
        tool_results = trace_bundle["tool_results"]
        alerts = trace_bundle["alerts"]
        timeline: list[dict[str, object]] = [
            {
                "happened_at": str(trace["started_at"]),
                "event_type": "request_started",
                "source_type": "trace",
                "source_name": str(trace["method"]),
                "title": f'{trace["method"]} {trace["path"]}',
                "details": f'auth_subject={trace["auth_subject"]}, status_code={trace["status_code"]}',
                "trace_id": str(trace["trace_id"]),
                "task_id": str(trace["task_id"]),
                "session_id": str(trace["session_id"]),
                "turn_id": str(trace["turn_id"]),
            }
        ]
        if task_bundle:
            task = task_bundle["task"]
            timeline.append(
                {
                    "happened_at": str(task["created_at"]),
                    "event_type": "task_recorded",
                    "source_type": "task",
                    "source_name": str(task["status"]),
                    "title": str(task["id"]),
                    "details": f'route={task["route_name"]}, execution_mode={task["execution_mode"]}',
                    "trace_id": str(task["trace_id"]),
                    "task_id": str(task["id"]),
                    "session_id": str(task["session_id"]),
                    "turn_id": str(task["turn_id"]),
                }
            )
        timeline.extend(
            {
                "happened_at": str(item["created_at"]),
                "event_type": str(item["event_type"]),
                "source_type": "task_event",
                "source_name": str(item["event_type"]),
                "title": str(item["event_message"]),
                "details": str(item["event_payload_json"]),
                "trace_id": str(item["trace_id"]),
                "task_id": str(item["task_id"]),
                "session_id": str(item["session_id"]),
                "turn_id": str(item["turn_id"]),
            }
            for item in task_events
        )
        timeline.extend(
            {
                "happened_at": str(item["created_at"]),
                "event_type": "route_decision",
                "source_type": "route",
                "source_name": str(item["route_source"]),
                "title": str(item["route_name"]),
                "details": str(item["route_reason"]),
                "trace_id": str(item["trace_id"]),
                "task_id": str(item["task_id"]),
                "session_id": str(item["session_id"]),
                "turn_id": str(item["turn_id"]),
            }
            for item in route_decisions
        )
        timeline.extend(
            {
                "happened_at": str(item["created_at"]),
                "event_type": "tool_result",
                "source_type": "tool",
                "source_name": str(item["tool_name"]),
                "title": f'{item["tool_name"]} success={item["success"]}',
                "details": f'exit_code={item["exit_code"]}',
                "trace_id": str(item["trace_id"]),
                "task_id": str(item["task_id"]),
                "session_id": str(item["session_id"]),
                "turn_id": str(item["turn_id"]),
            }
            for item in tool_results
        )
        timeline.extend(
            {
                "happened_at": str(item["created_at"]),
                "event_type": "alert",
                "source_type": "alert",
                "source_name": str(item["source_type"]),
                "title": str(item["event_code"]),
                "details": str(item["message"]),
                "trace_id": str(item["trace_id"]),
                "task_id": str(trace["task_id"]),
                "session_id": str(trace["session_id"]),
                "turn_id": str(trace["turn_id"]),
            }
            for item in alerts
        )
        return sorted(timeline, key=lambda item: item["happened_at"])

    def _build_trace_graph(self, trace_bundle: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        trace = trace_bundle["trace"]
        task_bundle = trace_bundle["task_bundle"]
        route_decisions = trace_bundle["route_decisions"]
        tool_results = trace_bundle["tool_results"]
        alerts = trace_bundle["alerts"]
        trace_node_id = f'trace:{trace["trace_id"]}'
        nodes: list[dict[str, object]] = [
            {
                "node_id": trace_node_id,
                "node_type": "trace",
                "title": f'{trace["method"]} {trace["path"]}',
                "subtitle": f'status={trace["status_code"]}',
                "happened_at": str(trace["started_at"]),
            }
        ]
        edges: list[dict[str, object]] = []

        task_node_id = ""
        if task_bundle:
            task = task_bundle["task"]
            task_node_id = f'task:{task["id"]}'
            nodes.append(
                {
                    "node_id": task_node_id,
                    "node_type": "task",
                    "title": str(task["id"]),
                    "subtitle": f'status={task["status"]}',
                    "happened_at": str(task["created_at"]),
                }
            )
            edges.append(
                {
                    "source_id": trace_node_id,
                    "target_id": task_node_id,
                    "edge_type": "owns_task",
                }
            )

        for item in route_decisions:
            route_node_id = f'route:{item["id"] or item["trace_id"] + ":" + item["route_name"]}'
            nodes.append(
                {
                    "node_id": route_node_id,
                    "node_type": "route",
                    "title": str(item["route_name"]),
                    "subtitle": str(item["route_source"]),
                    "happened_at": str(item["created_at"]),
                }
            )
            edges.append(
                {
                    "source_id": task_node_id or trace_node_id,
                    "target_id": route_node_id,
                    "edge_type": "route_decision",
                }
            )

        for item in tool_results:
            tool_node_id = f'tool:{item["id"] or item["trace_id"] + ":" + item["tool_name"]}'
            nodes.append(
                {
                    "node_id": tool_node_id,
                    "node_type": "tool",
                    "title": str(item["tool_name"]),
                    "subtitle": f'success={item["success"]}',
                    "happened_at": str(item["created_at"]),
                }
            )
            edges.append(
                {
                    "source_id": task_node_id or trace_node_id,
                    "target_id": tool_node_id,
                    "edge_type": "tool_execution",
                }
            )

        for item in alerts:
            alert_node_id = f'alert:{item["id"]}'
            nodes.append(
                {
                    "node_id": alert_node_id,
                    "node_type": "alert",
                    "title": str(item["event_code"]),
                    "subtitle": str(item["severity"]),
                    "happened_at": str(item["created_at"]),
                }
            )
            edges.append(
                {
                    "source_id": trace_node_id,
                    "target_id": alert_node_id,
                    "edge_type": "alert",
                }
            )
        return nodes, edges

    def _to_console_list_item(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "trace_id": str(item["trace_id"]),
            "request_id": str(item["request_id"]),
            "method": str(item["method"]),
            "path": str(item["path"]),
            "status_code": int(item["status_code"]),
            "error_code": str(item["error_code"] or ""),
            "rate_limited": bool(item["rate_limited"]),
            "started_at": str(item["started_at"]),
            "updated_at": str(item["updated_at"]),
            "session_id": str(item["session_id"] or ""),
            "turn_id": str(item["turn_id"] or ""),
            "task_id": str(item["task_id"] or ""),
            "route_name": str(item["route_name"] or ""),
            "route_source": str(item["route_source"] or ""),
            "execution_mode": str(item["execution_mode"] or ""),
            "review_status": str(item["review_status"] or ""),
            "alert_count": int(item["alert_count"] or 0),
            "last_event_at": str(item["last_event_at"] or ""),
        }

    def _to_trace_payload(self, trace: dict[str, object]) -> dict[str, object]:
        return {
            "trace_id": trace["trace_id"],
            "request_id": trace["request_id"],
            "method": trace["method"],
            "path": trace["path"],
            "auth_subject": trace["auth_subject"],
            "auth_type": trace["auth_type"],
            "session_id": trace["session_id"],
            "turn_id": trace["turn_id"],
            "task_id": trace["task_id"],
            "status_code": trace["status_code"],
            "error_code": trace["error_code"],
            "idempotency_key": trace["idempotency_key"],
            "rate_limited": trace["rate_limited"],
            "started_at": trace["started_at"],
            "updated_at": trace["updated_at"],
        }

    def _to_task_payload(self, task: dict[str, object]) -> dict[str, object]:
        return {
            "id": task["id"],
            "session_id": task["session_id"],
            "turn_id": task["turn_id"],
            "trace_id": task["trace_id"],
            "status": task["status"],
            "user_input": task["user_input"],
            "execution_mode": task["execution_mode"],
            "protocol_summary": task["protocol_summary"],
            "route_name": task["route_name"],
            "route_reason": task["route_reason"],
            "route_source": task["route_source"],
            "plan": task["plan"],
            "debate_summary": task["debate_summary"],
            "arbitration_summary": task["arbitration_summary"],
            "answer": task["answer"],
            "critic_summary": task["critic_summary"],
            "review_status": task["review_status"],
            "review_summary": task["review_summary"],
            "tool_count": task["tool_count"],
            "error_message": task["error_message"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        }

    def _to_task_event_payload(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "id": item["id"],
            "task_id": item["task_id"],
            "session_id": item["session_id"],
            "turn_id": item["turn_id"],
            "trace_id": item["trace_id"],
            "event_type": item["event_type"],
            "event_message": item["event_message"],
            "event_payload_json": item["event_payload_json"],
            "created_at": item["created_at"],
        }

    def _to_tool_result_payload(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "id": item["id"],
            "task_id": item["task_id"],
            "session_id": item["session_id"],
            "turn_id": item["turn_id"],
            "trace_id": item["trace_id"],
            "tool_name": item["tool_name"],
            "success": item["success"],
            "exit_code": item["exit_code"],
            "stdout": item["stdout"],
            "stderr": item["stderr"],
            "created_at": item["created_at"],
        }

    def _to_route_decision_payload(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "id": item["id"],
            "task_id": item["task_id"],
            "session_id": item["session_id"],
            "turn_id": item["turn_id"],
            "trace_id": item["trace_id"],
            "route_name": item["route_name"],
            "route_reason": item["route_reason"],
            "route_source": item["route_source"],
            "created_at": item["created_at"],
        }

    def _to_alert_payload(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "id": item["id"],
            "trace_id": item["trace_id"],
            "source_type": item["source_type"],
            "source_name": item["source_name"],
            "severity": item["severity"],
            "event_code": item["event_code"],
            "message": item["message"],
            "payload_json": item["payload_json"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
