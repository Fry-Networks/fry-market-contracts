import base64
"""F-03: Only admin can update the application."""
import pytest
from algokit_utils.models.amount import AlgoAmount
from algokit_utils import AppClientMethodCallParams
from algokit_utils.applications.app_client import LogicError
from algosdk.transaction import ApplicationUpdateTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner


def test_admin_can_update(deploy_market, algorand, creator):
    """Admin CAN update the application."""
    app = deploy_market
    # Get current programs
    app_info = algorand.client.algod.application_info(app.app_id)
    approval = app_info["params"]["approval-program"]
    clear = app_info["params"]["clear-state-program"]

    # Admin updates (same programs) - should succeed
    sp = algorand.client.algod.suggested_params()
    txn = ApplicationUpdateTxn(
        sender=creator.address,
        sp=sp,
        index=app.app_id,
        approval_program=base64.b64decode(approval),
        clear_program=base64.b64decode(clear),
    )
    signed = txn.sign(creator.private_key)
    txid = algorand.client.algod.send_transaction(signed)
    from algosdk.transaction import wait_for_confirmation
    wait_for_confirmation(algorand.client.algod, txid, 4)


def test_non_admin_cannot_update(deploy_market, algorand, creator, buyer):
    """Non-admin CANNOT update the application (F-03 guard)."""
    app = deploy_market
    app_info = algorand.client.algod.application_info(app.app_id)
    approval = app_info["params"]["approval-program"]
    clear = app_info["params"]["clear-state-program"]

    sp = algorand.client.algod.suggested_params()
    txn = ApplicationUpdateTxn(
        sender=buyer.address,
        sp=sp,
        index=app.app_id,
        approval_program=base64.b64decode(approval),
        clear_program=base64.b64decode(clear),
    )
    signed = txn.sign(buyer.private_key)
    with pytest.raises(Exception):
        txid = algorand.client.algod.send_transaction(signed)
        from algosdk.transaction import wait_for_confirmation
        wait_for_confirmation(algorand.client.algod, txid, 4)
