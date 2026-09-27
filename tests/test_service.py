import pytest
from langgraph.checkpoint.memory import MemorySaver
from hitl_agent.service import AgentService


def test_service_executes_safe_query_to_completion():
    """Verify safe read-only queries run without pausing for interrupts."""
    service = AgentService(checkpointer=MemorySaver())
    thread_id = "thread_service_001"

    status = service.run_user_message(thread_id, "Check my account balance")

    assert status["is_paused"] is False
    assert status["next_node"] == ()
    assert status["messages_count"] == 3


def test_service_detects_pause_and_inspects_interrupt_payload():
    """Verify high-risk request halts state and exposes structured interrupt payload."""
    service = AgentService(checkpointer=MemorySaver())
    thread_id = "thread_service_002"

    status = service.run_user_message(thread_id, "Transfer $500 to acc_ext")

    assert status["is_paused"] is True
    assert "reasoning" in status["next_node"]
    assert len(status["pending_interrupts"]) == 1
    
    interrupt_data = status["pending_interrupts"][0]
    assert interrupt_data["type"] == "HUMAN_APPROVAL_REQUIRED"
    assert interrupt_data["action"]["tool"] == "execute_funds_transfer"


def test_service_resumes_and_executes_when_approved():
    """Verify calling resume_action(approved=True) unblocks execution and completes tool call."""
    service = AgentService(checkpointer=MemorySaver())
    thread_id = "thread_service_003"

    # 1. Trigger pause
    service.run_user_message(thread_id, "Transfer $500")
    
    # 2. Resume with approval
    status = service.resume_action(thread_id, approved=True)

    assert status["is_paused"] is False
    assert status["pending_action"] is None
    assert "SUCCESS" in status["values"]["messages"][-2].content


def test_service_resumes_and_aborts_when_rejected():
    """Verify calling resume_action(approved=False) safely cancels the side-effect."""
    service = AgentService(checkpointer=MemorySaver())
    thread_id = "thread_service_004"

    # 1. Trigger pause
    service.run_user_message(thread_id, "Transfer $500")
    
    # 2. Resume with rejection
    status = service.resume_action(thread_id, approved=False)

    assert status["is_paused"] is False
    assert status["pending_action"] is None
    assert "cancelled" in status["values"]["messages"][-1].content

def test_example_using_fixtures(agent_service, initial_state):
    """Uses fixtures directly injected by conftest.py."""
    status = agent_service.run_user_message(
        thread_id="test_thread_fixture",
        message_content=initial_state["messages"][0].content,
        user_id=initial_state["execution_metadata"]["user_id"]
    )
    assert status["is_paused"] is False
