import json
import pytest
from hitl_agent.tools import fetch_user_account_details, execute_funds_transfer


def test_fetch_user_account_details_returns_valid_json():
    """Verify safe read-only tool returns expected JSON payload."""
    result = fetch_user_account_details.invoke({"user_id": "usr_9942"})
    data = json.loads(result)
    
    assert data["user_id"] == "usr_9942"
    assert data["status"] == "Active"
    assert "balance_usd" in data


def test_execute_funds_transfer_generates_idempotency_key_if_missing():
    """Verify side-effect tool generates an idempotency key when omitted."""
    payload = {
        "source_account": "acc_source",
        "destination_account": "acc_dest",
        "amount_usd": 500.00
    }
    result = execute_funds_transfer.invoke(payload)
    data = json.loads(result)
    
    assert data["status"] == "SUCCESS"
    assert data["amount_usd"] == 500.00
    assert data["idempotency_key"].startswith("tx_")


def test_execute_funds_transfer_respects_provided_idempotency_key():
    """Verify side-effect tool preserves user/graph-provided idempotency key."""
    custom_key = "idempotency_tx_explicit_001"
    payload = {
        "source_account": "acc_source",
        "destination_account": "acc_dest",
        "amount_usd": 250.00,
        "idempotency_key": custom_key
    }
    result = execute_funds_transfer.invoke(payload)
    data = json.loads(result)
    
    assert data["idempotency_key"] == custom_key


def test_execute_funds_transfer_replays_the_same_key():
    """The same idempotency key returns the original transaction and does not create another."""
    payload = {
        "source_account": "acc_source",
        "destination_account": "acc_dest",
        "amount_usd": 500.00,
        "idempotency_key": "idempotency_tx_replay_001",
    }
    first = json.loads(execute_funds_transfer.invoke(payload))
    second = json.loads(execute_funds_transfer.invoke(payload))

    assert second == first
    assert first["transaction_id"].startswith("txn_")


def test_execute_funds_transfer_raises_error_for_invalid_amount():
    """Verify input validation fails on zero or negative values."""
    payload = {
        "source_account": "acc_source",
        "destination_account": "acc_dest",
        "amount_usd": -100.00
    }
    with pytest.raises(ValueError, match="Transfer amount must be greater than zero"):
        execute_funds_transfer.invoke(payload)
