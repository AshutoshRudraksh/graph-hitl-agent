# graph-hitl-agent

`graph-hitl-agent` is a small LangGraph demo of human-in-the-loop (HITL) approval for risky tool calls.

## Behavior
- A normal message gets a direct assistant response.
- A safe read-only tool call (account lookup) runs immediately.
- A risky tool call (funds transfer) interrupts execution and waits for human approval.
- The paused thread is persisted by a LangGraph checkpointer, so approval/rejection can be sent in a later call.
