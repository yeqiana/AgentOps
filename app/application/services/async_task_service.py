"""
Async task orchestration service.

What this is:
- The stage-2 minimal async submission service.

What it does:
- Accepts prepared chat turn state.
- Persists queued and running task states.
- Executes the existing chat workflow in a background thread.
- Persists completed or failed results using the same session service as sync calls.

Why this is done this way:
- Stage 2 needs a real async task boundary without introducing a full queue
  platform yet.
- Reusing the existing workflow and persistence services keeps async and sync
  behavior aligned.
"""

from __future__ import annotations

from app.application.services.chat_service import ChatService
from app.application.services.session_service import SessionService
from app.domain.errors import AgentError
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.logger import get_logger
from app.infrastructure.queue import BackgroundTaskRunner
from app.infrastructure.trace import TraceService


logger = get_logger("application.async_task")


class AsyncTaskService:
    def __init__(
        self,
        *,
        runner: BackgroundTaskRunner,
        chat_service: ChatService,
        session_service: SessionService,
        trace_service: TraceService,
    ) -> None:
        self.runner = runner
        self.chat_service = chat_service
        self.session_service = session_service
        self.trace_service = trace_service

    def submit_turn(self, state: dict[str, object]) -> None:
        self.session_service.persist_queued_turn(state)  # type: ignore[arg-type]
        self.trace_service.attach_execution_context(
            state["trace_id"],  # type: ignore[index]
            session_id=state["session_id"],  # type: ignore[index]
            turn_id=state["turn_id"],  # type: ignore[index]
            task_id=state["task_id"],  # type: ignore[index]
        )
        self.runner.submit(state["task_id"], lambda: self._execute_turn(state))  # type: ignore[index]

    def get_runtime_snapshot(self) -> dict[str, object]:
        return self.runner.get_runtime_snapshot()

    def _execute_turn(self, state: dict[str, object]) -> None:
        self.session_service.mark_task_running(state)  # type: ignore[arg-type]
        try:
            result = self.chat_service.run_turn(state)  # type: ignore[arg-type]
            self.session_service.persist_turn(result)
            self.trace_service.attach_execution_context(
                result["trace_id"],
                session_id=result["session_id"],
                turn_id=result["turn_id"],
                task_id=result["task_id"],
            )
        except AgentError as error:
            error.with_trace_id(state["trace_id"])  # type: ignore[index]
            self.session_service.persist_failed_turn(state, error)  # type: ignore[arg-type]
        except Exception as error:
            logger.exception("异步任务执行发生未预期异常")
            wrapped = AgentError(
                "system",
                "unexpected_error",
                sanitize_text(str(error)),
                trace_id=state["trace_id"],  # type: ignore[index]
            )
            self.session_service.persist_failed_turn(state, wrapped)  # type: ignore[arg-type]
