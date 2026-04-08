"""
API schemas.

What this is:
- Pydantic models for FastAPI request and response contracts.

What it does:
- Defines stable payloads for chat, sessions, tasks, tools, asset analysis, and
  upload endpoints.

Why this is done this way:
- Once the API is consumed by Web, plugins, or mobile clients, contract
  stability matters more than loosely shaped dictionaries.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="服务状态。")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="用户当前输入。")
    session_id: str | None = Field(default=None, description="已有会话 ID，为空时创建新会话。")
    user_name: str = Field(default="api-user", description="当前请求对应的用户名。")
    session_title: str = Field(default="API Session", description="新建会话标题。")


class ChatResponse(BaseModel):
    session_id: str
    turn_id: str
    task_id: str
    trace_id: str
    route_name: str
    route_reason: str
    plan: str
    debate_summary: str
    arbitration_summary: str
    answer: str
    critic_summary: str
    review_status: str
    review_summary: str
    tool_names: list[str]
    asset_count: int


class SessionPayload(BaseModel):
    id: str
    user_id: str
    title: str
    last_trace_id: str
    created_at: str
    updated_at: str


class MessagePayload(BaseModel):
    id: str
    session_id: str
    turn_id: str
    trace_id: str
    role: str
    content: str
    created_at: str


class AssetPayload(BaseModel):
    id: str
    session_id: str
    turn_id: str
    trace_id: str
    kind: str
    name: str
    source: str
    content: str
    storage_mode: str
    locator: str
    mime_type: str
    created_at: str


class SessionResponse(BaseModel):
    session: SessionPayload
    messages: list[MessagePayload]
    assets: list[AssetPayload]


class SessionListResponse(BaseModel):
    sessions: list[SessionPayload]


class AssetResponse(BaseModel):
    asset: AssetPayload


class AssetListResponse(BaseModel):
    assets: list[AssetPayload]


class TaskPayload(BaseModel):
    id: str
    session_id: str
    turn_id: str
    trace_id: str
    status: str
    user_input: str
    route_name: str
    route_reason: str
    plan: str
    debate_summary: str
    arbitration_summary: str
    answer: str
    critic_summary: str
    review_status: str
    review_summary: str
    tool_count: int
    error_message: str
    created_at: str
    updated_at: str


class ToolResultPayload(BaseModel):
    id: str = ""
    task_id: str = ""
    session_id: str = ""
    turn_id: str = ""
    trace_id: str
    tool_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    created_at: str = ""


class TaskResponse(BaseModel):
    task: TaskPayload
    tool_results: list[ToolResultPayload]


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class ToolInfoPayload(BaseModel):
    name: str
    description: str


class ToolListResponse(BaseModel):
    tools: list[ToolInfoPayload]


class ToolExecuteRequest(BaseModel):
    parameters: dict[str, str] = Field(default_factory=dict, description="工具执行参数。")
    trace_id: str | None = Field(default=None, description="可选的外部 trace_id。")


class ToolExecuteResponse(BaseModel):
    result: ToolResultPayload


class AnalyzeAssetRequest(BaseModel):
    input: str = Field(min_length=1, description="原始多模态输入命令。")
    run_tools: bool = Field(default=False, description="是否在解析后立即试跑可用本地工具。")


class AnalyzeAssetResponse(BaseModel):
    user_input: str
    input_assets: list[dict[str, object]]
    tool_results: list[ToolResultPayload] = Field(default_factory=list)
    task_state: str = Field(default="", description="工具试跑后的任务状态摘要。")
    available_tools: list[str] = Field(default_factory=list)


class UploadAssetResponse(BaseModel):
    session_id: str = Field(description="本次上传写入的会话 ID。")
    turn_id: str = Field(description="本次上传写入的轮次 ID。")
    task_id: str = Field(description="本次上传写入的任务 ID。")
    trace_id: str = Field(description="本次上传写入的追踪 ID。")
    upload_dir: str = Field(description="当前请求使用的上传目录。")
    saved_path: str = Field(description="文件实际写入的本地路径。")
    inferred_kind: str = Field(description="系统最终识别出的资产类型。")
    user_input: str = Field(description="本轮上传生成的默认或显式任务指令。")
    input_assets: list[dict[str, object]] = Field(description="标准化后的资产列表。")
    tool_results: list[ToolResultPayload] = Field(default_factory=list, description="工具试跑结果。")
    task_state: str = Field(default="", description="工具试跑后的任务状态摘要。")
    available_tools: list[str] = Field(default_factory=list, description="当前环境可用工具名列表。")


class ErrorResponse(BaseModel):
    category: str
    code: str
    message: str
    trace_id: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class TracePayload(BaseModel):
    trace_id: str
    request_id: str
    method: str
    path: str
    auth_subject: str
    auth_type: str
    session_id: str
    turn_id: str
    task_id: str
    status_code: int
    error_code: str
    idempotency_key: str
    rate_limited: bool
    started_at: str
    updated_at: str


class TraceResponse(BaseModel):
    trace: TracePayload


class WorkflowRolePayload(BaseModel):
    role_key: str = ""
    name: str
    stance_instruction: str
    is_enabled: bool = True
    sort_order: int = 0
    role_type: str = ""
    description: str = ""


class WorkflowConfigPayload(BaseModel):
    deliberation_enabled: bool
    deliberation_keywords: list[str]
    support_role: WorkflowRolePayload
    challenge_role: WorkflowRolePayload
    arbitration_role: WorkflowRolePayload
    critic_role: WorkflowRolePayload


class WorkflowConfigResponse(BaseModel):
    workflow: WorkflowConfigPayload


class WorkflowRoleListResponse(BaseModel):
    roles: list[WorkflowRolePayload]


class WorkflowRoleUpsertRequest(BaseModel):
    name: str = Field(min_length=1, description="角色名称。")
    stance_instruction: str = Field(min_length=1, description="角色立场或职责指令。")
    is_enabled: bool = Field(default=True, description="角色是否启用。")
    sort_order: int = Field(default=100, description="角色排序，数值越小越靠前。")
    role_type: str = Field(default="custom", description="角色类型，例如 debate / review / custom。")
    description: str = Field(default="", description="角色说明。")
    updated_by: str = Field(default="api-role", description="本次角色修改的操作人。")


class WorkflowRoleUpsertResponse(BaseModel):
    role: WorkflowRolePayload


class SecurityConfigPayload(BaseModel):
    allowed_tools: list[str]
    upload_allowed_kinds: list[str]
    upload_max_bytes: int
    auth_enabled: bool
    rate_limit_enabled: bool
    idempotency_enabled: bool


class SecurityConfigResponse(BaseModel):
    security: SecurityConfigPayload


class RuntimeConfigItemPayload(BaseModel):
    id: str
    config_scope: str
    config_key: str
    config_value: str
    value_type: str
    config_source: str
    description: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str


class RuntimeConfigListResponse(BaseModel):
    configs: list[RuntimeConfigItemPayload]


class RuntimeConfigUpsertRequest(BaseModel):
    config_scope: str = Field(min_length=1, description="配置作用域，例如 workflow 或 security。")
    config_key: str = Field(min_length=1, description="配置键名。")
    config_value: str = Field(description="配置值，统一按字符串提交。")
    value_type: str = Field(default="str", description="配置值类型，例如 bool / int / csv / str。")
    description: str = Field(default="", description="配置项说明。")
    updated_by: str = Field(default="api-config", description="本次配置修改的操作人。")


class RuntimeConfigUpsertResponse(BaseModel):
    config: RuntimeConfigItemPayload
