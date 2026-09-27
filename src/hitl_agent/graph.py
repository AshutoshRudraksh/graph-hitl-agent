from typing import Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from hitl_agent.state import ProductionAgentState
from hitl_agent.nodes import reasoning_node


def build_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    """Constructs and compiles the HITL Agent StateGraph.
    
    Args:
        checkpointer: Durable checkpointer instance (e.g., MemorySaver or PostgresSaver).
                      If None, defaults to an in-memory MemorySaver.
    """
    # 1. Initialize Graph with Production State Schema
    builder = StateGraph(ProductionAgentState)

    # 2. Add Core Reasoning Node
    builder.add_node("reasoning", reasoning_node)

    # 3. Define State Graph Edges
    builder.add_edge(START, "reasoning")
    builder.add_edge("reasoning", END)

    # 4. Fallback default checkpointer for state persistence
    saver = checkpointer if checkpointer is not None else MemorySaver()

    # 5. Compile Graph with Checkpointer
    return builder.compile(checkpointer=saver)


# Singleton instance compiled with MemorySaver for testing/local CLI usage
graph = build_graph()
