"""F-05: cancel_bid reads caller's OWN box, not a passed-in address."""
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
from algosdk.transaction import PaymentTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import decode_address
from tests.conftest import _load_spec


def _deploy_active_bidding(algorand, creator):
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
            args=[1, creator.address, 1_000_000, 100_000, now - 10, now + 3600],
        )
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))
    return app_client


def test_non_highest_bidder_can_cancel(algorand, creator, dispenser, bidder_a, bidder_b):
    """Bidder A (not highest) CAN cancel their bid."""
    app = _deploy_active_bidding(algorand, creator)
    sp = algorand.client.algod.suggested_params()

    # Bidder A bids 2 ALGO
    pay_a = PaymentTxn(sender=bidder_a.address, sp=sp, receiver=app.app_address, amt=2_000_000)
    app.send.call(AppClientMethodCallParams(
        method="bid",
        args=[TransactionWithSigner(txn=pay_a, signer=bidder_a.signer)],
        sender=bidder_a.address, signer=bidder_a.signer,
        box_references=[b"b" + decode_address(bidder_a.address)],
    ))

    # Bidder B bids 3 ALGO (becomes highest)
    sp = algorand.client.algod.suggested_params()
    pay_b = PaymentTxn(sender=bidder_b.address, sp=sp, receiver=app.app_address, amt=3_000_000)
    app.send.call(AppClientMethodCallParams(
        method="bid",
        args=[TransactionWithSigner(txn=pay_b, signer=bidder_b.signer)],
        sender=bidder_b.address, signer=bidder_b.signer,
        box_references=[b"b" + decode_address(bidder_b.address)],
    ))

    # Bidder A cancels - should succeed (not highest)
    app.send.call(AppClientMethodCallParams(
        method="cancel_bid",
        extra_fee=AlgoAmount(micro_algo=1000),
        args=[],
        sender=bidder_a.address, signer=bidder_a.signer,
        box_references=[b"b" + decode_address(bidder_a.address)],
    ))


def test_highest_bidder_cannot_cancel(algorand, creator, dispenser, bidder_a, bidder_b):
    """Highest bidder CANNOT cancel their bid (F-05 guard)."""
    app = _deploy_active_bidding(algorand, creator)
    sp = algorand.client.algod.suggested_params()

    # Bidder A bids 2 ALGO
    pay_a = PaymentTxn(sender=bidder_a.address, sp=sp, receiver=app.app_address, amt=2_000_000)
    app.send.call(AppClientMethodCallParams(
        method="bid",
        args=[TransactionWithSigner(txn=pay_a, signer=bidder_a.signer)],
        sender=bidder_a.address, signer=bidder_a.signer,
        box_references=[b"b" + decode_address(bidder_a.address)],
    ))

    # Bidder B bids 3 ALGO (highest)
    sp = algorand.client.algod.suggested_params()
    pay_b = PaymentTxn(sender=bidder_b.address, sp=sp, receiver=app.app_address, amt=3_000_000)
    app.send.call(AppClientMethodCallParams(
        method="bid",
        args=[TransactionWithSigner(txn=pay_b, signer=bidder_b.signer)],
        sender=bidder_b.address, signer=bidder_b.signer,
        box_references=[b"b" + decode_address(bidder_b.address)],
    ))

    # Bidder B (highest) tries to cancel - must fail
    with pytest.raises(LogicError):
        app.send.call(AppClientMethodCallParams(
            method="cancel_bid",
        extra_fee=AlgoAmount(micro_algo=1000),
            args=[],
            sender=bidder_b.address, signer=bidder_b.signer,
            box_references=[b"b" + decode_address(bidder_b.address)],
        ))
