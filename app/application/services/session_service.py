"""
会话服务。
这是什么：
- 这是阶段 1 的会话与持久化编排服务。
做什么：
- 创建用户和会话。
- 持久化消息和资产。
- 按会话重建最小状态。
- 对入口层提供“获取或创建会话”的统一接口。
为什么这么做：
- 会话服务是 API、CLI、数据库和工作流之间的胶水层。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.domain.errors import AgentError
from app.application.agent_service import create_initial_state
from app.domain.models import AgentState, AssetRecord, InputAsset, MessageRecord, RouteDecisionRecord, TaskEventRecord, TaskRecord, ToolResultRecord
from app.infrastructure.persistence.repositories import (
    SQLiteAssetRepository,
    SQLiteMessageRepository,
    SQLiteRouteDecisionRepository,
    SQLiteSessionRepository,
    SQLiteTaskEventRepository,
    SQLiteTaskRepository,
    SQLiteToolResultRepository,
    SQLiteUserRepository,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionService:
    """
    会话服务。
    这是什么：
    - 应用层的状态持久化编排对象。
    做什么：
    - 统一处理会话创建、消息落库、资产落库和状态恢复。
    为什么这么做：
    - CLI、API 和未来的其他入口都需要同样的会话管理能力。
    """

    def __init__(self) -> None:
        self.user_repository = SQLiteUserRepository()
        self.session_repository = SQLiteSessionRepository()
        self.message_repository = SQLiteMessageRepository()
        self.asset_repository = SQLiteAssetRepository()
        self.task_repository = SQLiteTaskRepository()
        self.task_event_repository = SQLiteTaskEventRepository()
        self.tool_result_repository = SQLiteToolResultRepository()
        self.route_decision_repository = SQLiteRouteDecisionRepository()

    def create_state(self, *, user_name: str = "local-cli-user", title: str = "Agent Session") -> AgentState:
        user = self.user_repository.get_or_create(user_name)
        state = create_initial_state(user_id=user["id"])
        self.session_repository.create(user["id"], state["session_id"], title)
        return state

    def _actor_id(self, state: AgentState) -> str:
        return state["user_id"] or "system"

    def ensure_session(self, session_id: str | None, *, user_name: str, title: str) -> AgentState:
        """
        获取或创建会话状态。
        这是什么：
        - 入口层复用的会话装载函数。
        做什么：
        - 优先加载已有会话，不存在时创建新会话。
        为什么这么做：
        - 避免 CLI 和 API 各自手写会话创建/恢复逻辑。
        """
        if session_id:
            loaded_state = self.load_state(session_id)
            if loaded_state["messages"] or loaded_state["trace_id"]:
                return loaded_state
        return self.create_state(user_name=user_name, title=title)

    def load_state(self, session_id: str) -> AgentState:
        session = self.session_repository.get_by_id(session_id)
        state = create_initial_state()
        state["session_id"] = session_id
        if not session:
            return state

        messages = self.message_repository.list_by_session(session_id)
        state["messages"] = [{"role": message["role"], "content": message["content"]} for message in messages]
        state["user_id"] = session["user_id"]
        state["trace_id"] = session["last_trace_id"]
        return state

    def persist_turn(self, state: AgentState) -> None:
        self.session_repository.update_last_trace(
            state["session_id"],
            state["trace_id"],
            updated_by=self._actor_id(state),
        )
        self._persist_messages(state, include_assistant_reply=True)
        self._persist_assets_and_task(state, status="completed", error_message="")
        self.record_task_event(
            state,
            event_type="completed",
            event_message="任务执行完成。",
            event_payload={"status": "completed", "tool_count": len(state["tool_results"])},
        )

    def persist_queued_turn(self, state: AgentState) -> None:
        """
        记录排队中的任务。
        这是什么：
        - 异步任务提交后的首个持久化入口。
        做什么：
        - 只写入任务快照，不提前写入消息、资产和工具结果。
        为什么这么做：
        - 异步任务还未真正执行时，只需要让任务可查，避免提前写入最终态数据。
        """
        self.session_repository.update_last_trace(
            state["session_id"],
            state["trace_id"],
            updated_by=self._actor_id(state),
        )
        self.task_repository.create_or_update(self._to_task_record(state, status="queued", error_message=""))
        self.record_task_event(
            state,
            event_type="queued",
            event_message="异步任务已进入排队状态。",
            event_payload={"status": "queued"},
        )

    def mark_task_running(self, state: AgentState) -> None:
        """
        标记任务运行中。
        这是什么：
        - 异步任务执行前的状态流转入口。
        做什么：
        - 将任务状态更新为 running，供任务查询接口回查。
        为什么这么做：
        - 预留异步任务体系时，至少要有 queued -> running -> completed/failed 这条状态链。
        """
        self.session_repository.update_last_trace(
            state["session_id"],
            state["trace_id"],
            updated_by=self._actor_id(state),
        )
        self.task_repository.create_or_update(self._to_task_record(state, status="running", error_message=""))
        self.record_task_event(
            state,
            event_type="running",
            event_message="异步任务开始后台执行。",
            event_payload={"status": "running"},
        )

    def persist_failed_turn(self, state: AgentState, error: AgentError) -> None:
        """
        持久化失败任务。
        这是什么：
        - 失败轮次的专用落库方法。
        做什么：
        - 把用户输入、输入资产、任务状态和工具结果按 failed 状态写入数据库。
        为什么这么做：
        - “出问题时能查清楚”不能只靠日志，失败任务也必须可查询、可复盘。
        """
        self.session_repository.update_last_trace(
            state["session_id"],
            state["trace_id"],
            updated_by=self._actor_id(state),
        )
        self._persist_messages(state, include_assistant_reply=False)
        self._persist_assets_and_task(state, status="failed", error_message=error.message)
        self.record_task_event(
            state,
            event_type="failed",
            event_message=error.message,
            event_payload={"status": "failed", "error_code": error.code, "category": error.category},
        )

    def get_session_bundle(self, session_id: str) -> dict[str, object]:
        session = self.session_repository.get_by_id(session_id)
        return {
            "session": session,
            "messages": self.message_repository.list_by_session(session_id),
            "assets": self.asset_repository.list_by_session(session_id),
        }

    def get_asset(self, asset_id: str) -> dict[str, object] | None:
        return self.asset_repository.get_by_id(asset_id)

    def list_sessions(self, limit: int = 20, offset: int = 0) -> list[dict[str, object]]:
        return self.session_repository.list_sessions(limit=limit, offset=offset)

    def get_task(self, task_id: str) -> dict[str, object] | None:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return None
        return {
            "task": task,
            "task_events": self.task_event_repository.list_by_task(task_id),
            "tool_results": self.tool_result_repository.list_by_task(task_id),
            "route_decisions": self.route_decision_repository.list_by_task(task_id),
        }

    def list_task_events(self, task_id: str, *, limit: int = 100, offset: int = 0) -> list[TaskEventRecord]:
        return self.task_event_repository.list_by_task(task_id, limit=limit, offset=offset)

    def record_task_event(
        self,
        state: AgentState,
        *,
        event_type: str,
        event_message: str,
        event_payload: dict[str, object] | None = None,
    ) -> None:
        self.task_event_repository.create(
            self._to_task_event_record(
                state,
                event_type=event_type,
                event_message=event_message,
                event_payload=event_payload or {},
            )
        )

    def list_route_decisions(
        self,
        *,
        task_id: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RouteDecisionRecord]:
        return self.route_decision_repository.list_decisions(
            task_id=task_id,
            session_id=session_id,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
        )

    def list_route_decision_stats(
        self,
        *,
        session_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self.route_decision_repository.list_stats(
            session_id=session_id,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
        )

    def list_tasks_by_session(self, session_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, object]]:
        tasks = self.task_repository.list_by_session(session_id, limit=limit, offset=offset)
        return [
            {
                "task": task,
                "tool_results": self.tool_result_repository.list_by_task(task["id"]),
                "route_decisions": self.route_decision_repository.list_by_task(task["id"]),
            }
            for task in tasks
        ]

    def list_tasks(
        self,
        *,
        status: str | None = None,
        session_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        """
        查询任务列表。
        这是什么：
        - 任务查询服务方法。
        做什么：
        - 按状态、会话和分页条件返回任务列表及其工具结果。
        为什么这么做：
        - 当任务开始变多时，只靠单任务查询不够，后台必须支持筛选列表视角。
        """
        tasks = self.task_repository.list_tasks(status=status, session_id=session_id, limit=limit, offset=offset)
        return [
            {
                "task": task,
                "tool_results": self.tool_result_repository.list_by_task(task["id"]),
                "route_decisions": self.route_decision_repository.list_by_task(task["id"]),
            }
            for task in tasks
        ]

    def _to_asset_record(self, state: AgentState, asset: InputAsset) -> AssetRecord:
        locator = asset.get("locator", asset.get("url", asset.get("local_path", "")))
        mime_type = asset.get("mime_type", "")
        storage_mode = asset.get("storage_mode", "inline_text")
        timestamp = _now_iso()
        actor_id = self._actor_id(state)
        return {
            "id": f"asset_{uuid.uuid4().hex}",
            "session_id": state["session_id"],
            "turn_id": state["turn_id"],
            "trace_id": state["trace_id"],
            "kind": asset["kind"],
            "name": asset["name"],
            "source": asset["source"],
            "content": asset["content"],
            "storage_mode": storage_mode,
            "locator": locator,
            "mime_type": mime_type,
            "created_by": actor_id,
            "updated_by": actor_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }

    def _to_task_record(self, state: AgentState, *, status: str, error_message: str) -> TaskRecord:
        timestamp = _now_iso()
        actor_id = self._actor_id(state)
        return {
            "id": state["task_id"],
            "session_id": state["session_id"],
            "turn_id": state["turn_id"],
            "trace_id": state["trace_id"],
            "status": status,
            "user_input": state["user_input"],
            "execution_mode": state["execution_mode"],
            "protocol_summary": state["protocol_summary"],
            "route_name": state["route_name"],
            "route_reason": state["route_reason"],
            "plan": state["plan"],
            "debate_summary": state["debate_summary"],
            "arbitration_summary": state["arbitration_summary"],
            "answer": state["answer"],
            "critic_summary": state["critic_summary"],
            "review_status": state["review_status"],
            "review_summary": state["review_summary"],
            "tool_count": len(state["tool_results"]),
            "error_message": error_message,
            "created_by": actor_id,
            "updated_by": actor_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }

    def _to_tool_result_records(self, state: AgentState) -> list[ToolResultRecord]:
        records: list[ToolResultRecord] = []
        actor_id = self._actor_id(state)
        for result in state["tool_results"]:
            timestamp = _now_iso()
            records.append(
                {
                    "id": f"tool_{uuid.uuid4().hex}",
                    "task_id": state["task_id"],
                    "session_id": state["session_id"],
                    "turn_id": state["turn_id"],
                    "trace_id": state["trace_id"],
                    "tool_name": result["tool_name"],
                    "success": result["success"],
                    "exit_code": result["exit_code"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "created_by": actor_id,
                    "updated_by": actor_id,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "ext_data1": "",
                    "ext_data2": "",
                    "ext_data3": "",
                    "ext_data4": "",
                    "ext_data5": "",
                }
            )
        return records

    def _to_task_event_record(
        self,
        state: AgentState,
        *,
        event_type: str,
        event_message: str,
        event_payload: dict[str, object],
    ) -> TaskEventRecord:
        timestamp = _now_iso()
        actor_id = self._actor_id(state)
        return {
            "id": f"task_event_{uuid.uuid4().hex}",
            "task_id": state["task_id"],
            "session_id": state["session_id"],
            "turn_id": state["turn_id"],
            "trace_id": state["trace_id"],
            "event_type": event_type,
            "event_message": event_message,
            "event_payload_json": json.dumps(event_payload, ensure_ascii=False, sort_keys=True),
            "created_by": actor_id,
            "updated_by": actor_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "ext_data1": "",
            "ext_data2": "",
            "ext_data3": "",
            "ext_data4": "",
            "ext_data5": "",
        }

    def _to_route_decision_records(self, state: AgentState) -> list[RouteDecisionRecord]:
        if not state["route_name"]:
            return []

        timestamp = _now_iso()
        actor_id = self._actor_id(state)
        return [
            {
                "id": f"route_{uuid.uuid4().hex}",
                "task_id": state["task_id"],
                "session_id": state["session_id"],
                "turn_id": state["turn_id"],
                "trace_id": state["trace_id"],
                "route_name": state["route_name"],
                "route_reason": state["route_reason"],
                "route_source": state["route_source"] or "request_entry",
                "created_by": actor_id,
                "updated_by": actor_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "ext_data1": "",
                "ext_data2": "",
                "ext_data3": "",
                "ext_data4": "",
                "ext_data5": "",
            }
        ]

    def _persist_messages(self, state: AgentState, *, include_assistant_reply: bool) -> None:
        messages_to_persist: list[MessageRecord] = []
        if include_assistant_reply:
            current_messages = state["messages"][-2:] if len(state["messages"]) >= 2 else state["messages"][-1:]
        else:
            current_messages = state["messages"][-1:]

        actor_id = self._actor_id(state)
        for message in current_messages:
            timestamp = _now_iso()
            messages_to_persist.append(
                {
                    "id": f"msg_{uuid.uuid4().hex}",
                    "session_id": state["session_id"],
                    "turn_id": state["turn_id"],
                    "trace_id": state["trace_id"],
                    "role": message["role"],
                    "content": message["content"],
                    "created_by": actor_id,
                    "updated_by": actor_id,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "ext_data1": "",
                    "ext_data2": "",
                    "ext_data3": "",
                    "ext_data4": "",
                    "ext_data5": "",
                }
            )

        for message in messages_to_persist:
            self.message_repository.create(message)

    def _persist_assets_and_task(self, state: AgentState, *, status: str, error_message: str) -> None:
        asset_records: list[AssetRecord] = []
        for asset in state["input_assets"]:
            asset_records.append(self._to_asset_record(state, asset))
        self.asset_repository.create_many(asset_records)
        self.task_repository.create_or_update(self._to_task_record(state, status=status, error_message=error_message))
        self.tool_result_repository.replace_for_task(state["task_id"], self._to_tool_result_records(state))
        self.route_decision_repository.replace_for_task(state["task_id"], self._to_route_decision_records(state))
