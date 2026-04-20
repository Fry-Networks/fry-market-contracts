"""Happy path: create collection -> list auction -> 2 bids -> settle.

Phase 6 implementation notes:
End-to-end flow across FryAuction + FryAuctionBidding. Two bidders place
escalating bids; auction ends; winner claims NFT; seller receives funds.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_full_auction_lifecycle():
    raise NotImplementedError()
