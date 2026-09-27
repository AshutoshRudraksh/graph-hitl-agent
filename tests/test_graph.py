import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from hitl_agent.graph import build_graph


def test_graph_executes_read_only_tool_end_to_end():
    """Verify state updates and history persist cleanly across safe operations."""
    checkpointer = MemorySaver()
    app = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread_safe_001"}}

    inputs = {
        "messages": [HumanMessage(content="Check my balance")],
        "execution_metadata": {"user_id": "usr_test_1", "tenant_id": "t_1"}
    }

    # Run graph execution
    final_state = app.invoke(inputs, config=config)

    assert len(final_state["messages"]) == 3  # Human -> AI tool_call -> ToolResponse
    assert "balance_usd" in final_state["messages"][-1].content


def test_graph_interrupts_and_resumes_via_command():
    """Verify that high-risk request triggers interrupt and resumes upon receiving Command."""
    checkpointer = MemorySaver()
    app = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread_hitl_002"}}

    inputs = {
        "messages": [HumanMessage(content="Transfer $500 to external account")],
        "execution_metadata": {"user_id": "usr_test_2", "tenant_id": "t_1"}
    }

    # 1. First execution should hit interrupt and pause
    app.invoke(inputs, config=config)

    # Inspect current thread state snapshot
    snapshot = app.get_state(config)
    assert snapshot.next == ("reasoning",)  # Node remains paused at reasoning
    assert len(snapshot.tasks) > 0
    assert snapshot.tasks[0].interrupts[0].value["type"] == "HUMAN_APPROVAL_REQUIRED"

    # 2. Resume execution via Command with approval payload
    resumed_state = app.invoke(Command(resume={"approved": True}), config=config)

    assert resumed_state["pending_action"] is None
    assert "SUCCESS" in resumed_state["messages"][-2].content  # ToolMessage output


def test_thread_isolation_in_checkpointing():
    """Verify that state in thread_A does not leak into thread_B."""
    checkpointer = MemorySaver()
    app = build_graph(checkpointer=checkpointer)

    config_a = {"configurable": {"thread_id": "thread_A"}}
    config_b = {"configurable": {"thread_id": "thread_B"}}

    app.invoke({"messages": [HumanMessage(content="Check balance")]}, config=config_a)
    app.invoke({"messages": [HumanMessage(content="Transfer $500")]}, config=config_b)

    snapshot_a = app.get_state(config_a)
    snapshot_b = app.get_state(config_b)

    # Thread A finished read operation, Thread B is paused on interrupt
    assert snapshot_a.next == ()
    assert snapshot_b.next == ("reasoning",)
