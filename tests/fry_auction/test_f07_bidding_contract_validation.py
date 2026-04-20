"""F-07: Bidding contract must be created by auction contract (factory pattern)."""
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
from tests.conftest import _load_spec


def test_claim_with_unauthorized_bidding_app_fails(algorand, creator, dispenser):
    """Cannot claim with a bidding app NOT created by the auction contract (F-07)."""
    # Deploy auction contract
    auction_spec = _load_spec("fry_auction/FryAuction.arc56.json")
    auction_factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=auction_spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    auction_client, _ = auction_factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    auction_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))

    # Deploy a SEPARATE bidding app (NOT created by auction contract)
    import time
    now = int(time.time())
    bidding_spec = _load_spec("fry_auction_bidding/FryAuctionBidding.arc56.json")
    bidding_factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=bidding_spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    fake_bidding, _ = bidding_factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create",
            args=[1, creator.address, 1_000_000, 100_000, now - 10, now + 3600],
        )
    )

    # Try to claim using the unauthorized bidding app - must fail
    # The creator check: bidding_app.creator != auction_client.app_address
    with pytest.raises(LogicError):
        auction_client.send.call(AppClientMethodCallParams(
            method="claim_nft_royalty",
        extra_fee=AlgoAmount(micro_algo=4000),
            args=[1, fake_bidding.app_id],
            app_references=[fake_bidding.app_id],
            asset_references=[1],
        ))
