"""F-04: cancelNftAuction must fail during live bidding window.

Phase 6 implementation notes:
- List NFT at auction with bid window [t0, t0+1h].
- Bidder places bid.
- Seller calls cancelNftAuction during [t0, t0+1h] -> MUST FAIL.
- Seller calls before t0 or after t0+1h -> MUST SUCCEED (or some other
  defined behavior; exact policy set in Phase 6).
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_cannot_cancel_during_live_window():
    raise NotImplementedError()
