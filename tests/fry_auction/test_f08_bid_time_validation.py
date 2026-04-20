"""F-08: Time validation guards on list_nft_on_auction."""
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
from algosdk.transaction import AssetTransferTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner
from tests.conftest import _load_spec, create_test_nft
from pathlib import Path


def _get_bidding_programs():
    """Read compiled bidding contract programs."""
    artifacts = Path(__file__).parent.parent.parent / "smart_contracts" / "artifacts" / "fry_auction_bidding"
    approval_teal = (artifacts / "FryAuctionBidding.approval.teal").read_text()
    clear_teal = (artifacts / "FryAuctionBidding.clear.teal").read_text()
    return approval_teal, clear_teal


def test_list_with_past_start_time_fails(algorand, creator, dispenser):
    """Cannot list auction with start time in the past (F-08)."""
    now = int(time.time())
    spec = _load_spec("fry_auction/FryAuction.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))

    asset_id = create_test_nft(algorand, creator)
    app_client.send.call(AppClientMethodCallParams(method="asset_opt_in", args=[asset_id], extra_fee=AlgoAmount(micro_algo=1000)))

    # Compile bidding programs
    approval_teal, clear_teal = _get_bidding_programs()
    approval_compiled = algorand.app.compile_teal(approval_teal)
    clear_compiled = algorand.app.compile_teal(clear_teal)

    # Create NFT transfer txn
    sp = algorand.client.algod.suggested_params()
    nft_txn = AssetTransferTxn(
        sender=creator.address, sp=sp,
        receiver=app_client.app_address,
        amt=1, index=asset_id,
    )
    tws = TransactionWithSigner(txn=nft_txn, signer=creator.signer)

    # Try listing with PAST start time - must fail
    with pytest.raises(LogicError):
        app_client.send.call(AppClientMethodCallParams(
            method="list_nft_on_auction",
        extra_fee=AlgoAmount(micro_algo=2000),
            args=[
                asset_id,
                1_000_000,          # bid_start_amount
                100_000,            # min_bid_amount
                now - 100,          # PAST start time
                now + 3600,         # end time
                0,                  # collection_id
                tws,                # nft_txn
                approval_compiled.compiled_base64_to_bytes,  # bidding approval
                clear_compiled.compiled_base64_to_bytes,     # bidding clear
            ],
            asset_references=[asset_id],
        ))


def test_list_with_end_before_start_fails(algorand, creator, dispenser):
    """Cannot list auction with end time <= start time (F-08)."""
    now = int(time.time())
    spec = _load_spec("fry_auction/FryAuction.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))

    asset_id = create_test_nft(algorand, creator)
    app_client.send.call(AppClientMethodCallParams(method="asset_opt_in", args=[asset_id], extra_fee=AlgoAmount(micro_algo=1000)))

    approval_teal, clear_teal = _get_bidding_programs()
    approval_compiled = algorand.app.compile_teal(approval_teal)
    clear_compiled = algorand.app.compile_teal(clear_teal)

    sp = algorand.client.algod.suggested_params()
    nft_txn = AssetTransferTxn(
        sender=creator.address, sp=sp,
        receiver=app_client.app_address,
        amt=1, index=asset_id,
    )
    tws = TransactionWithSigner(txn=nft_txn, signer=creator.signer)

    # Try listing with end_time <= start_time - must fail
    start = now + 600
    with pytest.raises(LogicError):
        app_client.send.call(AppClientMethodCallParams(
            method="list_nft_on_auction",
        extra_fee=AlgoAmount(micro_algo=2000),
            args=[
                asset_id,
                1_000_000, 100_000,
                start,
                start - 1,         # end BEFORE start
                0,
                tws,
                approval_compiled.compiled_base64_to_bytes,
                clear_compiled.compiled_base64_to_bytes,
            ],
            asset_references=[asset_id],
        ))
