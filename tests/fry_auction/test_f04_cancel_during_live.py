"""F-04: Cannot cancel auction after bidding has started."""
import time
import pytest
from algokit_utils import (
    AppClientMethodCallParams,
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryParams,
)
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.applications.app_client import FundAppAccountParams
from algokit_utils.applications.app_client import LogicError
from algosdk.transaction import AssetTransferTxn, PaymentTxn, wait_for_confirmation
from algosdk.atomic_transaction_composer import TransactionWithSigner
from tests.conftest import _load_spec, create_test_nft
from pathlib import Path


def _get_chain_timestamp(algorand):
    """Force a new block and return its timestamp."""
    disp = algorand.account.localnet_dispenser()
    sp = algorand.client.algod.suggested_params()
    txn = PaymentTxn(sender=disp.address, sp=sp, receiver=disp.address, amt=0)
    signed = txn.sign(disp.private_key)
    txid = algorand.client.algod.send_transaction(signed)
    result = wait_for_confirmation(algorand.client.algod, txid, 4)
    block = algorand.client.algod.block_info(result["confirmed-round"])
    return block["block"]["ts"]


def _list_auction(algorand, app_client, creator, asset_id, start_time, end_time):
    """Helper: list NFT on auction with factory inner-txn."""
    artifacts = Path(__file__).parent.parent.parent / "smart_contracts" / "artifacts" / "fry_auction_bidding"
    approval_teal = (artifacts / "FryAuctionBidding.approval.teal").read_text()
    clear_teal = (artifacts / "FryAuctionBidding.clear.teal").read_text()
    approval_compiled = algorand.app.compile_teal(approval_teal)
    clear_compiled = algorand.app.compile_teal(clear_teal)

    sp = algorand.client.algod.suggested_params()
    nft_txn = AssetTransferTxn(
        sender=creator.address, sp=sp,
        receiver=app_client.app_address, amt=1, index=asset_id,
    )
    tws = TransactionWithSigner(txn=nft_txn, signer=creator.signer)

    app_client.send.call(AppClientMethodCallParams(
        method="list_nft_on_auction",
        extra_fee=AlgoAmount(micro_algo=2000),
        args=[
            asset_id, 1_000_000, 100_000,
            start_time, end_time, 0,
            tws, approval_compiled.compiled_base64_to_bytes,
            clear_compiled.compiled_base64_to_bytes,
        ],
        box_references=[b"a" + asset_id.to_bytes(8, "big")],
        asset_references=[asset_id],
    ))


def test_cancel_before_bidding_starts_succeeds(algorand, creator, dispenser):
    """Can cancel auction BEFORE bidding start time."""
    spec = _load_spec("fry_auction/FryAuction.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=20)))

    asset_id = create_test_nft(algorand, creator)
    app_client.send.call(AppClientMethodCallParams(
        method="asset_opt_in", args=[asset_id],
        extra_fee=AlgoAmount(micro_algo=1000),
    ))

    # Get chain time and list with start far in future
    chain_now = _get_chain_timestamp(algorand)
    start_time = chain_now + 600
    end_time = chain_now + 3600
    _list_auction(algorand, app_client, creator, asset_id, start_time, end_time)

    # Cancel immediately - should succeed (chain time << start_time)
    app_client.send.call(AppClientMethodCallParams(
        method="cancel_nft_auction",
        extra_fee=AlgoAmount(micro_algo=1000),
        args=[asset_id],
        box_references=[b"a" + asset_id.to_bytes(8, "big")],
        asset_references=[asset_id],
    ))


def test_cancel_after_bidding_starts_fails(algorand, creator, dispenser):
    """CANNOT cancel auction AFTER bidding start time (F-04 guard)."""
    spec = _load_spec("fry_auction/FryAuction.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=20)))

    asset_id = create_test_nft(algorand, creator)
    app_client.send.call(AppClientMethodCallParams(
        method="asset_opt_in", args=[asset_id],
        extra_fee=AlgoAmount(micro_algo=1000),
    ))

    # Get chain time and list with start_time 3s in future
    chain_now = _get_chain_timestamp(algorand)
    start_time = chain_now + 3
    end_time = chain_now + 3600
    _list_auction(algorand, app_client, creator, asset_id, start_time, end_time)

    # Wait for chain time to surpass start_time
    time.sleep(6)

    # Force a new block so Global.LatestTimestamp advances
    # (devmode only produces blocks on-demand)
    _get_chain_timestamp(algorand)

    # Try to cancel AFTER bidding started - must fail
    with pytest.raises(LogicError):
        app_client.send.call(AppClientMethodCallParams(
            method="cancel_nft_auction",
            extra_fee=AlgoAmount(micro_algo=1000),
            args=[asset_id],
            box_references=[b"a" + asset_id.to_bytes(8, "big")],
            asset_references=[asset_id],
        ))
