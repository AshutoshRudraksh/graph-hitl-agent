import json
import sys

from hitl_agent.service import AgentService


def _print_status(status: dict) -> None:
    print(f"thread={status['thread_id']} paused={status['is_paused']} messages={status['messages_count']}")
    if status["pending_interrupts"]:
        print(json.dumps(status["pending_interrupts"], indent=2))
    for message in status["values"].get("messages", []):
        content = getattr(message, "content", message)
        kind = getattr(message, "type", "message")
        print(f"  [{kind}] {content}")


def run_simulated_workflow() -> None:
    """Run a balance lookup and a transfer through the compiled graph.

    The transfer pauses on interrupt(). Approval resumes that same invocation
    and applies the staged transfer.
    """
    service = AgentService()
    thread_id = "local-cli"
    user_id = "usr_9876"

    print("HITL agent")
    balance = service.run_user_message(thread_id, "Please check my balance", user_id=user_id)
    _print_status(balance)

    transfer = service.run_user_message(
        thread_id,
        "Transfer $500 from acc_A to acc_B",
        user_id=user_id,
    )
    _print_status(transfer)
    if not transfer["is_paused"]:
        return

    decision = input("Approve this transfer? (y/n): ").strip().lower()
    finished = service.resume_action(thread_id, approved=decision == "y")
    _print_status(finished)


if __name__ == "__main__":
    try:
        run_simulated_workflow()
    except KeyboardInterrupt:
        sys.exit(130)
