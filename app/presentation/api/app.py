"""
FastAPI application factory.

What this is:
- The HTTP entrypoint for the stage-2 Agent runtime.

What it does:
- Exposes health, chat, session, task, tool, asset analysis, upload, asset, and
  trace APIs.
- Applies auth, governance, and trace middleware.
- Converts domain and runtime exceptions into stable structured HTTP responses.

Why this is done this way:
- API consumers need a stable protocol surface, while the internal graph,
  persistence, observability, and toolchain can continue evolving behind the
  factory boundary.
"""

import json

from app.application.agent_service import create_initial_state, parse_input_assets
from app.application.services.alert_service import AlertService
from app.application.services.async_task_service import AsyncTaskService
from app.application.services.chat_service import ChatService
from app.application.services.config_service import RuntimeConfigService
from app.application.services.request_route_service import RequestRouteService
from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.application.services.workflow_role_service import WorkflowRoleService
from app.application.upload_service import create_uploaded_asset
from app.config import (
    get_async_task_workers,
    get_upload_download_dir,
    is_async_task_enabled,
)
from app.domain.errors import AgentError, ParsingError, ValidationError
from app.infrastructure.auth import AuthService
from app.infrastructure.llm.client import LLMCallError, sanitize_text
from app.infrastructure.logger import get_logger
from app.infrastructure.queue import BackgroundTaskRunner
from app.infrastructure.tools.registry import build_default_tool_registry
from app.infrastructure.trace import TraceService
from app.presentation.api.middleware.auth import AuthMiddleware
from app.presentation.api.middleware.governance import GovernanceMiddleware, IdempotencyStore, RateLimiter
from app.presentation.api.middleware.trace import TraceMiddleware
from app.presentation.api.schemas import (
    AuthMeResponse,
    AuthPermissionPayload,
    AuthPermissionMatrixResponse,
    AuthProfilePayload,
    AuthRoleListResponse,
    AuthRolePermissionMatrixItemPayload,
    AuthRolePayload,
    AuthSubjectRoleAssignRequest,
    AuthSubjectRoleAssignResponse,
    AuthSubjectAccessResponse,
    AuthSubjectRolePayload,
    AsyncTaskRuntimePayload,
    AsyncTaskRuntimeResponse,
    AsyncTaskSubmitRequest,
    AsyncTaskSubmitResponse,
    AnalyzeAssetRequest,
    AnalyzeAssetResponse,
    AlertEventListResponse,
    AlertEventPayload,
    AlertEventResponse,
    AlertStatPayload,
    AlertStatsResponse,
    AssetListResponse,
    AssetPayload,
    AssetResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    RecoveryConfigPayload,
    RecoveryConfigResponse,
    RouteDecisionListResponse,
    RouteDecisionPayload,
    RouteDecisionStatPayload,
    RouteDecisionStatsResponse,
    RuntimeConfigItemPayload,
    RuntimeConfigEventListResponse,
    RuntimeConfigEventPayload,
    RuntimeConfigListResponse,
    RuntimeConfigUpsertRequest,
    RuntimeConfigUpsertResponse,
    RoutingConfigPayload,
    RoutingConfigResponse,
    RoutingPreviewRequest,
    RoutingPreviewResponse,
    RoutingConfigTemplateItemPayload,
    RoutingConfigTemplateResponse,
    RoutingDecisionRulePayload,
    RoutingRulePayload,
    SessionListResponse,
    SessionPayload,
    SecurityConfigPayload,
    SecurityConfigResponse,
    MessagePayload,
    OperationsOverviewPayload,
    OperationsOverviewResponse,
    SessionResponse,
    SessionSummaryPayload,
    SessionSummaryResponse,
    TaskListResponse,
    TaskEventListResponse,
    TaskEventPayload,
    TaskPayload,
    TaskResponse,
    TaskStatsPayload,
    TaskStatsResponse,
    TaskStatusStatPayload,
    TaskSummaryPayload,
    TaskSummaryResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolInfoPayload,
    ToolListResponse,
    TracePayload,
    TraceSummaryPayload,
    TraceSummaryResponse,
    TraceResponse,
    TraceStatsResponse,
    TraceStatPayload,
    TraceGraphEdgePayload,
    TraceGraphNodePayload,
    TraceGraphResponse,
    TraceTimelineEventPayload,
    TraceTimelineResponse,
    UploadAssetResponse,
    WorkflowConfigPayload,
    WorkflowConfigResponse,
    WorkflowRolePayload,
    WorkflowRoleListResponse,
    WorkflowRoleUpsertRequest,
    WorkflowRoleUpsertResponse,
)
from app.workflow.graph import build_graph
from app.workflow.nodes import tool_node
from app.workflow.registry import build_workflow_policy_registry


logger = get_logger("presentation.api")


def _build_trace_timeline_events(
    trace: dict[str, object],
    task_bundle: dict[str, object] | None,
    route_decisions: list[dict[str, object]],
    task_events: list[dict[str, object]],
    tool_results: list[dict[str, object]],
    alerts: list[dict[str, object]],
) -> list[TraceTimelineEventPayload]:
    """
    Build a single chronological trace timeline from already-persisted records.

    What this is:
    - A lightweight API-side event normalizer for trace visualization.

    What it does:
    - Merges trace, task, route, tool, and alert records into one sorted list.

    Why this is done this way:
    - Stage 3 needs timeline-style data, but stage 2 already persists enough
      records to derive it without introducing a new table.
    """
    timeline: list[TraceTimelineEventPayload] = [
        TraceTimelineEventPayload(
            happened_at=str(trace["started_at"]),
            event_type="request_started",
            source_type="trace",
            source_name=str(trace["method"]),
            title=f'{trace["method"]} {trace["path"]}',
            details=f'auth_subject={trace["auth_subject"]}, status_code={trace["status_code"]}',
            trace_id=str(trace["trace_id"]),
            task_id=str(trace["task_id"]),
            session_id=str(trace["session_id"]),
            turn_id=str(trace["turn_id"]),
        )
    ]
    if task_bundle:
        task = task_bundle["task"]
        timeline.append(
            TraceTimelineEventPayload(
                happened_at=str(task["created_at"]),
                event_type="task_recorded",
                source_type="task",
                source_name=str(task["status"]),
                title=str(task["id"]),
                details=f'route={task["route_name"]}, execution_mode={task["execution_mode"]}',
                trace_id=str(task["trace_id"]),
                task_id=str(task["id"]),
                session_id=str(task["session_id"]),
                turn_id=str(task["turn_id"]),
            )
        )
    timeline.extend(
        TraceTimelineEventPayload(
            happened_at=str(item["created_at"]),
            event_type=str(item["event_type"]),
            source_type="task_event",
            source_name=str(item["event_type"]),
            title=str(item["event_message"]),
            details=str(item["event_payload_json"]),
            trace_id=str(item["trace_id"]),
            task_id=str(item["task_id"]),
            session_id=str(item["session_id"]),
            turn_id=str(item["turn_id"]),
        )
        for item in task_events
    )
    timeline.extend(
        TraceTimelineEventPayload(
            happened_at=str(item["created_at"]),
            event_type="route_decision",
            source_type="route",
            source_name=str(item["route_source"]),
            title=str(item["route_name"]),
            details=str(item["route_reason"]),
            trace_id=str(item["trace_id"]),
            task_id=str(item["task_id"]),
            session_id=str(item["session_id"]),
            turn_id=str(item["turn_id"]),
        )
        for item in route_decisions
    )
    timeline.extend(
        TraceTimelineEventPayload(
            happened_at=str(item["created_at"]),
            event_type="tool_result",
            source_type="tool",
            source_name=str(item["tool_name"]),
            title=f'{item["tool_name"]} success={item["success"]}',
            details=f'exit_code={item["exit_code"]}',
            trace_id=str(item["trace_id"]),
            task_id=str(item["task_id"]),
            session_id=str(item["session_id"]),
            turn_id=str(item["turn_id"]),
        )
        for item in tool_results
    )
    timeline.extend(
        TraceTimelineEventPayload(
            happened_at=str(item["created_at"]),
            event_type="alert",
            source_type="alert",
            source_name=str(item["source_type"]),
            title=str(item["event_code"]),
            details=str(item["message"]),
            trace_id=str(item["trace_id"]),
            task_id=str(trace["task_id"]),
            session_id=str(trace["session_id"]),
            turn_id=str(trace["turn_id"]),
        )
        for item in alerts
    )
    return sorted(timeline, key=lambda item: item.happened_at)


def _build_trace_graph(
    trace: dict[str, object],
    task_bundle: dict[str, object] | None,
    route_decisions: list[dict[str, object]],
    tool_results: list[dict[str, object]],
    alerts: list[dict[str, object]],
) -> tuple[list[TraceGraphNodePayload], list[TraceGraphEdgePayload]]:
    """
    Build graph-style trace view data for future visualization UIs.

    What this is:
    - A normalized node/edge projection over already persisted trace data.

    What it does:
    - Emits graph nodes and relationships for trace, task, route, tool, and alert records.

    Why this is done this way:
    - Stage 3 visualization work should not need to reverse-engineer raw API payloads.
      A simple graph projection keeps the server-side protocol stable and UI-friendly.
    """
    trace_node_id = f'trace:{trace["trace_id"]}'
    nodes: list[TraceGraphNodePayload] = [
        TraceGraphNodePayload(
            node_id=trace_node_id,
            node_type="trace",
            title=f'{trace["method"]} {trace["path"]}',
            subtitle=f'status={trace["status_code"]}',
            happened_at=str(trace["started_at"]),
        )
    ]
    edges: list[TraceGraphEdgePayload] = []

    task_node_id = ""
    if task_bundle:
        task = task_bundle["task"]
        task_node_id = f'task:{task["id"]}'
        nodes.append(
            TraceGraphNodePayload(
                node_id=task_node_id,
                node_type="task",
                title=str(task["id"]),
                subtitle=f'status={task["status"]}',
                happened_at=str(task["created_at"]),
            )
        )
        edges.append(TraceGraphEdgePayload(source_id=trace_node_id, target_id=task_node_id, edge_type="owns_task"))

    for item in route_decisions:
        route_node_id = f'route:{item["id"] or item["trace_id"] + ":" + item["route_name"]}'
        nodes.append(
            TraceGraphNodePayload(
                node_id=route_node_id,
                node_type="route",
                title=str(item["route_name"]),
                subtitle=str(item["route_source"]),
                happened_at=str(item["created_at"]),
            )
        )
        edges.append(
            TraceGraphEdgePayload(
                source_id=task_node_id or trace_node_id,
                target_id=route_node_id,
                edge_type="route_decision",
            )
        )

    for item in tool_results:
        tool_node_id = f'tool:{item["id"] or item["trace_id"] + ":" + item["tool_name"]}'
        nodes.append(
            TraceGraphNodePayload(
                node_id=tool_node_id,
                node_type="tool",
                title=str(item["tool_name"]),
                subtitle=f'success={item["success"]}',
                happened_at=str(item["created_at"]),
            )
        )
        edges.append(
            TraceGraphEdgePayload(
                source_id=task_node_id or trace_node_id,
                target_id=tool_node_id,
                edge_type="tool_execution",
            )
        )

    for item in alerts:
        alert_node_id = f'alert:{item["id"]}'
        nodes.append(
            TraceGraphNodePayload(
                node_id=alert_node_id,
                node_type="alert",
                title=str(item["event_code"]),
                subtitle=str(item["severity"]),
                happened_at=str(item["created_at"]),
            )
        )
        edges.append(
            TraceGraphEdgePayload(
                source_id=trace_node_id,
                target_id=alert_node_id,
                edge_type="alert",
            )
        )
    return nodes, edges


def create_app():
    try:
        from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
        from fastapi.responses import JSONResponse, StreamingResponse
    except ImportError as error:
        raise RuntimeError(
            "未安装 fastapi。请先安装 `fastapi`、`uvicorn` 和 `python-multipart` 后再启动 API。"
        ) from error

    session_service = SessionService()
    alert_service = AlertService()
    config_service = RuntimeConfigService()
    workflow_role_service = WorkflowRoleService()
    tool_registry = build_default_tool_registry(config_service)
    task_service = TaskService(tool_registry)
    chat_service = ChatService()
    auth_service = AuthService()
    trace_service = TraceService()
    request_route_service = RequestRouteService()
    graph = build_graph()
    app = FastAPI(title="Agent Base Runtime API", version="0.7.0")
    async_task_service = AsyncTaskService(
        runner=BackgroundTaskRunner(max_workers=get_async_task_workers()),
        chat_service=chat_service,
        session_service=session_service,
        trace_service=trace_service,
        task_service=task_service,
        request_route_service=request_route_service,
    )
    app.add_middleware(TraceMiddleware, trace_service=trace_service)
    app.add_middleware(GovernanceMiddleware, rate_limiter=RateLimiter(), idempotency_store=IdempotencyStore())
    app.add_middleware(AuthMiddleware, auth_service=auth_service)

    def build_error_response(error: AgentError) -> ErrorResponse:
        return ErrorResponse(**error.to_dict())

    def persist_failed_task_if_possible(current_state: dict[str, object] | None, error: AgentError) -> None:
        if current_state is None:
            return
        session_service.persist_failed_turn(current_state, error)

    def preview_tools(
        user_input: str,
        input_assets: list[dict[str, object]],
        *,
        trace_id: str,
    ) -> tuple[dict[str, object], list[dict[str, object]], str]:
        task_service.tool_registry = current_tool_registry()
        route_decision = request_route_service.decide(
            user_input=user_input,
            input_assets=input_assets,  # type: ignore[arg-type]
            message_count=1,
            route_source="request_entry",
        )
        preview_state = task_service.prepare_turn_state(
            create_initial_state(user_id="preview-user"),
            user_input,
            input_assets,  # type: ignore[arg-type]
            trace_id=trace_id,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            route_source=route_decision["route_source"],
        )
        preview_state = tool_node(preview_state)
        return preview_state, preview_state["tool_results"], preview_state["task_state"]

    def current_tool_registry():
        return build_default_tool_registry(config_service)

    def prepare_async_state(
        *,
        user_input: str,
        session_id: str,
        user_name: str,
        session_title: str,
        trace_id: str,
    ) -> dict[str, object]:
        normalized_user_input, input_assets = parse_input_assets(user_input)
        task_service.tool_registry = current_tool_registry()
        state = session_service.ensure_session(session_id or None, user_name=user_name, title=session_title)
        route_decision = request_route_service.decide(
            user_input=normalized_user_input,
            input_assets=input_assets,
            message_count=len(state["messages"]) + 1,
            route_source="request_entry",
        )
        return task_service.prepare_turn_state(
            state,
            normalized_user_input,
            input_assets,
            trace_id=trace_id,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            route_source=route_decision["route_source"],
        )

    def get_auth_profile(request: Request):
        return auth_service.get_authorization_profile(
            getattr(request.state, "auth_subject", "anonymous"),
            getattr(request.state, "auth_type", "unknown"),
        )

    def require_permission(request: Request, permission_key: str):
        return auth_service.authorize(
            subject=getattr(request.state, "auth_subject", "anonymous"),
            auth_type=getattr(request.state, "auth_type", "unknown"),
            permission_key=permission_key,
        )

    @app.exception_handler(AgentError)
    async def handle_agent_error(request: Request, error: AgentError) -> JSONResponse:
        status_code = 500
        if error.category in {"validation", "parsing"}:
            status_code = 400
        elif error.category == "auth":
            status_code = 401 if error.code == "authentication_error" else 403
        elif error.category == "rate_limit":
            status_code = 429
        elif error.category == "conflict":
            status_code = 409
        elif error.category == "model":
            status_code = 502
        request.state.error_code = error.code
        if not error.trace_id and getattr(request.state, "trace_id", ""):
            error.with_trace_id(request.state.trace_id)
        return JSONResponse(status_code=status_code, content=build_error_response(error).model_dump())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail
        if isinstance(detail, dict) and {"category", "code", "message"} <= set(detail.keys()):
            payload = ErrorResponse(**detail)
        else:
            payload = ErrorResponse(
                category="http",
                code="http_error",
                message=sanitize_text(str(detail)),
                trace_id=getattr(request.state, "trace_id", None),
                details={},
            )
        request.state.error_code = payload.code
        return JSONResponse(status_code=error.status_code, content=payload.model_dump())

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/auth/me", response_model=AuthMeResponse)
    def get_auth_me(request: Request) -> AuthMeResponse:
        profile = get_auth_profile(request)
        return AuthMeResponse(
            profile=AuthProfilePayload(
                auth_subject=profile.subject,
                auth_type=profile.auth_type,
                roles=profile.roles,
                permissions=profile.permissions,
            )
        )

    @app.get("/auth/roles", response_model=AuthRoleListResponse)
    def list_auth_roles(request: Request) -> AuthRoleListResponse:
        require_permission(request, "auth.read")
        roles = auth_service.list_roles()
        permissions = auth_service.list_permissions()
        return AuthRoleListResponse(
            roles=[
                AuthRolePayload(
                    role_key=item["role_key"],
                    role_name=item["role_name"],
                    description=item["description"],
                    is_enabled=item["is_enabled"],
                )
                for item in roles
            ],
            permissions=[
                AuthPermissionPayload(
                    permission_key=item["permission_key"],
                    permission_name=item["permission_name"],
                    description=item["description"],
                )
                for item in permissions
            ],
        )

    @app.get("/auth/permissions/matrix", response_model=AuthPermissionMatrixResponse)
    def get_auth_permission_matrix(request: Request) -> AuthPermissionMatrixResponse:
        require_permission(request, "auth.read")
        roles = auth_service.list_roles()
        matrix = []
        for role in roles:
            permissions = auth_service.role_permission_repository.list_by_role_keys([role["role_key"]])
            matrix.append(
                AuthRolePermissionMatrixItemPayload(
                    role_key=role["role_key"],
                    role_name=role["role_name"],
                    permissions=sorted({item["permission_key"] for item in permissions}),
                )
            )
        return AuthPermissionMatrixResponse(matrix=matrix)

    @app.put("/auth/subjects/{auth_subject}/roles", response_model=AuthSubjectRoleAssignResponse, responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
    def assign_subject_roles(auth_subject: str, payload: AuthSubjectRoleAssignRequest, request: Request) -> AuthSubjectRoleAssignResponse:
        require_permission(request, "auth.role.assign")
        assignments = auth_service.assign_subject_roles(
            auth_subject=sanitize_text(auth_subject),
            role_keys=payload.role_keys,
            updated_by=sanitize_text(payload.updated_by) or getattr(request.state, "auth_subject", "api-auth"),
        )
        return AuthSubjectRoleAssignResponse(
            auth_subject=sanitize_text(auth_subject),
            role_keys=[item["role_key"] for item in assignments],
            assignments=[
                AuthSubjectRolePayload(
                    auth_subject=item["auth_subject"],
                    role_key=item["role_key"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in assignments
            ],
        )

    @app.get("/auth/subjects/{auth_subject}/roles", response_model=AuthSubjectAccessResponse, responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
    def get_subject_roles(auth_subject: str, request: Request) -> AuthSubjectAccessResponse:
        require_permission(request, "auth.read")
        normalized_subject = sanitize_text(auth_subject)
        assignments = auth_service.get_subject_assignments(auth_subject=normalized_subject)
        profile = auth_service.get_authorization_profile(normalized_subject, "managed")
        return AuthSubjectAccessResponse(
            auth_subject=normalized_subject,
            roles=profile.roles,
            permissions=profile.permissions,
            assignments=[
                AuthSubjectRolePayload(
                    auth_subject=item["auth_subject"],
                    role_key=item["role_key"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in assignments
            ],
        )

    @app.post(
        "/chat",
        response_model=ChatResponse,
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        require_permission(request, "chat.execute")
        user_input = sanitize_text(payload.message)
        session_id = sanitize_text(payload.session_id or "")
        user_name = sanitize_text(payload.user_name) or "api-user"
        session_title = sanitize_text(payload.session_title) or "API Session"
        if not user_input:
            raise ValidationError("message 不能为空。")

        current_state = None
        try:
            normalized_user_input, input_assets = parse_input_assets(user_input)
            task_service.tool_registry = current_tool_registry()
            state = session_service.ensure_session(session_id or None, user_name=user_name, title=session_title)
            route_decision = request_route_service.decide(
                user_input=normalized_user_input,
                input_assets=input_assets,
                message_count=len(state["messages"]) + 1,
                route_source="request_entry",
            )
            current_state = task_service.prepare_turn_state(
                state,
                normalized_user_input,
                input_assets,
                trace_id=request.state.trace_id,
                route_name=route_decision["route_name"],
                route_reason=route_decision["route_reason"],
                route_source=route_decision["route_source"],
            )
            result = graph.invoke(current_state)
            session_service.persist_turn(result)
            trace_service.attach_execution_context(
                result["trace_id"],
                session_id=result["session_id"],
                turn_id=result["turn_id"],
                task_id=result["task_id"],
            )
            return ChatResponse(
                session_id=result["session_id"],
                turn_id=result["turn_id"],
                task_id=result["task_id"],
                trace_id=result["trace_id"],
                execution_mode=result["execution_mode"],
                protocol_summary=result["protocol_summary"],
                route_name=result["route_name"],
                route_reason=result["route_reason"],
                plan=result["plan"],
                debate_summary=result["debate_summary"],
                arbitration_summary=result["arbitration_summary"],
                answer=result["answer"],
                critic_summary=result["critic_summary"],
                review_status=result["review_status"],
                review_summary=result["review_summary"],
                tool_names=result["runtime_context"]["tools"],
                asset_count=len(result["input_assets"]),
            )
        except ParsingError:
            raise
        except LLMCallError as error:
            error.with_trace_id(current_state["trace_id"] if current_state is not None else getattr(request.state, "trace_id", None))
            persist_failed_task_if_possible(current_state, error)
            raise error
        except AgentError as error:
            error.with_trace_id(current_state["trace_id"] if current_state is not None else getattr(request.state, "trace_id", error.trace_id))
            persist_failed_task_if_possible(current_state, error)
            raise error
        except Exception as error:
            logger.exception("API /chat 发生未预期异常")
            unexpected = AgentError(
                "system",
                "unexpected_error",
                sanitize_text(str(error)),
                trace_id=current_state["trace_id"] if current_state is not None else getattr(request.state, "trace_id", None),
            )
            persist_failed_task_if_possible(current_state, unexpected)
            raise unexpected from error

    @app.post(
        "/tasks/submit",
        response_model=AsyncTaskSubmitResponse,
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def submit_task(payload: AsyncTaskSubmitRequest, request: Request) -> AsyncTaskSubmitResponse:
        require_permission(request, "task.submit")
        if not is_async_task_enabled():
            raise ValidationError("????????????????")

        user_input = sanitize_text(payload.message)
        session_id = sanitize_text(payload.session_id or "")
        user_name = sanitize_text(payload.user_name) or "api-user"
        session_title = sanitize_text(payload.session_title) or "Async Task Session"
        if not user_input:
            raise ValidationError("message ?????")

        current_state = prepare_async_state(
            user_input=user_input,
            session_id=session_id,
            user_name=user_name,
            session_title=session_title,
            trace_id=request.state.trace_id,
        )
        async_task_service.submit_turn(current_state)
        trace_service.attach_execution_context(
            current_state["trace_id"],
            session_id=current_state["session_id"],
            turn_id=current_state["turn_id"],
            task_id=current_state["task_id"],
        )
        return AsyncTaskSubmitResponse(
            session_id=current_state["session_id"],
            turn_id=current_state["turn_id"],
            task_id=current_state["task_id"],
            trace_id=current_state["trace_id"],
            status="queued",
            message="???????????????",
        )

    @app.post(
        "/tasks/{task_id}/retry",
        response_model=AsyncTaskSubmitResponse,
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def retry_task(task_id: str, request: Request) -> AsyncTaskSubmitResponse:
        require_permission(request, "task.submit")
        if not is_async_task_enabled():
            raise ValidationError("????????????????")

        retried = async_task_service.retry_turn(
            sanitize_text(task_id),
            trace_id=request.state.trace_id,
        )
        return AsyncTaskSubmitResponse(**retried)

    @app.get("/tasks/runtime", response_model=AsyncTaskRuntimeResponse)
    def get_async_task_runtime(request: Request) -> AsyncTaskRuntimeResponse:
        require_permission(request, "task.read")
        snapshot = async_task_service.get_runtime_snapshot()
        return AsyncTaskRuntimeResponse(
            async_task_enabled=is_async_task_enabled(),
            runtime=AsyncTaskRuntimePayload(
                max_workers=snapshot["max_workers"],
                active_task_count=snapshot["active_task_count"],
                active_task_ids=snapshot["active_task_ids"],
            ),
        )

    @app.post("/tasks/{task_id}/cancel", response_model=TaskResponse, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
    def cancel_task(task_id: str, request: Request) -> TaskResponse:
        require_permission(request, "task.submit")
        canceled = async_task_service.cancel_turn(
            sanitize_text(task_id),
            updated_by=getattr(request.state, "auth_subject", "api-task"),
        )
        return TaskResponse(**canceled)

    @app.post(
        "/chat/stream",
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def chat_stream(payload: ChatRequest, request: Request):
        require_permission(request, "chat.execute")
        user_input = sanitize_text(payload.message)
        session_id = sanitize_text(payload.session_id or "")
        user_name = sanitize_text(payload.user_name) or "api-user"
        session_title = sanitize_text(payload.session_title) or "API Session"
        if not user_input:
            raise ValidationError("message 不能为空。")

        normalized_user_input, input_assets = parse_input_assets(user_input)
        task_service.tool_registry = current_tool_registry()
        state = session_service.ensure_session(session_id or None, user_name=user_name, title=session_title)
        route_decision = request_route_service.decide(
            user_input=normalized_user_input,
            input_assets=input_assets,
            message_count=len(state["messages"]) + 1,
            route_source="request_entry",
        )
        current_state = task_service.prepare_turn_state(
            state,
            normalized_user_input,
            input_assets,
            trace_id=request.state.trace_id,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            route_source=route_decision["route_source"],
        )

        def encode_event(event_name: str, payload_dict: dict[str, object]) -> str:
            return f"event: {event_name}\ndata: {json.dumps(payload_dict, ensure_ascii=False)}\n\n"

        def event_stream():
            try:
                for event in chat_service.stream_turn_events(current_state):
                    if event["type"] == "metadata":
                        yield encode_event(
                            "metadata",
                            {
                                "session_id": event["session_id"],
                                "turn_id": event["turn_id"],
                                "task_id": event["task_id"],
                                "trace_id": event["trace_id"],
                                "route_name": event["route_name"],
                                "route_reason": event["route_reason"],
                                "execution_mode": event["execution_mode"],
                                "protocol_summary": event["protocol_summary"],
                            },
                        )
                    elif event["type"] == "answer_delta":
                        yield encode_event("answer_delta", {"delta": event["delta"]})
                    elif event["type"] == "done":
                        final_state = event["state"]
                        session_service.persist_turn(final_state)
                        trace_service.attach_execution_context(
                            final_state["trace_id"],
                            session_id=final_state["session_id"],
                            turn_id=final_state["turn_id"],
                            task_id=final_state["task_id"],
                        )
                        yield encode_event(
                            "done",
                            {
                                "session_id": final_state["session_id"],
                                "turn_id": final_state["turn_id"],
                                "task_id": final_state["task_id"],
                                "trace_id": final_state["trace_id"],
                                "answer": final_state["answer"],
                                "review_status": final_state["review_status"],
                                "review_summary": final_state["review_summary"],
                            },
                        )
            except ParsingError as error:
                yield encode_event("error", build_error_response(error).model_dump())
            except LLMCallError as error:
                error.with_trace_id(current_state["trace_id"])
                persist_failed_task_if_possible(current_state, error)
                yield encode_event("error", build_error_response(error).model_dump())
            except AgentError as error:
                error.with_trace_id(current_state["trace_id"])
                persist_failed_task_if_possible(current_state, error)
                yield encode_event("error", build_error_response(error).model_dump())
            except Exception as error:
                logger.exception("API /chat/stream 发生未预期异常")
                unexpected = AgentError(
                    "system",
                    "unexpected_error",
                    sanitize_text(str(error)),
                    trace_id=current_state["trace_id"],
                )
                persist_failed_task_if_possible(current_state, unexpected)
                yield encode_event("error", build_error_response(unexpected).model_dump())

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/sessions", response_model=SessionListResponse)
    def list_sessions(request: Request, limit: int = 20, offset: int = 0) -> SessionListResponse:
        require_permission(request, "session.read")
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        sessions = session_service.list_sessions(limit=normalized_limit, offset=normalized_offset)
        return SessionListResponse(sessions=sessions)

    @app.get("/sessions/{session_id}", response_model=SessionResponse, responses={404: {"model": ErrorResponse}})
    def get_session(session_id: str, request: Request) -> SessionResponse:
        require_permission(request, "session.read")
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        return SessionResponse(**bundle)

    @app.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse, responses={404: {"model": ErrorResponse}})
    def get_session_summary(session_id: str, request: Request, task_limit: int = 20, task_offset: int = 0) -> SessionSummaryResponse:
        require_permission(request, "session.read")
        normalized_session_id = sanitize_text(session_id)
        bundle = session_service.get_session_bundle(normalized_session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        tasks = session_service.list_tasks_by_session(
            normalized_session_id,
            limit=max(1, min(task_limit, 100)),
            offset=max(0, task_offset),
        )
        return SessionSummaryResponse(
            summary=SessionSummaryPayload(
                session=SessionPayload(**bundle["session"]),
                messages=[MessagePayload(**item) for item in bundle["messages"]],
                assets=[AssetPayload(**item) for item in bundle["assets"]],
                tasks=[TaskPayload(**item["task"]) for item in tasks],
            )
        )

    @app.get("/sessions/{session_id}/assets", response_model=AssetListResponse, responses={404: {"model": ErrorResponse}})
    def list_assets_by_session(session_id: str, request: Request) -> AssetListResponse:
        require_permission(request, "session.read")
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        return AssetListResponse(assets=[AssetPayload(**asset) for asset in bundle["assets"]])

    @app.get("/assets/{asset_id}", response_model=AssetResponse, responses={404: {"model": ErrorResponse}})
    def get_asset(asset_id: str, request: Request) -> AssetResponse:
        require_permission(request, "session.read")
        asset = session_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=ValidationError("资产不存在。").to_dict())
        return AssetResponse(asset=AssetPayload(**asset))

    @app.get("/tools", response_model=ToolListResponse)
    def list_tools(request: Request) -> ToolListResponse:
        require_permission(request, "tool.read")
        descriptions = current_tool_registry().get_tool_descriptions()
        return ToolListResponse(
            tools=[ToolInfoPayload(name=name, description=description) for name, description in descriptions.items()]
        )

    @app.get("/workflow/config", response_model=WorkflowConfigResponse)
    def get_workflow_config(request: Request) -> WorkflowConfigResponse:
        require_permission(request, "workflow.read")
        registry = build_workflow_policy_registry(config_service, workflow_role_service)
        return WorkflowConfigResponse(
            workflow=WorkflowConfigPayload(
                execution_mode=registry.execution_mode,
                deliberation_enabled=registry.deliberation_enabled,
                deliberation_keywords=registry.deliberation_keywords,
                support_role=WorkflowRolePayload(
                    role_key="support",
                    name=registry.support_role.name,
                    stance_instruction=registry.support_role.stance_instruction,
                ),
                challenge_role=WorkflowRolePayload(
                    role_key="challenge",
                    name=registry.challenge_role.name,
                    stance_instruction=registry.challenge_role.stance_instruction,
                ),
                planner_role=WorkflowRolePayload(
                    role_key="planner",
                    name=registry.planner_role.name,
                    stance_instruction=registry.planner_role.stance_instruction,
                ),
                executor_role=WorkflowRolePayload(
                    role_key="executor",
                    name=registry.executor_role.name,
                    stance_instruction=registry.executor_role.stance_instruction,
                ),
                arbitration_role=WorkflowRolePayload(
                    role_key="arbitration",
                    name=registry.arbitration_role.name,
                    stance_instruction=registry.arbitration_role.stance_instruction,
                ),
                critic_role=WorkflowRolePayload(
                    role_key="critic",
                    name=registry.critic_role.name,
                    stance_instruction=registry.critic_role.stance_instruction,
                ),
                reviewer_role=WorkflowRolePayload(
                    role_key="reviewer",
                    name=registry.reviewer_role.name,
                    stance_instruction=registry.reviewer_role.stance_instruction,
                ),
            )
        )

    @app.get("/workflow/roles", response_model=WorkflowRoleListResponse)
    def list_workflow_roles(request: Request, enabled_only: bool = False) -> WorkflowRoleListResponse:
        require_permission(request, "workflow.read")
        roles = workflow_role_service.list_roles(only_enabled=enabled_only)
        return WorkflowRoleListResponse(
            roles=[
                WorkflowRolePayload(
                    role_key=item["role_key"],
                    name=item["role_name"],
                    stance_instruction=item["role_instruction"],
                    is_enabled=item["is_enabled"],
                    sort_order=item["sort_order"],
                    role_type=item["role_type"],
                    description=item["description"],
                )
                for item in roles
            ]
        )

    @app.put("/workflow/roles/{role_key}", response_model=WorkflowRoleUpsertResponse, responses={400: {"model": ErrorResponse}})
    def upsert_workflow_role(role_key: str, payload: WorkflowRoleUpsertRequest, request: Request) -> WorkflowRoleUpsertResponse:
        require_permission(request, "workflow_role.write")
        normalized_role_key = sanitize_text(role_key)
        if not normalized_role_key:
            raise ValidationError("role_key 不能为空。")
        role = workflow_role_service.upsert_role(
            role_key=normalized_role_key,
            role_name=sanitize_text(payload.name),
            role_instruction=sanitize_text(payload.stance_instruction),
            is_enabled=payload.is_enabled,
            sort_order=max(1, payload.sort_order),
            role_type=sanitize_text(payload.role_type) or "custom",
            description=sanitize_text(payload.description),
            updated_by=sanitize_text(payload.updated_by) or "api-role",
        )
        return WorkflowRoleUpsertResponse(
            role=WorkflowRolePayload(
                role_key=role["role_key"],
                name=role["role_name"],
                stance_instruction=role["role_instruction"],
                is_enabled=role["is_enabled"],
                sort_order=role["sort_order"],
                role_type=role["role_type"],
                description=role["description"],
            )
        )

    @app.get("/security/config", response_model=SecurityConfigResponse)
    def get_security_config(request: Request) -> SecurityConfigResponse:
        require_permission(request, "config.read")
        effective_security = config_service.get_effective_security_config()
        return SecurityConfigResponse(
            security=SecurityConfigPayload(
                allowed_tools=effective_security["allowed_tools"],
                upload_allowed_kinds=effective_security["upload_allowed_kinds"],
                upload_max_bytes=effective_security["upload_max_bytes"],
                auth_enabled=effective_security["auth_enabled"],
                rate_limit_enabled=effective_security["rate_limit_enabled"],
                idempotency_enabled=effective_security["idempotency_enabled"],
            )
        )

    @app.get("/recovery/config", response_model=RecoveryConfigResponse)
    def get_recovery_config(request: Request) -> RecoveryConfigResponse:
        require_permission(request, "config.read")
        effective_recovery = config_service.get_effective_recovery_config()
        return RecoveryConfigResponse(
            recovery=RecoveryConfigPayload(
                llm_degrade_to_mock=effective_recovery["llm_degrade_to_mock"],
                tool_soft_fail=effective_recovery["tool_soft_fail"],
            )
        )

    @app.get("/routing/config", response_model=RoutingConfigResponse)
    def get_routing_config(request: Request) -> RoutingConfigResponse:
        require_permission(request, "config.read")
        effective_routing = config_service.get_effective_routing_config()
        return RoutingConfigResponse(
            routing=RoutingConfigPayload(
                image_route=RoutingRulePayload(
                    route_name=effective_routing["image_route_name"],
                    route_reason=effective_routing["image_route_reason"],
                ),
                audio_route=RoutingRulePayload(
                    route_name=effective_routing["audio_route_name"],
                    route_reason=effective_routing["audio_route_reason"],
                ),
                video_route=RoutingRulePayload(
                    route_name=effective_routing["video_route_name"],
                    route_reason=effective_routing["video_route_reason"],
                ),
                file_route=RoutingRulePayload(
                    route_name=effective_routing["file_route_name"],
                    route_reason=effective_routing["file_route_reason"],
                ),
                tool_augmented_route=RoutingRulePayload(
                    route_name=effective_routing["tool_augmented_route_name"],
                    route_reason=effective_routing["tool_augmented_route_reason"],
                ),
                deliberation_route=RoutingDecisionRulePayload(
                    route_name=effective_routing["deliberation_route_name"],
                    route_reason=effective_routing["deliberation_route_reason"],
                    enabled=effective_routing["deliberation_enabled"],
                    keywords=effective_routing["deliberation_keywords"],
                    message_threshold=0,
                ),
                contextual_route=RoutingDecisionRulePayload(
                    route_name=effective_routing["contextual_route_name"],
                    route_reason=effective_routing["contextual_route_reason"],
                    enabled=effective_routing["contextual_message_threshold"] > 0,
                    keywords=[],
                    message_threshold=effective_routing["contextual_message_threshold"],
                ),
                default_route=RoutingRulePayload(
                    route_name=effective_routing["default_route_name"],
                    route_reason=effective_routing["default_route_reason"],
                ),
            )
        )

    @app.get("/routing/config/template", response_model=RoutingConfigTemplateResponse)
    def get_routing_config_template(request: Request) -> RoutingConfigTemplateResponse:
        require_permission(request, "config.read")
        definitions = config_service.get_routing_config_template()
        return RoutingConfigTemplateResponse(
            templates=[
                RoutingConfigTemplateItemPayload(
                    config_key=key,
                    value_type=item["value_type"],
                    description=item["description"],
                    example_value=item["example_value"],
                )
                for key, item in definitions.items()
            ]
        )

    @app.post("/routing/preview", response_model=RoutingPreviewResponse, responses={400: {"model": ErrorResponse}})
    def preview_routing(payload: RoutingPreviewRequest, request: Request) -> RoutingPreviewResponse:
        require_permission(request, "task.read")
        raw_input = sanitize_text(payload.input)
        if not raw_input:
            raise ValidationError("input 不能为空。")
        normalized_user_input, input_assets = parse_input_assets(raw_input)
        route_decision = request_route_service.decide(
            user_input=normalized_user_input,
            input_assets=input_assets,
            message_count=max(0, payload.message_count),
            route_source=sanitize_text(payload.route_source) or "preview",
        )
        return RoutingPreviewResponse(
            user_input=normalized_user_input,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            route_source=route_decision["route_source"],
            input_assets=input_assets,
        )

    @app.get("/config/runtime", response_model=RuntimeConfigListResponse)
    def list_runtime_configs(request: Request, scope: str | None = None) -> RuntimeConfigListResponse:
        require_permission(request, "config.read")
        normalized_scope = sanitize_text(scope or "") or None
        configs = config_service.list_configs(scope=normalized_scope)
        return RuntimeConfigListResponse(
            configs=[
                RuntimeConfigItemPayload(
                    id=item["id"],
                    config_scope=item["config_scope"],
                    config_key=item["config_key"],
                    config_value=item["config_value"],
                    value_type=item["value_type"],
                    config_source=item["config_source"],
                    description=item["description"],
                    created_by=item["created_by"],
                    updated_by=item["updated_by"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in configs
            ]
        )

    @app.get("/config/runtime/events", response_model=RuntimeConfigEventListResponse)
    def list_runtime_config_events(
        request: Request,
        scope: str | None = None,
        key: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> RuntimeConfigEventListResponse:
        require_permission(request, "config.read")
        events = config_service.repository.list_config_events(
            scope=sanitize_text(scope or "") or None,
            key=sanitize_text(key or "") or None,
            limit=max(1, min(limit, 200)),
            offset=max(0, offset),
        )
        return RuntimeConfigEventListResponse(
            events=[
                RuntimeConfigEventPayload(
                    id=item["id"],
                    config_scope=item["config_scope"],
                    config_key=item["config_key"],
                    action_type=item["action_type"],
                    old_value=item["old_value"],
                    new_value=item["new_value"],
                    value_type=item["value_type"],
                    description=item["description"],
                    created_by=item["created_by"],
                    updated_by=item["updated_by"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in events
            ]
        )

    @app.put("/config/runtime", response_model=RuntimeConfigUpsertResponse, responses={400: {"model": ErrorResponse}})
    def upsert_runtime_config(payload: RuntimeConfigUpsertRequest, request: Request) -> RuntimeConfigUpsertResponse:
        require_permission(request, "config.write")
        if not payload.config_scope or not payload.config_key:
            raise ValidationError("config_scope 和 config_key 不能为空。")
        config_service.validate_config_entry(
            scope=sanitize_text(payload.config_scope),
            key=sanitize_text(payload.config_key),
            value=sanitize_text(payload.config_value),
            value_type=sanitize_text(payload.value_type),
        )
        item = config_service.upsert_config(
            scope=sanitize_text(payload.config_scope),
            key=sanitize_text(payload.config_key),
            value=sanitize_text(payload.config_value),
            value_type=sanitize_text(payload.value_type),
            description=sanitize_text(payload.description),
            updated_by=sanitize_text(payload.updated_by) or "api-config",
        )
        refreshed_tool_registry = build_default_tool_registry(config_service)
        task_service.tool_registry = refreshed_tool_registry
        return RuntimeConfigUpsertResponse(
            config=RuntimeConfigItemPayload(
                id=item["id"],
                config_scope=item["config_scope"],
                config_key=item["config_key"],
                config_value=item["config_value"],
                value_type=item["value_type"],
                config_source=item["config_source"],
                description=item["description"],
                created_by=item["created_by"],
                updated_by=item["updated_by"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
        )

    @app.post("/tools/{tool_name}/execute", response_model=ToolExecuteResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
    def execute_tool(tool_name: str, payload: ToolExecuteRequest, request: Request) -> ToolExecuteResponse:
        require_permission(request, "tool.execute")
        normalized_tool_name = sanitize_text(tool_name)
        if not normalized_tool_name:
            raise ValidationError("tool_name 不能为空。")
        trace_id = sanitize_text(payload.trace_id or "") or request.state.trace_id
        result = current_tool_registry().execute(normalized_tool_name, trace_id, payload.parameters)
        return ToolExecuteResponse(result=result)

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks(request: Request, status: str | None = None, session_id: str | None = None, limit: int = 20, offset: int = 0) -> TaskListResponse:
        require_permission(request, "task.read")
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        normalized_status = sanitize_text(status or "") or None
        normalized_session_id = sanitize_text(session_id or "") or None
        tasks = session_service.list_tasks(
            status=normalized_status,
            session_id=normalized_session_id,
            limit=normalized_limit,
            offset=normalized_offset,
        )
        return TaskListResponse(tasks=[TaskResponse(**task) for task in tasks])

    @app.get("/tasks/stats", response_model=TaskStatsResponse)
    def get_task_stats(request: Request, session_id: str | None = None) -> TaskStatsResponse:
        require_permission(request, "task.read")
        normalized_session_id = sanitize_text(session_id or "") or None
        stats = session_service.list_task_status_stats(session_id=normalized_session_id)
        return TaskStatsResponse(
            summary=TaskStatsPayload(
                session_id=normalized_session_id,
                stats=[
                    TaskStatusStatPayload(
                        status=item["status"],
                        task_count=item["task_count"],
                        last_updated_at=item["last_updated_at"] or "",
                    )
                    for item in stats
                ],
            )
        )

    @app.get("/operations/overview", response_model=OperationsOverviewResponse)
    def get_operations_overview(request: Request) -> OperationsOverviewResponse:
        require_permission(request, "task.read")
        require_permission(request, "alert.read")
        task_stats = session_service.list_task_status_stats()
        runtime = async_task_service.get_runtime_snapshot()
        recent_tasks = session_service.list_tasks(limit=5, offset=0)
        route_stats = session_service.list_route_decision_stats(limit=5, offset=0)
        recent_alerts = alert_service.list_alerts(limit=5, offset=0)
        return OperationsOverviewResponse(
            summary=OperationsOverviewPayload(
                task_stats=[
                    TaskStatusStatPayload(
                        status=item["status"],
                        task_count=item["task_count"],
                        last_updated_at=item["last_updated_at"] or "",
                    )
                    for item in task_stats
                ],
                runtime=AsyncTaskRuntimePayload(
                    max_workers=int(runtime["max_workers"]),
                    active_task_count=int(runtime["active_task_count"]),
                    active_task_ids=list(runtime["active_task_ids"]),
                ),
                recent_tasks=[TaskPayload(**item["task"]) for item in recent_tasks],
                route_stats=[
                    RouteDecisionStatPayload(
                        route_name=item["route_name"],
                        route_source=item["route_source"],
                        decision_count=item["decision_count"],
                        last_trace_id=item["last_trace_id"],
                        last_task_id=item["last_task_id"],
                        last_decided_at=item["last_decided_at"],
                    )
                    for item in route_stats
                ],
                recent_alerts=[
                    AlertEventPayload(
                        id=item["id"],
                        trace_id=item["trace_id"],
                        source_type=item["source_type"],
                        source_name=item["source_name"],
                        severity=item["severity"],
                        event_code=item["event_code"],
                        message=item["message"],
                        payload_json=item["payload_json"],
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                    )
                    for item in recent_alerts
                ],
            )
        )

    @app.get("/sessions/{session_id}/tasks", response_model=TaskListResponse, responses={404: {"model": ErrorResponse}})
    def list_tasks_by_session(session_id: str, request: Request, limit: int = 20, offset: int = 0) -> TaskListResponse:
        require_permission(request, "task.read")
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        tasks = session_service.list_tasks_by_session(session_id, limit=normalized_limit, offset=normalized_offset)
        return TaskListResponse(tasks=[TaskResponse(**task) for task in tasks])

    @app.get("/tasks/{task_id}", response_model=TaskResponse, responses={404: {"model": ErrorResponse}})
    def get_task(task_id: str, request: Request) -> TaskResponse:
        require_permission(request, "task.read")
        task = session_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=ValidationError("任务不存在。").to_dict())
        return TaskResponse(**task)


    @app.get("/tasks/{task_id}/summary", response_model=TaskSummaryResponse, responses={404: {"model": ErrorResponse}})
    def get_task_summary(task_id: str, request: Request) -> TaskSummaryResponse:
        require_permission(request, "task.read")
        normalized_task_id = sanitize_text(task_id)
        task_bundle = session_service.get_task(normalized_task_id)
        if not task_bundle:
            raise HTTPException(status_code=404, detail=ValidationError("??????").to_dict())

        task = task_bundle["task"]
        trace = trace_service.get_trace(task["trace_id"]) if task["trace_id"] else None
        alerts = alert_service.list_alerts(trace_id=task["trace_id"], limit=100, offset=0) if task["trace_id"] else []
        return TaskSummaryResponse(
            summary=TaskSummaryPayload(
                task=TaskPayload(**task),
                trace=TracePayload(**trace) if trace else None,
                task_events=[TaskEventPayload(**item) for item in task_bundle["task_events"]],
                tool_results=[ToolResultPayload(**item) for item in task_bundle["tool_results"]],
                route_decisions=[RouteDecisionPayload(**item) for item in task_bundle["route_decisions"]],
                alerts=[AlertEventPayload(**item) for item in alerts],
            )
        )
    @app.get("/tasks/{task_id}/events", response_model=TaskEventListResponse, responses={404: {"model": ErrorResponse}})
    def get_task_events(task_id: str, request: Request, limit: int = 100, offset: int = 0) -> TaskEventListResponse:
        require_permission(request, "task.read")
        task = session_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=ValidationError("任务不存在。").to_dict())
        events = session_service.list_task_events(task_id, limit=max(1, min(limit, 200)), offset=max(0, offset))
        return TaskEventListResponse(
            task_events=[
                TaskEventPayload(
                    id=item["id"],
                    task_id=item["task_id"],
                    session_id=item["session_id"],
                    turn_id=item["turn_id"],
                    trace_id=item["trace_id"],
                    event_type=item["event_type"],
                    event_message=item["event_message"],
                    event_payload_json=item["event_payload_json"],
                    created_at=item["created_at"],
                )
                for item in events
            ]
        )

    @app.get("/tasks/{task_id}/routes", response_model=RouteDecisionListResponse, responses={404: {"model": ErrorResponse}})
    def get_task_routes(task_id: str, request: Request) -> RouteDecisionListResponse:
        require_permission(request, "task.read")
        task = session_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=ValidationError("任务不存在。").to_dict())
        return RouteDecisionListResponse(route_decisions=task["route_decisions"])

    @app.get("/routes", response_model=RouteDecisionListResponse)
    def list_route_decisions(
        request: Request,
        task_id: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> RouteDecisionListResponse:
        require_permission(request, "task.read")
        decisions = session_service.list_route_decisions(
            task_id=sanitize_text(task_id or "") or None,
            session_id=sanitize_text(session_id or "") or None,
            trace_id=sanitize_text(trace_id or "") or None,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return RouteDecisionListResponse(route_decisions=decisions)

    @app.get("/routes/stats", response_model=RouteDecisionStatsResponse)
    def list_route_decision_stats(
        request: Request,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> RouteDecisionStatsResponse:
        require_permission(request, "task.read")
        stats = session_service.list_route_decision_stats(
            session_id=sanitize_text(session_id or "") or None,
            trace_id=sanitize_text(trace_id or "") or None,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return RouteDecisionStatsResponse(
            stats=[
                RouteDecisionStatPayload(
                    route_name=item["route_name"],
                    route_source=item["route_source"],
                    decision_count=item["decision_count"],
                    last_trace_id=item["last_trace_id"],
                    last_task_id=item["last_task_id"],
                    last_decided_at=item["last_decided_at"],
                )
                for item in stats
            ]
        )

    @app.get("/traces/stats", response_model=TraceStatsResponse)
    def list_trace_stats(
        request: Request,
        method: str | None = None,
        path: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TraceStatsResponse:
        require_permission(request, "trace.read")
        stats = trace_service.list_trace_stats(
            method=sanitize_text(method or "") or None,
            path=sanitize_text(path or "") or None,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return TraceStatsResponse(
            stats=[
                TraceStatPayload(
                    method=item["method"],
                    path=item["path"],
                    status_code=item["status_code"],
                    rate_limited=item["rate_limited"],
                    trace_count=item["trace_count"],
                    last_started_at=item["last_started_at"] or "",
                )
                for item in stats
            ]
        )

    @app.get("/traces/{trace_id}", response_model=TraceResponse, responses={404: {"model": ErrorResponse}})
    def get_trace(trace_id: str, request: Request) -> TraceResponse:
        require_permission(request, "trace.read")
        trace = trace_service.get_trace(sanitize_text(trace_id))
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())
        return TraceResponse(trace=TracePayload(**trace))

    @app.get("/traces/{trace_id}/summary", response_model=TraceSummaryResponse, responses={404: {"model": ErrorResponse}})
    def get_trace_summary(trace_id: str, request: Request) -> TraceSummaryResponse:
        require_permission(request, "trace.read")
        normalized_trace_id = sanitize_text(trace_id)
        trace = trace_service.get_trace(normalized_trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())

        task_bundle = session_service.get_task(trace["task_id"]) if trace["task_id"] else None
        route_decisions = task_bundle["route_decisions"] if task_bundle else session_service.list_route_decisions(trace_id=normalized_trace_id, limit=100, offset=0)
        task_events = task_bundle["task_events"] if task_bundle else []
        tool_results = task_bundle["tool_results"] if task_bundle else []
        alerts = alert_service.list_alerts(trace_id=normalized_trace_id, limit=100, offset=0)

        return TraceSummaryResponse(
            summary=TraceSummaryPayload(
                trace=TracePayload(**trace),
                task=TaskPayload(**task_bundle["task"]) if task_bundle else None,
                task_events=[
                    TaskEventPayload(
                        id=item["id"],
                        task_id=item["task_id"],
                        session_id=item["session_id"],
                        turn_id=item["turn_id"],
                        trace_id=item["trace_id"],
                        event_type=item["event_type"],
                        event_message=item["event_message"],
                        event_payload_json=item["event_payload_json"],
                        created_at=item["created_at"],
                    )
                    for item in task_events
                ],
                tool_results=[
                    ToolResultPayload(
                        id=item["id"],
                        task_id=item["task_id"],
                        session_id=item["session_id"],
                        turn_id=item["turn_id"],
                        trace_id=item["trace_id"],
                        tool_name=item["tool_name"],
                        success=item["success"],
                        exit_code=item["exit_code"],
                        stdout=item["stdout"],
                        stderr=item["stderr"],
                        created_at=item["created_at"],
                    )
                    for item in tool_results
                ],
                route_decisions=[
                    RouteDecisionPayload(
                        id=item["id"],
                        task_id=item["task_id"],
                        session_id=item["session_id"],
                        turn_id=item["turn_id"],
                        trace_id=item["trace_id"],
                        route_name=item["route_name"],
                        route_reason=item["route_reason"],
                        route_source=item["route_source"],
                        created_at=item["created_at"],
                    )
                    for item in route_decisions
                ],
                alerts=[
                    AlertEventPayload(
                        id=item["id"],
                        trace_id=item["trace_id"],
                        source_type=item["source_type"],
                        source_name=item["source_name"],
                        severity=item["severity"],
                        event_code=item["event_code"],
                        message=item["message"],
                        payload_json=item["payload_json"],
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                    )
                    for item in alerts
                ],
            )
        )

    @app.get("/traces/{trace_id}/timeline", response_model=TraceTimelineResponse, responses={404: {"model": ErrorResponse}})
    def get_trace_timeline(trace_id: str, request: Request) -> TraceTimelineResponse:
        require_permission(request, "trace.read")
        normalized_trace_id = sanitize_text(trace_id)
        trace = trace_service.get_trace(normalized_trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())

        task_bundle = session_service.get_task(trace["task_id"]) if trace["task_id"] else None
        route_decisions = task_bundle["route_decisions"] if task_bundle else session_service.list_route_decisions(trace_id=normalized_trace_id, limit=100, offset=0)
        task_events = task_bundle["task_events"] if task_bundle else []
        tool_results = task_bundle["tool_results"] if task_bundle else []
        alerts = alert_service.list_alerts(trace_id=normalized_trace_id, limit=100, offset=0)
        return TraceTimelineResponse(
            trace=TracePayload(**trace),
            events=_build_trace_timeline_events(
                trace,
                task_bundle,
                route_decisions,
                task_events,
                tool_results,
                alerts,
            ),
        )

    @app.get("/traces/{trace_id}/graph", response_model=TraceGraphResponse, responses={404: {"model": ErrorResponse}})
    def get_trace_graph(trace_id: str, request: Request) -> TraceGraphResponse:
        require_permission(request, "trace.read")
        normalized_trace_id = sanitize_text(trace_id)
        trace = trace_service.get_trace(normalized_trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())

        task_bundle = session_service.get_task(trace["task_id"]) if trace["task_id"] else None
        route_decisions = task_bundle["route_decisions"] if task_bundle else session_service.list_route_decisions(trace_id=normalized_trace_id, limit=100, offset=0)
        tool_results = task_bundle["tool_results"] if task_bundle else []
        alerts = alert_service.list_alerts(trace_id=normalized_trace_id, limit=100, offset=0)
        nodes, edges = _build_trace_graph(trace, task_bundle, route_decisions, tool_results, alerts)
        return TraceGraphResponse(trace=TracePayload(**trace), nodes=nodes, edges=edges)

    @app.get("/alerts", response_model=AlertEventListResponse)
    def list_alerts(
        request: Request,
        severity: str | None = None,
        source_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AlertEventListResponse:
        require_permission(request, "alert.read")
        alerts = alert_service.list_alerts(
            severity=sanitize_text(severity or "") or None,
            source_type=sanitize_text(source_type or "") or None,
            trace_id=sanitize_text(trace_id or "") or None,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return AlertEventListResponse(
            alerts=[
                AlertEventPayload(
                    id=item["id"],
                    trace_id=item["trace_id"],
                    source_type=item["source_type"],
                    source_name=item["source_name"],
                    severity=item["severity"],
                    event_code=item["event_code"],
                    message=item["message"],
                    payload_json=item["payload_json"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in alerts
            ]
        )

    @app.get("/alerts/stats", response_model=AlertStatsResponse)
    def list_alert_stats(
        request: Request,
        source_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> AlertStatsResponse:
        require_permission(request, "alert.read")
        stats = alert_service.list_alert_stats(
            source_type=sanitize_text(source_type or "") or None,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return AlertStatsResponse(
            stats=[
                AlertStatPayload(
                    severity=item["severity"],
                    source_type=item["source_type"],
                    alert_count=item["alert_count"],
                    last_created_at=item["last_created_at"] or "",
                )
                for item in stats
            ]
        )

    @app.get("/alerts/{alert_id}", response_model=AlertEventResponse, responses={404: {"model": ErrorResponse}})
    def get_alert(alert_id: str, request: Request) -> AlertEventResponse:
        require_permission(request, "alert.read")
        alert = alert_service.get_alert(sanitize_text(alert_id))
        if not alert:
            raise HTTPException(status_code=404, detail=ValidationError("告警不存在。").to_dict())
        return AlertEventResponse(
            alert=AlertEventPayload(
                id=alert["id"],
                trace_id=alert["trace_id"],
                source_type=alert["source_type"],
                source_name=alert["source_name"],
                severity=alert["severity"],
                event_code=alert["event_code"],
                message=alert["message"],
                payload_json=alert["payload_json"],
                created_at=alert["created_at"],
                updated_at=alert["updated_at"],
            )
        )

    @app.get("/traces/{trace_id}/alerts", response_model=AlertEventListResponse, responses={404: {"model": ErrorResponse}})
    def list_trace_alerts(trace_id: str, request: Request) -> AlertEventListResponse:
        require_permission(request, "alert.read")
        normalized_trace_id = sanitize_text(trace_id)
        trace = trace_service.get_trace(normalized_trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())
        alerts = alert_service.list_alerts(trace_id=normalized_trace_id, limit=100, offset=0)
        return AlertEventListResponse(
            alerts=[
                AlertEventPayload(
                    id=item["id"],
                    trace_id=item["trace_id"],
                    source_type=item["source_type"],
                    source_name=item["source_name"],
                    severity=item["severity"],
                    event_code=item["event_code"],
                    message=item["message"],
                    payload_json=item["payload_json"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                )
                for item in alerts
            ]
        )

    @app.post("/assets/analyze", response_model=AnalyzeAssetResponse, responses={400: {"model": ErrorResponse}})
    def analyze_asset(payload: AnalyzeAssetRequest, request: Request) -> AnalyzeAssetResponse:
        require_permission(request, "asset.analyze")
        raw_input = sanitize_text(payload.input)
        if not raw_input:
            raise ValidationError("input 不能为空。")
        normalized_user_input, input_assets = parse_input_assets(raw_input)
        route_decision = request_route_service.decide(
            user_input=normalized_user_input,
            input_assets=input_assets,
            message_count=1,
            route_source="request_entry",
        )
        tool_results: list[dict[str, object]] = []
        task_state = ""
        if payload.run_tools:
            _, tool_results, task_state = preview_tools(normalized_user_input, input_assets, trace_id=request.state.trace_id)

        return AnalyzeAssetResponse(
            user_input=normalized_user_input,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            input_assets=input_assets,
            tool_results=tool_results,
            task_state=task_state,
            available_tools=current_tool_registry().list_tool_names(),
        )

    @app.post("/assets/upload", response_model=UploadAssetResponse, responses={400: {"model": ErrorResponse}})
    async def upload_asset(
        request: Request,
        file: UploadFile = File(...),
        kind: str = Form(default="auto"),
        prompt: str = Form(default=""),
        run_tools: bool = Form(default=False),
        session_id: str = Form(default=""),
        user_name: str = Form(default="upload-user"),
        session_title: str = Form(default="Upload Session"),
    ) -> UploadAssetResponse:
        require_permission(request, "asset.upload")
        if not file.filename:
            raise ValidationError("上传文件名不能为空。")
        file_bytes = await file.read()
        user_input, asset, inferred_kind, saved_path = create_uploaded_asset(
            filename=file.filename,
            data=file_bytes,
            content_type=file.content_type or "",
            kind=kind,
        )
        normalized_user_input = sanitize_text(prompt) or user_input
        input_assets = [asset]
        state = session_service.ensure_session(
            sanitize_text(session_id) or None,
            user_name=sanitize_text(user_name) or "upload-user",
            title=sanitize_text(session_title) or "Upload Session",
        )
        task_service.tool_registry = current_tool_registry()
        route_decision = request_route_service.decide(
            user_input=normalized_user_input,
            input_assets=input_assets,
            message_count=len(state["messages"]) + 1,
            route_source="request_entry",
        )
        current_state = task_service.prepare_turn_state(
            state,
            normalized_user_input,
            input_assets,
            trace_id=request.state.trace_id,
            route_name=route_decision["route_name"],
            route_reason=route_decision["route_reason"],
            route_source=route_decision["route_source"],
        )
        if run_tools:
            current_state = tool_node(current_state)
        session_service.persist_turn(current_state)
        trace_service.attach_execution_context(
            current_state["trace_id"],
            session_id=current_state["session_id"],
            turn_id=current_state["turn_id"],
            task_id=current_state["task_id"],
        )

        return UploadAssetResponse(
            session_id=current_state["session_id"],
            turn_id=current_state["turn_id"],
            task_id=current_state["task_id"],
            trace_id=current_state["trace_id"],
            upload_dir=str(get_upload_download_dir()),
            saved_path=saved_path,
            inferred_kind=inferred_kind,
            user_input=normalized_user_input,
            route_name=current_state["route_name"],
            route_reason=current_state["route_reason"],
            input_assets=current_state["input_assets"],
            tool_results=current_state["tool_results"],
            task_state=current_state["task_state"],
            available_tools=current_tool_registry().list_tool_names(),
        )

    return app
