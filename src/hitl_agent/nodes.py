import hashlib
import json
import re
from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt

from hitl_agent.state import ProductionAgentState
from hitl_agent.tools import fetch_user_account_details, tool_map

# Tools in this set pause for approval. Resume executes the staged args.
HIGH_RISK_TOOLS = {"execute_funds_transfer"}

_DEFAULT_SOURCE = "acc_main"
_DEFAULT_DESTINATION = "acc_external"
_AMOUNT = re.compile(r"\$(\d+(?:\.\d+)?)")
_ACCOUNT = re.compile(r"\b(from|to)\s+([A-Za-z0-9_\-]+)", re.IGNORECASE)
_TRANSFER = re.compile(r"\btransfer\b", re.IGNORECASE)
_NEGATED_TRANSFER = re.compile(
    r"\b(?:don't|do not|never)\b(?:\W+\w+){0,6}\W+transfer\b",
    re.IGNORECASE,
)


def reasoning_node(state: ProductionAgentState) -> Dict[str, Any]:
    """Choose the next action from the latest user message.

    High-risk tools call interrupt() with the exact args that resume will run.
    interrupt() restarts this node and then returns the human decision, so the
    side effect happens in that same invocation, using args rebuilt from the
    user message rather than from a later turn.
    """
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    if isinstance(last_message, AIMessage) or not last_message:
        return {}

    user_text = str(last_message.content)
    transfer = _parse_transfer(user_text)
    if transfer is not None:
        action = _stage_transfer(state, transfer)
        if action["tool"] in HIGH_RISK_TOOLS:
            return _review_transfer(action)

    if _TRANSFER.search(user_text) and not _NEGATED_TRANSFER.search(user_text):
        return {
            "messages": [
                AIMessage(
                    content="Include a transfer amount, for example: transfer $500 from acc_main to acc_external."
                )
            ]
        }

    if "balance" in user_text.lower() or "account" in user_text.lower():
        return _lookup_account(state)

    return {"messages": [AIMessage(content="I can help you check balances or transfer funds.")]}


def _review_transfer(action: Dict[str, Any]) -> Dict[str, Any]:
    decision = interrupt({
        "type": "HUMAN_APPROVAL_REQUIRED",
        "action": action,
        "message": f"Approval requested for high-risk action: {action['description']}",
    })
    approved = _is_approved(decision)
    if not approved:
        return {
            "messages": [
                AIMessage(content=f"Action '{action['tool']}' was cancelled by the human reviewer.")
            ],
            "pending_action": None,
            "action_approved": False,
        }

    tool_result = tool_map[action["tool"]].invoke(action["args"])
    return {
        "messages": [
            ToolMessage(content=tool_result, tool_call_id=action["tool_call_id"]),
            AIMessage(content=f"Action '{action['tool']}' successfully executed following human approval."),
        ],
        "pending_action": None,
        "action_approved": True,
    }


def _lookup_account(state: ProductionAgentState) -> Dict[str, Any]:
    user_id = state.get("execution_metadata", {}).get("user_id", "usr_default")
    result = fetch_user_account_details.invoke({"user_id": user_id})
    call_id = "call_read_" + _digest({"user_id": user_id, "index": len(state["messages"]) - 1})[:8]
    return {
        "messages": [
            AIMessage(
                content="Fetching account details...",
                tool_calls=[{
                    "name": "fetch_user_account_details",
                    "args": {"user_id": user_id},
                    "id": call_id,
                }],
            ),
            ToolMessage(content=result, tool_call_id=call_id),
        ]
    }


def _parse_transfer(user_text: str) -> Optional[Dict[str, Any]]:
    """Return source, destination, and amount from a transfer request.

    Specified accounts win over the defaults. A negated request or a request
    with no amount is not a transfer.
    """
    if _NEGATED_TRANSFER.search(user_text) or not _TRANSFER.search(user_text):
        return None
    amount_match = _AMOUNT.search(user_text)
    if amount_match is None:
        return None
    amount = float(amount_match.group(1))
    if amount <= 0:
        return None

    source = _DEFAULT_SOURCE
    destination = _DEFAULT_DESTINATION
    for match in _ACCOUNT.finditer(user_text):
        kind, account = match.group(1).lower(), match.group(2)
        if kind == "from":
            source = account
        else:
            destination = account
    return {
        "source_account": source,
        "destination_account": destination,
        "amount_usd": amount,
    }


def _stage_transfer(state: ProductionAgentState, transfer: Dict[str, Any]) -> Dict[str, Any]:
    args = {
        "source_account": transfer["source_account"],
        "destination_account": transfer["destination_account"],
        "amount_usd": transfer["amount_usd"],
    }
    identity = {
        "index": len(state["messages"]) - 1,
        "content": str(state["messages"][-1].content),
        "tool": "execute_funds_transfer",
        "args": args,
    }
    idempotency_key = "tx_" + _digest(identity)
    args["idempotency_key"] = idempotency_key
    amount = transfer["amount_usd"]
    return {
        "tool": "execute_funds_transfer",
        "args": args,
        "description": (
            f"Transfer ${amount:.2f} from {transfer['source_account']} "
            f"to {transfer['destination_account']}"
        ),
        "tool_call_id": f"call_{idempotency_key}",
    }


def _digest(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _is_approved(decision: Any) -> bool:
    if isinstance(decision, bool):
        return decision
    if isinstance(decision, dict) and "approved" in decision:
        return bool(decision["approved"])
    raise TypeError("Human review resume value must be a bool or {'approved': bool}")
