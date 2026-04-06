"""
任务服务。
这是什么：
- 这是阶段 1 的执行上下文编排服务。
做什么：
- 生成 turn_id、task_id、trace_id。
- 准备每轮调用的状态对象。
- 把工具能力写入运行时上下文。
为什么这么做：
- 执行上下文是“稳定执行、出问题可查”的基础，不能散落在 CLI 和 API 里。
"""

from __future__ import annotations

import uuid

from app.application.agent_service import append_user_message
from app.domain.models import AgentState, InputAsset
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.tools.registry import ToolRegistry


def _generate_identifier(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class TaskService:
    """
    任务服务。
    这是什么：
    - 应用层的执行上下文管理对象。
    做什么：
    - 为每轮输入生成统一的执行上下文并更新状态。
    为什么这么做：
    - 当前阶段先把执行上下文打通，后面才能继续接 trace、任务系统和工具系统。
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def prepare_turn_state(self, state: AgentState, user_input: str, input_assets: list[InputAsset]) -> AgentState:
        updated_messages = append_user_message(state["messages"], sanitize_text(user_input))
        runtime_context = {**state["runtime_context"], "tools": self.tool_registry.list_tool_names()}
        return {
            **state,
            "user_input": sanitize_text(user_input),
            "plan": "",
            "answer": "",
            "messages": updated_messages,
            "input_assets": input_assets,
            "tool_results": [],
            "turn_id": _generate_identifier("turn"),
            "task_id": _generate_identifier("task"),
            "trace_id": _generate_identifier("trace"),
            "runtime_context": runtime_context,
            "last_error": None,
        }
