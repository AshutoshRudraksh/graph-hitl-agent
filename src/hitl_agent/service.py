from typing import Any, Dict, Optional
from langgraph.types import Command
from hitl_agent.graph import build_graph, BaseCheckpointSaver


class AgentService:
    """Service wrapper for invoking, inspecting, and resuming stateful HITL graphs."""

    def __init__(self, checkpointer: Optional[BaseCheckpointSaver] = None):
        self.app = build_graph(checkpointer=checkpointer)

    def run_user_message(self, thread_id: str, message_content: str, user_id: str = "usr_default") -> Dict[str, Any]:
        """Sends a new user message to the specified thread.
        
        Returns the updated thread state snapshot after execution or pause.
        """
        config = {"configurable": {"thread_id": thread_id}}
        payload = {
            "messages": [{"role": "user", "content": message_content}],
            "execution_metadata": {"user_id": user_id}
        }
        
        self.app.invoke(payload, config=config)
        return self.inspect_thread(thread_id)

    def inspect_thread(self, thread_id: str) -> Dict[str, Any]:
        """Inspects current thread snapshot to check if graph is active, finished, or paused on interrupt."""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.app.get_state(config)

        # Extract interrupt details if graph is currently paused
        pending_interrupts = []
        if snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for intr in task.interrupts:
                        pending_interrupts.append(intr.value)

        return {
            "thread_id": thread_id,
            "is_paused": len(snapshot.next) > 0 and len(pending_interrupts) > 0,
            "next_node": snapshot.next,
            "pending_interrupts": pending_interrupts,
            "pending_action": snapshot.values.get("pending_action"),
            "messages_count": len(snapshot.values.get("messages", [])),
            "values": snapshot.values
        }

    def resume_action(self, thread_id: str, approved: bool) -> Dict[str, Any]:
        """Resumes a paused thread using Command(resume=...) with human decision."""
        config = {"configurable": {"thread_id": thread_id}}
        
        # Unblock in-node interrupt() with human decision payload
        self.app.invoke(Command(resume={"approved": approved}), config=config)
        
        return self.inspect_thread(thread_id)
