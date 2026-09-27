import os
import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from hitl_agent.state import ProductionAgentState
from hitl_agent.service import AgentService
from hitl_agent.tools import reset_transfer_ledger


# ---------------------------------------------------------------------------
# 1. Global Test Environment Setup
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Automatically inject dummy environment variables across all unit tests."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-openai-key-for-testing")
    monkeypatch.setenv("POSTGRES_URI", "postgresql://mock:mock@localhost:5432/mock_db")
    reset_transfer_ledger()
    yield
    reset_transfer_ledger()


# ---------------------------------------------------------------------------
# 2. Shared State & Service Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def memory_checkpointer():
    """Provides a fresh, isolated MemorySaver instance for thread testing."""
    return MemorySaver()


@pytest.fixture
def agent_service(memory_checkpointer):
    """Provides an AgentService instance initialized with an in-memory checkpointer."""
    return AgentService(checkpointer=memory_checkpointer)


@pytest.fixture
def initial_state() -> ProductionAgentState:
    """Provides a baseline ProductionAgentState payload for node/state testing."""
    return {
        "messages": [HumanMessage(content="Hello, check my account details.")],
        "pending_action": None,
        "action_approved": None,
        "execution_metadata": {
            "user_id": "usr_test_99",
            "tenant_id": "tenant_test_1",
            "trace_id": "trace_test_001"
        }
    }
