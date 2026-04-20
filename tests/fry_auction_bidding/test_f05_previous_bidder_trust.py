"""F-05: cancelBid must validate previousHighestBidder.

Phase 6 implementation notes:
- 2 bidders bid. Second bidder has highest bid.
- First bidder calls cancelBid but provides WRONG previousHighestBidder
  (not actually the next-highest) -> MUST FAIL.
- First bidder calls with correct previousHighestBidder -> MUST SUCCEED.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_cancel_bid_rejects_wrong_previous_bidder():
    raise NotImplementedError()
