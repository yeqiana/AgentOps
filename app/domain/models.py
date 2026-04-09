"""
领域模型模块。
这是什么：
- 这是 Agent 底座最核心的数据结构定义文件。
做什么：
- 定义消息、输入资产、运行时上下文、工具结果、持久化记录和共享状态。
为什么这么做：
- 先稳定核心对象，其他层才知道要围绕什么数据协作。
- 状态、数据库、API 和工具返回都复用同一套模型，可以减少隐式耦合。
"""

from typing import Literal, NotRequired, TypedDict


class Message(TypedDict):
    """
    单条对话消息。
    这是什么：
    - 会话历史里的最小消息对象。
    做什么：
    - 保存角色和文本内容。
    为什么这么做：
    - 多轮上下文最稳定的形式就是消息列表。
    """

    role: Literal["user", "assistant"]
    content: str


class InputAsset(TypedDict):
    """
    多模态输入资产。
    这是什么：
    - 文本、图片、音频、视频、文件的统一输入抽象。
    做什么：
    - 描述资产类型、来源、内容和定位方式。
    为什么这么做：
    - 先把输入结构统一，后面的 Prompt、工具调用和持久化才能稳定工作。
    """

    kind: Literal["text", "image", "audio", "video", "file"]
    name: str
    content: str
    source: str
    storage_mode: NotRequired[
        Literal["inline_text", "local_path", "url", "bytes", "base64", "stream", "object_uri"]
    ]
    mime_type: NotRequired[str]
    locator: NotRequired[str]
    url: NotRequired[str]
    local_path: NotRequired[str]
    data_base64: NotRequired[str]
    size_bytes: NotRequired[int]
    sha256: NotRequired[str]


class RuntimeContext(TypedDict):
    """
    运行时能力描述。
    这是什么：
    - 给模型和应用层看的能力边界对象。
    做什么：
    - 描述可用输入输出模态、工具、联网情况和限制。
    为什么这么做：
    - Agent 底座要明确知道自己能做什么、不能做什么。
    """

    input_modalities: list[str]
    output_modalities: list[str]
    tools: list[str]
    network_status: str
    file_access_status: str
    runtime_constraints: list[str]


class ToolExecutionResult(TypedDict):
    """
    工具执行结果。
    这是什么：
    - 工具网关统一返回对象。
    做什么：
    - 保存工具名、是否成功、退出码和标准输出错误输出。
    为什么这么做：
    - 没有统一工具结果，后面的工具调用很快就会各说各话。
    """

    tool_name: str
    trace_id: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str


class UserRecord(TypedDict):
    """
    用户持久化记录。
    这是什么：
    - 数据库中的用户行结构。
    做什么：
    - 保存用户最小必要字段。
    为什么这么做：
    - 即使当前只有默认用户，也要先把用户概念固定下来。
    """

    id: str
    user_name: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class SessionRecord(TypedDict):
    """
    会话持久化记录。
    这是什么：
    - 数据库中的会话行结构。
    做什么：
    - 保存会话和最近一次执行链路信息。
    为什么这么做：
    - 会话是消息、资产和任务记录的聚合根。
    """

    id: str
    user_id: str
    title: str
    last_trace_id: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class MessageRecord(TypedDict):
    """
    消息持久化记录。
    这是什么：
    - 数据库中的消息行结构。
    做什么：
    - 为每条消息绑定会话、轮次和 trace。
    为什么这么做：
    - 之后排障要查的是一轮执行中的哪些消息，而不只是消息文本本身。
    """

    id: str
    session_id: str
    turn_id: str
    trace_id: str
    role: Literal["user", "assistant"]
    content: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AssetRecord(TypedDict):
    """
    资产持久化记录。
    这是什么：
    - 数据库中的输入资产行结构。
    做什么：
    - 为每个输入资产保存会话、轮次、trace 和定位信息。
    为什么这么做：
    - 多模态输入只存在内存里时，很难复盘一次执行到底分析了什么。
    """

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
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class TaskRecord(TypedDict):
    """
    任务持久化记录。
    这是什么：
    - 数据库中的任务行结构。
    做什么：
    - 保存任务与会话、轮次、trace、状态、输入和结果之间的关系。
    为什么这么做：
    - 没有任务表时，`task_id` 只存在内存和响应里，无法真正提供任务状态查询接口。
    """

    id: str
    session_id: str
    turn_id: str
    trace_id: str
    status: str
    user_input: str
    execution_mode: str
    protocol_summary: str
    route_name: str
    route_reason: str
    route_source: str
    plan: str
    debate_summary: str
    arbitration_summary: str
    answer: str
    critic_summary: str
    review_status: str
    review_summary: str
    tool_count: int
    error_message: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class ToolResultRecord(TypedDict):
    """
    工具结果持久化记录。
    这是什么：
    - 数据库中的工具调用结果行结构。
    做什么：
    - 保存任务、会话、轮次、trace、工具名和执行输出。
    为什么这么做：
    - 只有把工具结果正式落库，任务查询接口才具备真正的排障价值。
    """

    id: str
    task_id: str
    session_id: str
    turn_id: str
    trace_id: str
    tool_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class RouteDecisionRecord(TypedDict):
    """
    路由决策持久化记录。

    这是什么：
    - 数据库中的请求路由决策行结构。

    做什么：
    - 保存任务、会话、轮次、trace、路由名称、原因和决策来源。

    为什么这么做：
    - 请求路由中台要可查询、可追踪，仅写在任务表的摘要字段里还不够。
    """

    id: str
    task_id: str
    session_id: str
    turn_id: str
    trace_id: str
    route_name: str
    route_reason: str
    route_source: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class TraceRecord(TypedDict):
    """
    请求追踪持久化记录。
    这是什么：
    - 数据库中的请求级 trace 行结构。
    做什么：
    - 保存 HTTP 请求、执行链路上下文、认证主体、状态码和错误码。
    为什么这么做：
    - 阶段 2 需要从“只有 trace_id”升级为“可以查询一次请求完整元信息”的 trace service。
    """

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
    created_by: str
    updated_by: str
    created_at: str
    started_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class RuntimeConfigRecord(TypedDict):
    """
    运行时配置持久化记录。
    这是什么：
    - 数据库中的运行时配置覆盖项行结构。
    做什么：
    - 保存配置作用域、配置键、配置值和来源说明。
    为什么这么做：
    - 阶段 2 需要把 workflow 和 security 策略从纯环境变量升级为可持久化、
      可查询、可覆盖的配置中心。
    """

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
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class WorkflowRoleRecord(TypedDict):
    """
    工作流角色持久化记录。
    这是什么：
    - 数据库中的工作流角色定义行结构。
    做什么：
    - 保存角色键、角色名称、角色指令、启停状态和排序信息。
    为什么这么做：
    - 多 Agent 编排在进入阶段 2 后，角色不应只依赖零散配置键，
      而应该成为可注册、可查询、可扩展的独立对象。
    """

    id: str
    role_key: str
    role_name: str
    role_instruction: str
    is_enabled: bool
    sort_order: int
    role_type: str
    description: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AlertEventRecord(TypedDict):
    """
    告警事件持久化记录。

    What this is:
    - 数据库中的系统级告警事件行结构。

    What it does:
    - 保存告警来源、严重级别、事件编码、关联 trace 和扩展载荷。

    Why this is done this way:
    - 阶段 2 的失败恢复不应只停留在“重试和熔断”，还需要把关键异常
      和降级事件沉淀为可查询的治理数据。
    """

    id: str
    trace_id: str
    source_type: str
    source_name: str
    severity: str
    event_code: str
    message: str
    payload_json: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AuthRoleRecord(TypedDict):
    """
    RBAC 角色持久化记录。

    这是什么：
    - 数据库中的授权角色定义行结构。

    做什么：
    - 保存角色键、角色名称、描述和启停状态。

    为什么这么做：
    - 阶段 2 需要把“认证”推进到“最小授权”，角色必须成为可查询、
      可分配、可扩展的独立对象。
    """

    id: str
    role_key: str
    role_name: str
    description: str
    is_enabled: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AuthPermissionRecord(TypedDict):
    """
    RBAC 权限持久化记录。

    这是什么：
    - 数据库中的权限定义行结构。

    做什么：
    - 保存权限键、权限名称和权限说明。

    为什么这么做：
    - 只有把权限定义固化下来，角色授权和接口鉴权才能围绕统一权限语言协作。
    """

    id: str
    permission_key: str
    permission_name: str
    description: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AuthRolePermissionRecord(TypedDict):
    """
    角色权限关系持久化记录。

    这是什么：
    - 数据库中的角色到权限关系行结构。

    做什么：
    - 保存某个角色包含哪些权限。

    为什么这么做：
    - 最小 RBAC 需要将角色和权限解耦，后续才方便扩展权限组合。
    """

    id: str
    role_key: str
    permission_key: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AuthSubjectRoleRecord(TypedDict):
    """
    主体角色关系持久化记录。

    这是什么：
    - 数据库中的主体到角色关系行结构。

    做什么：
    - 保存某个认证主体被授予的角色集合。

    为什么这么做：
    - 当前认证主体可能是 API Key、Bearer Token 或后续用户实体，
      主体与角色分离后更适合后续演进。
    """

    id: str
    auth_subject: str
    role_key: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    ext_data1: str
    ext_data2: str
    ext_data3: str
    ext_data4: str
    ext_data5: str


class AgentState(TypedDict):
    """
    Agent 共享状态。
    这是什么：
    - LangGraph 节点之间流转的核心状态对象。
    做什么：
    - 保存当前输入、规划、回答、消息历史、资产、工具结果和执行上下文。
    为什么这么做：
    - 一阶段的底座已经不能只围绕单轮问答设计，必须把工具结果和可追踪性一起带进状态。
    """

    user_id: str
    session_id: str
    turn_id: str
    task_id: str
    trace_id: str
    user_input: str
    execution_mode: str
    protocol_summary: str
    route_name: str
    route_reason: str
    route_source: str
    plan: str
    debate_summary: str
    arbitration_summary: str
    answer: str
    critic_summary: str
    review_status: str
    review_summary: str
    messages: list[Message]
    input_assets: list[InputAsset]
    tool_results: list[ToolExecutionResult]
    runtime_context: RuntimeContext
    user_profile: str
    task_state: str
    output_format: str
    tone_style: str
    verbosity_level: str
    last_error: NotRequired[dict[str, object] | None]
