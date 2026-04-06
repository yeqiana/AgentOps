"""
FastAPI application factory.

What this is:
- The HTTP entrypoint for the stage-1 Agent runtime.

What it does:
- Exposes health, chat, session, task, tool, asset analysis, upload, and asset
  query APIs.
- Converts domain and runtime exceptions into stable structured HTTP responses.

Why this is done this way:
- API consumers need a stable protocol surface, while the internal graph,
  persistence, and toolchain can continue evolving behind the factory boundary.
"""

import uuid

from app.application.agent_service import create_initial_state, parse_input_assets
from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.application.upload_service import create_uploaded_asset
from app.config import get_upload_download_dir
from app.domain.errors import AgentError, ParsingError, ValidationError
from app.infrastructure.llm.client import LLMCallError, sanitize_text
from app.infrastructure.logger import get_logger
from app.infrastructure.tools.registry import build_default_tool_registry
from app.presentation.api.schemas import (
    AnalyzeAssetRequest,
    AnalyzeAssetResponse,
    AssetListResponse,
    AssetPayload,
    AssetResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    SessionListResponse,
    SessionResponse,
    TaskListResponse,
    TaskResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolInfoPayload,
    ToolListResponse,
    UploadAssetResponse,
)
from app.workflow.graph import build_graph
from app.workflow.nodes import tool_node


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
    tool_registry = build_default_tool_registry()
    task_service = TaskService(tool_registry)
    graph = build_graph()
    app = FastAPI(title="Agent Base Runtime API", version="0.6.0")

    def build_error_response(error: AgentError) -> ErrorResponse:
        return ErrorResponse(**error.to_dict())

    def persist_failed_task_if_possible(current_state: dict[str, object] | None, error: AgentError) -> None:
        if current_state is None:
            return
        session_service.persist_failed_turn(current_state, error)

    def preview_tools(user_input: str, input_assets: list[dict[str, object]]) -> tuple[dict[str, object], list[dict[str, object]], str]:
        preview_state = task_service.prepare_turn_state(
            create_initial_state(user_id="preview-user"),
            user_input,
            input_assets,  # type: ignore[arg-type]
        )
        preview_state = tool_node(preview_state)
        return preview_state, preview_state["tool_results"], preview_state["task_state"]

    @app.exception_handler(AgentError)
    async def handle_agent_error(_: Request, error: AgentError) -> JSONResponse:
        status_code = 500
        if error.category in {"validation", "parsing"}:
            status_code = 400
        elif error.category == "model":
            status_code = 502
        return JSONResponse(status_code=status_code, content=build_error_response(error).model_dump())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail
        if isinstance(detail, dict) and {"category", "code", "message"} <= set(detail.keys()):
            payload = ErrorResponse(**detail)
        else:
            payload = ErrorResponse(
                category="http",
                code="http_error",
                message=sanitize_text(str(detail)),
                trace_id=None,
                details={},
            )
        return JSONResponse(status_code=error.status_code, content=payload.model_dump())

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post(
        "/chat",
        response_model=ChatResponse,
        responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    def chat(payload: ChatRequest) -> ChatResponse:
        user_input = sanitize_text(payload.message)
        session_id = sanitize_text(payload.session_id or "")
        user_name = sanitize_text(payload.user_name) or "api-user"
        session_title = sanitize_text(payload.session_title) or "API Session"
        if not user_input:
            raise ValidationError("message 不能为空。")

        current_state = None
        try:
            normalized_user_input, input_assets = parse_input_assets(user_input)
            state = session_service.ensure_session(session_id or None, user_name=user_name, title=session_title)
            current_state = task_service.prepare_turn_state(state, normalized_user_input, input_assets)
            result = graph.invoke(current_state)
            session_service.persist_turn(result)
            return ChatResponse(
                session_id=result["session_id"],
                turn_id=result["turn_id"],
                task_id=result["task_id"],
                trace_id=result["trace_id"],
                plan=result["plan"],
                answer=result["answer"],
                tool_names=result["runtime_context"]["tools"],
                asset_count=len(result["input_assets"]),
            )
        except ParsingError as error:
            raise error
        except LLMCallError as error:
            error.with_trace_id(current_state["trace_id"] if current_state is not None else None)
            persist_failed_task_if_possible(current_state, error)
            raise error
        except AgentError as error:
            error.with_trace_id(current_state["trace_id"] if current_state is not None else error.trace_id)
            persist_failed_task_if_possible(current_state, error)
            raise error
        except Exception as error:
            logger.exception("API /chat 发生未预期异常")
            unexpected = AgentError(
                "system",
                "unexpected_error",
                sanitize_text(str(error)),
                trace_id=current_state["trace_id"] if current_state is not None else None,
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

    @app.get(
        "/sessions/{session_id}/assets",
        response_model=AssetListResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def list_assets_by_session(session_id: str) -> AssetListResponse:
        bundle = session_service.get_session_bundle(session_id)
        if not bundle["session"]:
            raise HTTPException(status_code=404, detail=ValidationError("会话不存在。").to_dict())
        return AssetListResponse(assets=[AssetPayload(**asset) for asset in bundle["assets"]])

    @app.get(
        "/assets/{asset_id}",
        response_model=AssetResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def get_asset(asset_id: str) -> AssetResponse:
        asset = session_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=ValidationError("资产不存在。").to_dict())
        return AssetResponse(asset=AssetPayload(**asset))

    @app.get("/tools", response_model=ToolListResponse)
    def list_tools() -> ToolListResponse:
        descriptions = tool_registry.get_tool_descriptions()
        return ToolListResponse(
            tools=[ToolInfoPayload(name=name, description=description) for name, description in descriptions.items()]
        )

    @app.post(
        "/tools/{tool_name}/execute",
        response_model=ToolExecuteResponse,
        responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    def execute_tool(tool_name: str, payload: ToolExecuteRequest) -> ToolExecuteResponse:
        normalized_tool_name = sanitize_text(tool_name)
        if not normalized_tool_name:
            raise ValidationError("tool_name 不能为空。")
        trace_id = sanitize_text(payload.trace_id or "") or f"trace_{uuid.uuid4().hex}"
        result = tool_registry.execute(normalized_tool_name, trace_id, payload.parameters)
        return ToolExecuteResponse(result=result)

    @app.get("/tasks", response_model=TaskListResponse)
    def list_tasks(
        status: str | None = None,
        session_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TaskListResponse:
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

    @app.get(
        "/sessions/{session_id}/tasks",
        response_model=TaskListResponse,
        responses={404: {"model": ErrorResponse}},
    )
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

    @app.post("/assets/analyze", response_model=AnalyzeAssetResponse, responses={400: {"model": ErrorResponse}})
    def analyze_asset(payload: AnalyzeAssetRequest) -> AnalyzeAssetResponse:
        raw_input = sanitize_text(payload.input)
        if not raw_input:
            raise ValidationError("input 不能为空。")
        normalized_user_input, input_assets = parse_input_assets(raw_input)
        tool_results: list[dict[str, object]] = []
        task_state = ""
        if payload.run_tools:
            _, tool_results, task_state = preview_tools(normalized_user_input, input_assets)

        return AnalyzeAssetResponse(
            user_input=normalized_user_input,
            input_assets=input_assets,
            tool_results=tool_results,
            task_state=task_state,
            available_tools=tool_registry.list_tool_names(),
        )

    @app.post(
        "/assets/upload",
        response_model=UploadAssetResponse,
        responses={400: {"model": ErrorResponse}},
    )
    async def upload_asset(
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
        current_state = task_service.prepare_turn_state(state, normalized_user_input, input_assets)
        if run_tools:
            current_state = tool_node(current_state)
        session_service.persist_turn(current_state)

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
            available_tools=tool_registry.list_tool_names(),
        )

    return app
