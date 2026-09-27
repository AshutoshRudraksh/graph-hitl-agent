import json

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from hitl_agent.graph import build_graph
from hitl_agent.nodes import reasoning_node
from hitl_agent.state import ProductionAgentState
from hitl_agent.tools import reset_transfer_ledger


def _app():
    reset_transfer_ledger()
    return build_graph(checkpointer=MemorySaver())


def test_reasoning_node_executes_safe_tool_automatically():
    """Verify read-only tools run automatically without triggering interrupt()."""
    state: ProductionAgentState = {
        "messages": [HumanMessage(content="Please check my balance")],
        "pending_action": None,
        "action_approved": None,
        "execution_metadata": {"user_id": "usr_7788", "tenant_id": "t_1"}
    }

    result = reasoning_node(state)

    assert "messages" in result
    assert len(result["messages"]) == 2
    assert isinstance(result["messages"][0], AIMessage)
    assert isinstance(result["messages"][1], ToolMessage)
    assert "balance_usd" in result["messages"][1].content


def test_reasoning_node_stages_the_requested_transfer():
    """The interrupt payload uses the amount and account from the user message."""
    app = _app()
    config = {"configurable": {"thread_id": "node-stage"}}
    app.invoke(
        {
            "messages": [HumanMessage(content="Please transfer $1 to acc_other")],
            "execution_metadata": {"user_id": "usr_7788", "tenant_id": "t_1"},
        },
        config=config,
    )

    payload = app.get_state(config).tasks[0].interrupts[0].value
    assert payload["type"] == "HUMAN_APPROVAL_REQUIRED"
    assert payload["action"]["tool"] == "execute_funds_transfer"
    assert payload["action"]["args"]["amount_usd"] == 1.0
    assert payload["action"]["args"]["destination_account"] == "acc_other"
    assert payload["action"]["args"]["source_account"] == "acc_main"


def test_reasoning_node_executes_approved_action_on_resume():
    """Resume runs the staged transfer before the graph ends."""
    app = _app()
    config = {"configurable": {"thread_id": "node-approve"}}
    app.invoke(
        {
            "messages": [HumanMessage(content="Please transfer $500 to acc_external")],
            "execution_metadata": {"user_id": "usr_7788", "tenant_id": "t_1"},
        },
        config=config,
    )
    staged_key = app.get_state(config).tasks[0].interrupts[0].value["action"]["args"]["idempotency_key"]

    result = app.invoke(Command(resume={"approved": True}), config=config)

    assert result["pending_action"] is None
    assert result["action_approved"] is True
    tool_message = result["messages"][-2]
    assert isinstance(tool_message, ToolMessage)
    body = json.loads(tool_message.content)
    assert body["status"] == "SUCCESS"
    assert body["idempotency_key"] == staged_key
    assert body["amount_usd"] == 500.0
    assert body["destination"] == "acc_external"


def test_reasoning_node_cancels_on_rejection_without_a_later_turn():
    """Rejection is applied on resume and does not move funds."""
    app = _app()
    config = {"configurable": {"thread_id": "node-reject"}}
    app.invoke(
        {
            "messages": [HumanMessage(content="Transfer $500")],
            "execution_metadata": {"user_id": "usr_7788", "tenant_id": "t_1"},
        },
        config=config,
    )

    result = app.invoke(Command(resume={"approved": False}), config=config)

    assert result["pending_action"] is None
    assert result["action_approved"] is False
    assert "cancelled" in result["messages"][-1].content
    assert not any("SUCCESS" in str(message.content) for message in result["messages"])

    follow_up = app.invoke(
        {"messages": [HumanMessage(content="Please check my balance")]},
        config=config,
    )
    assert "balance_usd" in follow_up["messages"][-1].content
    assert not any("SUCCESS" in str(message.content) for message in follow_up["messages"])


def test_later_message_does_not_rerun_a_resolved_transfer():
    """A message sent after approval is handled on its own."""
    app = _app()
    config = {"configurable": {"thread_id": "node-follow"}}
    app.invoke(
        {
            "messages": [HumanMessage(content="Transfer $1 to acc_other")],
            "execution_metadata": {"user_id": "usr_7788"},
        },
        config=config,
    )
    app.invoke(Command(resume={"approved": True}), config=config)

    result = app.invoke(
        {"messages": [HumanMessage(content="Please check my balance")]},
        config=config,
    )

    contents = [str(message.content) for message in result["messages"]]
    assert sum("SUCCESS" in content for content in contents) == 1
    assert "balance_usd" in contents[-1]
    assert result["pending_action"] is None


def test_example_using_fixtures(agent_service, initial_state):
    """Uses fixtures directly injected by conftest.py."""
    status = agent_service.run_user_message(
        thread_id="test_thread_fixture",
        message_content=initial_state["messages"][0].content,
        user_id=initial_state["execution_metadata"]["user_id"]
    )
    assert status["is_paused"] is False
