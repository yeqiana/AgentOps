"""
CLI presentation module.

What this is:
- The command-line interaction entrypoint.

What it does:
- Reads user input, calls application services and workflow orchestration, and
  prints results or errors.
- Persists failed turns too, so CLI and API share the same troubleshooting
  semantics.
- Streams the final answer to the terminal instead of waiting for the full
  buffer.

Why this is done this way:
- CLI is still the most direct runtime entrypoint, but it should follow the
  same base rules as the HTTP API.
"""

from __future__ import annotations

import sys

from app.application.agent_service import format_conversation_history, parse_input_assets
from app.application.services.chat_service import ChatService
from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.domain.errors import AgentError, ParsingError
from app.domain.models import AgentState
from app.infrastructure.llm.client import LLMCallError, sanitize_text
from app.infrastructure.logger import configure_logging, get_logger
from app.infrastructure.tools.registry import build_default_tool_registry


EXIT_COMMANDS = {"exit", "quit", "q"}
logger = get_logger("presentation.cli")


def configure_stdio() -> None:
    """
    What this is:
    - CLI environment initialization.

    What it does:
    - Reconfigures standard input and output to UTF-8 where possible.

    Why this is done this way:
    - Windows terminals often mis-handle Chinese input and output. The CLI
      entrypoint should absorb that problem first.
    """

    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def should_exit(user_input: str) -> bool:
    """
    What this is:
    - Exit-command detection.

    What it does:
    - Returns whether the current input means the CLI should exit.

    Why this is done this way:
    - Exit logic belongs to the presentation layer, not the workflow layer.
    """

    return user_input.lower() in EXIT_COMMANDS


def log_conversation_context(stage: str, state: AgentState) -> None:
    """
    What this is:
    - A CLI-side conversation logging helper.

    What it does:
    - Writes the current message history into debug logs.

    Why this is done this way:
    - Multi-turn agent issues are easiest to debug by checking whether
      conversation history accumulated correctly.
    """

    logger.debug(
        "%s trace_id=%s session_id=%s turn_id=%s\n%s",
        stage,
        state["trace_id"] or "none",
        state["session_id"],
        state["turn_id"] or "none",
        format_conversation_history(state["messages"]),
    )


def main() -> None:
    """
    What this is:
    - The CLI runtime entrypoint.

    What it does:
    - Initializes logging, session services, task services, and chat services.
    - Starts the chat loop.
    - Streams the final answer as it is produced.

    Why this is done this way:
    - The current stage still needs a first-class CLI, but it should share the
      same orchestration path as the API as much as possible.
    """

    configure_stdio()
    configure_logging()

    tool_registry = build_default_tool_registry()
    session_service = SessionService()
    task_service = TaskService(tool_registry)
    chat_service = ChatService()
    state = session_service.create_state(title="CLI Session")

    logger.info("CLI 启动完成 session_id=%s", state["session_id"])

    print("=== Agent Base Runtime ===")
    print(f"当前会话：{state['session_id']}")
    print("输入问题开始对话，输入 exit / quit / q 退出。")

    while True:
        raw_input = input("\n你：")
        user_input = sanitize_text(raw_input)

        if not user_input:
            print("输入不能为空，请重新输入。")
            logger.warning("用户输入为空，已要求重新输入")
            continue

        if should_exit(user_input):
            logger.info("用户输入退出命令，程序即将结束 session_id=%s", state["session_id"])
            print("已退出对话。")
            break

        current_state = None
        try:
            normalized_user_input, input_assets = parse_input_assets(user_input)
            current_state = task_service.prepare_turn_state(state, normalized_user_input, input_assets)
            logger.info(
                "收到用户输入 session_id=%s turn_id=%s trace_id=%s",
                current_state["session_id"],
                current_state["turn_id"],
                current_state["trace_id"],
            )
            log_conversation_context("调用 streaming workflow 前的上下文", current_state)

            print("\nAgent：", end="", flush=True)
            streamed_state = None
            for event in chat_service.stream_turn_events(current_state):
                if event["type"] == "answer_delta":
                    print(event["delta"], end="", flush=True)
                elif event["type"] == "done":
                    streamed_state = event["state"]
            print()

            if streamed_state is None:
                raise AgentError("system", "streaming_execution_error", "流式执行未返回最终状态。")

            session_service.persist_turn(streamed_state)
            state = streamed_state
            logger.info(
                "本轮回答生成成功 session_id=%s turn_id=%s trace_id=%s",
                state["session_id"],
                state["turn_id"],
                state["trace_id"],
            )
            log_conversation_context("调用 streaming workflow 后的上下文", state)
        except ParsingError as error:
            logger.error("输入解析失败 trace_id=%s message=%s", error.trace_id or "none", error)
            print(f"\n[error] {error}")
            print("你可以修正命令后继续输入。")
        except LLMCallError as error:
            logger.error("模型调用失败 trace_id=%s message=%s", error.trace_id or "none", error)
            if current_state is not None:
                error.with_trace_id(current_state["trace_id"])
                session_service.persist_failed_turn(current_state, error)
            state["last_error"] = error.to_dict()
            print(f"\n[error] {error}")
            print("本轮对话未成功生成回答。修正配置或额度后可继续提问。")
        except AgentError as error:
            logger.error("底座执行失败 trace_id=%s message=%s", error.trace_id or "none", error)
            if current_state is not None:
                error.with_trace_id(current_state["trace_id"])
                session_service.persist_failed_turn(current_state, error)
            state["last_error"] = error.to_dict()
            print(f"\n[error] {error}")
            print("本轮对话已中断，你可以继续下一轮。")
        except Exception as error:
            unexpected = AgentError(
                "system",
                "unexpected_error",
                sanitize_text(str(error)),
                trace_id=current_state["trace_id"] if current_state is not None else None,
            )
            logger.exception("程序运行时出现未预期异常")
            if current_state is not None:
                session_service.persist_failed_turn(current_state, unexpected)
            state["last_error"] = unexpected.to_dict()
            print(f"\n[error] {unexpected}")
            print("本轮对话已中断，你可以继续下一轮，或输入 q 退出。")
