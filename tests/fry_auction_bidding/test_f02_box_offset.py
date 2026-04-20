"""F-02: Bidding box layout is [amount(8), timestamp(8)] = 16 bytes total.

Deployed contract uses wrong offset for returning-bidder update.
Phase 6 must use offset 0 for bid_amount, offset 8 for bid_timestamp.

Phase 6 implementation notes:
- Deploy fresh FryAuctionBidding.
- Bidder A bids amount X -> should succeed, box = [X, ts].
- Bidder A bids amount X+Y (increasing own bid) -> MUST SUCCEED.
  Verify box updated to [X+Y, ts2].
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_returning_bidder_can_increase_bid():
    raise NotImplementedError()
