from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ProductionAgentState(TypedDict):
    """State schema for a production-grade Human-in-the-Loop (HITL) agent.
    
    Acts as the single source of truth across every graph node transition,
    checkpointer snapshot, and API client request.
    
    Attributes:
        messages: Append-only ledger of conversation history managed by `add_messages`.
        pending_action: Cleared once a human decision is applied. While paused, the
            staged action is the interrupt payload, and that payload is what resume executes.
        action_approved: Human decision recorded when resume finishes.
        execution_metadata: Operational context (e.g., user_id, tenant_id, trace_id).
    """
    # Use add_messages reducer for atomic, append-only message updates and deduplication
    messages: Annotated[List[AnyMessage], add_messages]
    
    # Explicitly typed fields for human-in-the-loop tracking
    pending_action: Optional[Dict[str, Any]]
    action_approved: Optional[bool]
    
    # Context metadata for production observability, audit logs, and multi-tenancy
    execution_metadata: Dict[str, Any]
