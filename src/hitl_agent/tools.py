import json
import uuid
from typing import Optional
from langchain_core.tools import tool

# Results of applied transfers, keyed by idempotency key. A replay returns the
# stored result instead of creating another transaction.
_transfer_ledger: dict[str, str] = {}


def reset_transfer_ledger() -> None:
    """Clear applied transfers. Used by tests so cases do not share ledger state."""
    _transfer_ledger.clear()

# ---------------------------------------------------------------------------
# 1. Read-Only / Safe Tool (Executes automatically)
# ---------------------------------------------------------------------------
@tool
def fetch_user_account_details(user_id: str) -> str:
    """Fetch high-level account details and balance for a given user ID.
    
    Safe read-only operation. Executes automatically without human intervention.
    """
    # Mock database lookup
    return json.dumps({
        "user_id": user_id,
        "status": "Active",
        "account_tier": "Enterprise",
        "balance_usd": 15000.00,
        "tenant_id": "tenant_9942"
    })


# ---------------------------------------------------------------------------
# 2. High-Risk Side-Effect Tool (Requires Idempotency Key)
# ---------------------------------------------------------------------------
@tool
def execute_funds_transfer(
    source_account: str,
    destination_account: str,
    amount_usd: float,
    idempotency_key: Optional[str] = None
) -> str:
    """Executes a monetary transfer between two accounts.
    
    HIGH-RISK ACTION: Modifies ledger state. Must be routed through human
    approval before execution and requires an idempotency key to guarantee
    single execution across network retries or pause/resume loops.
    """
    if amount_usd <= 0:
        raise ValueError("Transfer amount must be greater than zero.")

    tx_key = idempotency_key or f"tx_{uuid.uuid4().hex[:12]}"
    stored = _transfer_ledger.get(tx_key)
    if stored is not None:
        return stored

    result = json.dumps({
        "status": "SUCCESS",
        "transaction_id": f"txn_{uuid.uuid4().hex[:8]}",
        "idempotency_key": tx_key,
        "source": source_account,
        "destination": destination_account,
        "amount_usd": amount_usd,
        "message": f"Successfully transferred ${amount_usd:.2f} to {destination_account}."
    })
    _transfer_ledger[tx_key] = result
    return result


# Export tool registry and map
tools = [fetch_user_account_details, execute_funds_transfer]
tool_map = {t.name: t for t in tools}
