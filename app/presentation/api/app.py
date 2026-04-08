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

from app.application.agent_service import create_initial_state, parse_input_assets
from app.application.services.alert_service import AlertService
from app.application.services.config_service import RuntimeConfigService
from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.application.services.workflow_role_service import WorkflowRoleService
from app.application.upload_service import create_uploaded_asset
from app.config import (
    get_upload_download_dir,
)
from app.domain.errors import AgentError, ParsingError, ValidationError
from app.infrastructure.auth import AuthService
from app.infrastructure.llm.client import LLMCallError, sanitize_text
from app.infrastructure.logger import get_logger
from app.infrastructure.tools.registry import build_default_tool_registry
from app.infrastructure.trace import TraceService
from app.presentation.api.middleware.auth import AuthMiddleware
from app.presentation.api.middleware.governance import GovernanceMiddleware, IdempotencyStore, RateLimiter
from app.presentation.api.middleware.trace import TraceMiddleware
from app.presentation.api.schemas import (
    AnalyzeAssetRequest,
    AnalyzeAssetResponse,
    AlertEventListResponse,
    AlertEventPayload,
    AlertEventResponse,
    AssetListResponse,
    AssetPayload,
    AssetResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    RuntimeConfigItemPayload,
    RuntimeConfigListResponse,
    RuntimeConfigUpsertRequest,
    RuntimeConfigUpsertResponse,
    SessionListResponse,
    SecurityConfigPayload,
    SecurityConfigResponse,
    SessionResponse,
    TaskListResponse,
    TaskResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolInfoPayload,
    ToolListResponse,
    TracePayload,
    TraceResponse,
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


def create_app():
    try:
        from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
        from fastapi.responses import JSONResponse
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
    auth_service = AuthService()
    trace_service = TraceService()
    graph = build_graph()
    app = FastAPI(title="Agent Base Runtime API", version="0.7.0")
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
        preview_state = task_service.prepare_turn_state(
            create_initial_state(user_id="preview-user"),
            user_input,
            input_assets,  # type: ignore[arg-type]
            trace_id=trace_id,
        )
        preview_state = tool_node(preview_state)
        return preview_state, preview_state["tool_results"], preview_state["task_state"]

    def current_tool_registry():
        return build_default_tool_registry(config_service)

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

    @app.post(
        "/chat",
        response_model=ChatResponse,
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def chat(payload: ChatRequest, request: Request) -> ChatResponse:
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
            current_state = task_service.prepare_turn_state(
                state,
                normalized_user_input,
                input_assets,
                trace_id=request.state.trace_id,
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

    @app.get("/sessions", response_model=SessionListResponse)
    def list_sessions(limit: int = 20, offset: int = 0) -> SessionListResponse:
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        sessions = session_service.list_sessions(limit=normalized_limit, offset=normalized_offset)
        return SessionListResponse(sessions=sessions)

    @app.get("/sessions/{session_id}", response_model=SessionResponse, responses={404: {"model": ErrorResponse}})
    def get_session(session_id: str) -> SessionResponse:
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        return SessionResponse(**bundle)

    @app.get("/sessions/{session_id}/assets", response_model=AssetListResponse, responses={404: {"model": ErrorResponse}})
    def list_assets_by_session(session_id: str) -> AssetListResponse:
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        return AssetListResponse(assets=[AssetPayload(**asset) for asset in bundle["assets"]])

    @app.get("/assets/{asset_id}", response_model=AssetResponse, responses={404: {"model": ErrorResponse}})
    def get_asset(asset_id: str) -> AssetResponse:
        asset = session_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=ValidationError("资产不存在。").to_dict())
        return AssetResponse(asset=AssetPayload(**asset))

    @app.get("/tools", response_model=ToolListResponse)
    def list_tools() -> ToolListResponse:
        descriptions = current_tool_registry().get_tool_descriptions()
        return ToolListResponse(
            tools=[ToolInfoPayload(name=name, description=description) for name, description in descriptions.items()]
        )

    @app.get("/workflow/config", response_model=WorkflowConfigResponse)
    def get_workflow_config() -> WorkflowConfigResponse:
        registry = build_workflow_policy_registry(config_service, workflow_role_service)
        return WorkflowConfigResponse(
            workflow=WorkflowConfigPayload(
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
            )
        )

    @app.get("/workflow/roles", response_model=WorkflowRoleListResponse)
    def list_workflow_roles(enabled_only: bool = False) -> WorkflowRoleListResponse:
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
    def upsert_workflow_role(role_key: str, payload: WorkflowRoleUpsertRequest) -> WorkflowRoleUpsertResponse:
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
    def get_security_config() -> SecurityConfigResponse:
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

    @app.get("/config/runtime", response_model=RuntimeConfigListResponse)
    def list_runtime_configs(scope: str | None = None) -> RuntimeConfigListResponse:
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

    @app.put("/config/runtime", response_model=RuntimeConfigUpsertResponse, responses={400: {"model": ErrorResponse}})
    def upsert_runtime_config(payload: RuntimeConfigUpsertRequest) -> RuntimeConfigUpsertResponse:
        if not payload.config_scope or not payload.config_key:
            raise ValidationError("config_scope 和 config_key 不能为空。")
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
        normalized_tool_name = sanitize_text(tool_name)
        if not normalized_tool_name:
            raise ValidationError("tool_name 不能为空。")
        trace_id = sanitize_text(payload.trace_id or "") or request.state.trace_id
        result = current_tool_registry().execute(normalized_tool_name, trace_id, payload.parameters)
        return ToolExecuteResponse(result=result)

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks(status: str | None = None, session_id: str | None = None, limit: int = 20, offset: int = 0) -> TaskListResponse:
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

    @app.get("/sessions/{session_id}/tasks", response_model=TaskListResponse, responses={404: {"model": ErrorResponse}})
    def list_tasks_by_session(session_id: str, limit: int = 20, offset: int = 0) -> TaskListResponse:
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        tasks = session_service.list_tasks_by_session(session_id, limit=normalized_limit, offset=normalized_offset)
        return TaskListResponse(tasks=[TaskResponse(**task) for task in tasks])

    @app.get("/tasks/{task_id}", response_model=TaskResponse, responses={404: {"model": ErrorResponse}})
    def get_task(task_id: str) -> TaskResponse:
        task = session_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=ValidationError("任务不存在。").to_dict())
        return TaskResponse(**task)

    @app.get("/traces/{trace_id}", response_model=TraceResponse, responses={404: {"model": ErrorResponse}})
    def get_trace(trace_id: str) -> TraceResponse:
        trace = trace_service.get_trace(sanitize_text(trace_id))
        if not trace:
            raise HTTPException(status_code=404, detail=ValidationError("Trace 不存在。").to_dict())
        return TraceResponse(trace=TracePayload(**trace))

    @app.get("/alerts", response_model=AlertEventListResponse)
    def list_alerts(
        severity: str | None = None,
        source_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AlertEventListResponse:
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

    @app.get("/alerts/{alert_id}", response_model=AlertEventResponse, responses={404: {"model": ErrorResponse}})
    def get_alert(alert_id: str) -> AlertEventResponse:
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
    def list_trace_alerts(trace_id: str) -> AlertEventListResponse:
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
        raw_input = sanitize_text(payload.input)
        if not raw_input:
            raise ValidationError("input 不能为空。")
        normalized_user_input, input_assets = parse_input_assets(raw_input)
        tool_results: list[dict[str, object]] = []
        task_state = ""
        if payload.run_tools:
            _, tool_results, task_state = preview_tools(normalized_user_input, input_assets, trace_id=request.state.trace_id)

        return AnalyzeAssetResponse(
            user_input=normalized_user_input,
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
        current_state = task_service.prepare_turn_state(
            state,
            normalized_user_input,
            input_assets,
            trace_id=request.state.trace_id,
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
            input_assets=current_state["input_assets"],
            tool_results=current_state["tool_results"],
            task_state=current_state["task_state"],
            available_tools=current_tool_registry().list_tool_names(),
        )

    return app
