"""
CLI 表现层模块。
这是什么：
- 这是命令行交互入口。
做什么：
- 读取用户输入，调用应用服务和工作流，并输出结果或错误。
- 在失败时也把任务状态落库，保证 CLI 与 API 的排障语义一致。
为什么这么做：
- CLI 仍然是当前项目最直接的使用方式，不能和 API 走两套不同的底座规则。
"""

from __future__ import annotations

import sys

from app.application.agent_service import format_conversation_history, parse_input_assets
from app.application.services.session_service import SessionService
from app.application.services.task_service import TaskService
from app.domain.errors import AgentError, ParsingError
from app.domain.models import AgentState
from app.infrastructure.llm.client import LLMCallError, sanitize_text
from app.infrastructure.logger import configure_logging, get_logger
from app.infrastructure.tools.registry import build_default_tool_registry
from app.workflow.graph import build_graph


EXIT_COMMANDS = {"exit", "quit", "q"}
logger = get_logger("presentation.cli")


def configure_stdio() -> None:
    """
    配置标准输入输出编码。
    这是什么：
    - CLI 环境初始化函数。
    做什么：
    - 尽量把标准输入输出切换成 UTF-8。
    为什么这么做：
    - Windows 终端的中文编码问题很常见，入口层应该优先兜底。
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def should_exit(user_input: str) -> bool:
    """
    判断是否退出。
    这是什么：
    - CLI 退出命令判断函数。
    做什么：
    - 判断输入是否属于退出命令。
    为什么这么做：
    - 退出逻辑属于表现层交互规则，不应该散落在主循环里。
    """
    return user_input.lower() in EXIT_COMMANDS


def log_conversation_context(stage: str, state: AgentState) -> None:
    """
    记录当前对话上下文。
    这是什么：
    - CLI 层的上下文日志辅助函数。
    做什么：
    - 把当前完整消息历史写入日志。
    为什么这么做：
    - 多轮 Agent 排查问题时，最先要看的就是上下文是否正确累积。
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
    启动 CLI Agent。
    这是什么：
    - 命令行模式下的主入口函数。
    做什么：
    - 初始化日志、会话服务、任务服务和 graph。
    - 启动持续对话循环。
    - 每轮调用一次 LangGraph 工作流并持久化结果。
    为什么这么做：
    - 当前阶段既要保留 CLI 可用，也要让 CLI 走正式底座链路。
    """
    configure_stdio()
    configure_logging()

    tool_registry = build_default_tool_registry()
    session_service = SessionService()
    task_service = TaskService(tool_registry)
    graph = build_graph()
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
            log_conversation_context("调用 graph 前的上下文", current_state)
            result = graph.invoke(current_state)
            session_service.persist_turn(result)
            state = result
            logger.info(
                "本轮回答生成成功 session_id=%s turn_id=%s trace_id=%s",
                state["session_id"],
                state["turn_id"],
                state["trace_id"],
            )
            log_conversation_context("调用 graph 后的上下文", state)
            print(f"\nAgent：{result['answer']}")
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
