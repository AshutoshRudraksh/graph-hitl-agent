from __future__ import annotations

import re
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


ACCOUNT_BALANCES = {
    "1234": 1250.0,
    "5678": 490.0,
    "9999": 10_000.0,
}


def account_lookup_tool(account_id: str) -> dict[str, Any]:
    balance = ACCOUNT_BALANCES.get(account_id, 0.0)
    return {"account_id": account_id, "balance": balance}


def transfer_funds_tool(source_account: str, destination_account: str, amount: float) -> dict[str, Any]:
    return {
        "source_account": source_account,
        "destination_account": destination_account,
        "amount": amount,
        "status": "completed",
    }


def _extract_account_id(message: str, default: str = "1234") -> str:
    match = re.search(r"\b\d{4}\b", message)
    return match.group(0) if match else default


def _extract_amount(message: str, default: float = 100.0) -> float:
    match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", message)
    return float(match.group(1)) if match else default


def _route(state: dict[str, Any]) -> dict[str, Any]:
    message = state["user_message"].lower()
    if "transfer" in message or "send" in message:
        return {
            "intent": "transfer",
            "source_account": "1234",
            "destination_account": _extract_account_id(message, default="5678"),
            "amount": _extract_amount(message),
        }
    if "balance" in message or "account" in message:
        return {"intent": "lookup", "account_id": _extract_account_id(message)}
    return {"intent": "answer"}


def _route_by_intent(state: dict[str, Any]) -> str:
    return state["intent"]


def _answer_directly(_: dict[str, Any]) -> dict[str, Any]:
    return {"response": "I can help with account lookups and transfer approvals."}


def _lookup_account(state: dict[str, Any]) -> dict[str, Any]:
    result = account_lookup_tool(state["account_id"])
    return {
        "lookup_result": result,
        "response": f"Account {result['account_id']} balance is ${result['balance']:.2f}.",
    }


def _await_transfer_approval(state: dict[str, Any]) -> dict[str, Any]:
    decision = interrupt(
        {
            "type": "transfer_approval",
            "source_account": state["source_account"],
            "destination_account": state["destination_account"],
            "amount": state["amount"],
        }
    )
    normalized = str(decision).strip().lower()
    if normalized in {"approve", "approved", "yes", "y"}:
        return {
            "approval": "approved",
            "source_account": state["source_account"],
            "destination_account": state["destination_account"],
            "amount": state["amount"],
        }
    return {
        "approval": "rejected",
        "response": "Transfer was rejected by a human reviewer.",
        "transfer_result": {"status": "rejected"},
    }


def _route_after_approval(state: dict[str, Any]) -> str:
    return "execute_transfer" if state.get("approval") == "approved" else END


def _execute_transfer(state: dict[str, Any]) -> dict[str, Any]:
    result = transfer_funds_tool(
        state["source_account"], state["destination_account"], float(state["amount"])
    )
    return {
        "approval": state.get("approval"),
        "transfer_result": result,
        "response": (
            f"Transferred ${result['amount']:.2f} from account {result['source_account']} "
            f"to account {result['destination_account']}."
        ),
    }


def build_graph(checkpointer: MemorySaver | None = None):
    workflow = StateGraph(dict)
    workflow.add_node("route", _route)
    workflow.add_node("answer", _answer_directly)
    workflow.add_node("lookup", _lookup_account)
    workflow.add_node("await_approval", _await_transfer_approval)
    workflow.add_node("execute_transfer", _execute_transfer)

    workflow.add_edge(START, "route")
    workflow.add_conditional_edges(
        "route",
        _route_by_intent,
        {"answer": "answer", "lookup": "lookup", "transfer": "await_approval"},
    )
    workflow.add_edge("answer", END)
    workflow.add_edge("lookup", END)
    workflow.add_conditional_edges("await_approval", _route_after_approval)
    workflow.add_edge("execute_transfer", END)

    return workflow.compile(checkpointer=checkpointer or MemorySaver())


def run_message(
    graph,
    user_message: str,
    thread_id: str,
    approval: str | None = None,
) -> dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id}}
    if approval is None:
        return graph.invoke({"user_message": user_message}, config=config)
    return graph.invoke(Command(resume=approval), config=config)
