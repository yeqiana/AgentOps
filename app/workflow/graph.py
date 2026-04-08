"""
工作流图定义模块。
这是什么：
- 这是 LangGraph 图结构定义文件。
做什么：
- 注册节点。
- 定义执行顺序。
- 返回编译后的 graph。
为什么这么做：
- 图编排是独立于 CLI 和模型接入的职责。
- 后续如果加工具节点、路由节点或 review 节点，应优先修改这里。
"""

from langgraph.graph import END, START, StateGraph

from app.domain.models import AgentState
from app.workflow.nodes import (
    answer_node,
    arbitration_node,
    critic_node,
    debate_node,
    plan_node,
    review_node,
    router_node,
    tool_node,
)


def build_graph():
    """
    构建 LangGraph 工作流。
    这是什么：
    - 这是 graph 工厂函数。
    做什么：
    - 创建状态图。
    - 注册工具、路由、规划、辩论、仲裁、回答、批评和复核节点。
    - 定义 `START -> tool_node -> router_node -> plan_node -> debate_node -> arbitration_node -> answer_node -> critic_node -> review_node -> END`。
    为什么这么做：
    - 阶段 1 的重点已经从“单纯对话”升级为“按资产自动触发最小工具调用”。
    - 先做一个线性可解释的工具链，比一开始引入复杂路由更稳定。
    """

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("tool_node", tool_node)
    graph_builder.add_node("router_node", router_node)
    graph_builder.add_node("plan_node", plan_node)
    graph_builder.add_node("debate_node", debate_node)
    graph_builder.add_node("arbitration_node", arbitration_node)
    graph_builder.add_node("answer_node", answer_node)
    graph_builder.add_node("critic_node", critic_node)
    graph_builder.add_node("review_node", review_node)
    graph_builder.add_edge(START, "tool_node")
    graph_builder.add_edge("tool_node", "router_node")
    graph_builder.add_edge("router_node", "plan_node")
    graph_builder.add_edge("plan_node", "debate_node")
    graph_builder.add_edge("debate_node", "arbitration_node")
    graph_builder.add_edge("arbitration_node", "answer_node")
    graph_builder.add_edge("answer_node", "critic_node")
    graph_builder.add_edge("critic_node", "review_node")
    graph_builder.add_edge("review_node", END)
    return graph_builder.compile()
