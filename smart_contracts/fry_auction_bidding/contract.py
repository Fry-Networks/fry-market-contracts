# SPDX-License-Identifier: MIT
# fry-market-contracts :: fry_auction_bidding
# Scaffolded by Phase 4b-FIX. Implementation lands in Phase 5.

from algopy import ARC4Contract, arc4


class FryAuctionBidding(ARC4Contract):
    """Placeholder - see ../../docs/AUDIT.md for findings this contract must fix."""

    @arc4.abimethod(create="require")
    def create(self) -> None:
        pass
