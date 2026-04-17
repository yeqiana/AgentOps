"""
Chat orchestration service.

What this is:
- The application-layer orchestration service for normal and streaming chat turns.

What it does:
- Runs the full graph for non-streaming calls.
- Runs the pre-answer workflow nodes, streams the final answer, and then
  completes critique and review for streaming calls.

Why this is done this way:
- User-facing streaming should not force the whole workflow to wait until the
  final answer buffer is complete.
- The orchestration logic should stay out of CLI and API handlers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypedDict

from app.application.prompt_builder import build_answer_prompt
from app.domain.models import AgentState
from app.infrastructure.llm.client import stream_llm
from app.infrastructure.markdown_utils import normalize_markdown
from app.workflow.graph import build_graph
from app.workflow.nodes import (
    append_assistant_message,
    arbitration_node,
    critic_node,
    debate_node,
    plan_node,
    protocol_node,
    review_node,
    router_node,
    tool_node,
)
from app.workflow.registry import build_workflow_policy_registry


class StreamEvent(TypedDict, total=False):
    type: str
    session_id: str
    turn_id: str
    task_id: str
    trace_id: str
    route_name: str
    route_reason: str
    execution_mode: str
    protocol_summary: str
    delta: str
    answer: str
    review_status: str
    review_summary: str
    state: AgentState


class ChatService:
    """
    What this is:
    - The main application service for chat-turn execution.

    What it does:
    - Provides one-shot graph execution.
    - Provides streaming execution for the final answer while preserving the
      same persisted state shape.

    Why this is done this way:
    - Stage-2 now supports multiple execution protocols and richer orchestration.
      That logic should be reusable across CLI and HTTP API instead of copied.
    """

    def __init__(self) -> None:
        self.graph = build_graph()

    def run_turn(self, state: AgentState) -> AgentState:
        return self.graph.invoke(state)

    def stream_turn_events(self, state: AgentState) -> Iterator[StreamEvent]:
        current_state = tool_node(state)
        current_state = router_node(current_state)
        current_state = protocol_node(current_state)

        yield {
            "type": "metadata",
            "session_id": current_state["session_id"],
            "turn_id": current_state["turn_id"],
            "task_id": current_state["task_id"],
            "trace_id": current_state["trace_id"],
            "route_name": current_state["route_name"],
            "route_reason": current_state["route_reason"],
            "execution_mode": current_state["execution_mode"],
            "protocol_summary": current_state["protocol_summary"],
        }

        current_state = plan_node(current_state)
        current_state = debate_node(current_state)
        current_state = arbitration_node(current_state)

        registry = build_workflow_policy_registry()
        prompt = build_answer_prompt(
            current_state,
            role_name=registry.executor_role.name,
            stance_instruction=registry.executor_role.stance_instruction,
        )
        answer_chunks: list[str] = []
        for chunk in stream_llm(prompt, input_assets=current_state["input_assets"], trace_id=current_state["trace_id"]):
            answer_chunks.append(chunk)
            yield {"type": "answer_delta", "delta": chunk}

        answer_text = "".join(answer_chunks).strip()
        # Normalize Markdown formatting in the answer
        answer_text = normalize_markdown(answer_text)
        current_state = {
            **current_state,
            "answer": answer_text,
            "messages": append_assistant_message(current_state["messages"], answer_text),
        }
        current_state = critic_node(current_state)
        current_state = review_node(current_state)

        yield {
            "type": "done",
            "answer": current_state["answer"],
            "review_status": current_state["review_status"],
            "review_summary": current_state["review_summary"],
            "state": current_state,
        }
