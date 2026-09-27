import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from hitl_agent.state import ProductionAgentState


def test_add_messages_reducer_appends_messages():
    """Verify that the add_messages reducer appends new messages without overwriting history."""
    initial_messages = [HumanMessage(content="Hello", id="msg_1")]
    new_messages = [AIMessage(content="How can I help you?", id="msg_2")]
    
    # Simulate LangGraph channel update using the reducer directly
    updated_messages = add_messages(initial_messages, new_messages)
    
    assert len(updated_messages) == 2
    assert updated_messages[0].content == "Hello"
    assert updated_messages[1].content == "How can I help you?"


def test_add_messages_reducer_deduplicates_by_id():
    """Verify that add_messages updates an existing message if IDs match (deduplication)."""
    initial_messages = [HumanMessage(content="Original text", id="msg_1")]
    updated_message = [HumanMessage(content="Updated text", id="msg_1")]
    
    reduced = add_messages(initial_messages, updated_message)
    
    assert len(reduced) == 1
    assert reduced[0].content == "Updated text"


def test_production_agent_state_schema_initialization():
    """Verify that ProductionAgentState initializes correctly with all required keys."""
    state: ProductionAgentState = {
        "messages": [HumanMessage(content="Check my balance")],
        "pending_action": {
            "tool": "execute_funds_transfer",
            "args": {"amount_usd": 100.0}
        },
        "action_approved": None,
        "execution_metadata": {
            "user_id": "usr_123",
            "tenant_id": "tenant_abc"
        }
    }
    
    assert len(state["messages"]) == 1
    assert state["pending_action"]["tool"] == "execute_funds_transfer"
    assert state["action_approved"] is None
    assert state["execution_metadata"]["user_id"] == "usr_123"
