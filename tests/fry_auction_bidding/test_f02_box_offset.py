"""F-02: Bid box stores [amount, timestamp] at offset 0 (16 bytes)."""
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
from algosdk.transaction import PaymentTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import decode_address
from tests.conftest import _load_spec


def test_bid_box_layout(algorand, creator, dispenser, bidder_a):
    """Bid writes [amount(8B), timestamp(8B)] correctly."""
    now = int(time.time())
    spec = _load_spec("fry_auction_bidding/FryAuctionBidding.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand,
        app_spec=spec,
        default_sender=creator.address,
        default_signer=creator.signer,
    ))

    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create",
            args=[
                1,                  # asset_id
                creator.address,    # seller
                1_000_000,          # bid_start_amount
                100_000,            # min_bid_amount
                now - 10,           # bidding_start_time (already started)
                now + 3600,         # bidding_end_time
            ],
        )
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))

    # Place a bid
    bid_amount = 2_000_000  # 2 ALGO
    sp = algorand.client.algod.suggested_params()
    pay_txn = PaymentTxn(
        sender=bidder_a.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=bid_amount,
    )
    tws = TransactionWithSigner(txn=pay_txn, signer=bidder_a.signer)

    app_client.send.call(AppClientMethodCallParams(
        method="bid",
        args=[tws],
        sender=bidder_a.address,
        signer=bidder_a.signer,
        box_references=[b"b" + decode_address(bidder_a.address)],
    ))

    box_name = b"b" + decode_address(bidder_a.address)
    box_value = algorand.client.algod.application_box_by_name(app_client.app_id, box_name)
    import base64; raw = base64.b64decode(box_value["value"])

    # First 8 bytes = amount (big-endian uint64)
    stored_amount = int.from_bytes(raw[0:8], "big")
    assert stored_amount == bid_amount

    # Next 8 bytes = timestamp (big-endian uint64)
    stored_timestamp = int.from_bytes(raw[8:16], "big")
    assert stored_timestamp > 0
    assert abs(stored_timestamp - now) < 30  # within 30s of now
