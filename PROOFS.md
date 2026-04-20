# F-Fix Proof Log

All proofs run on ATLAS00 localnet (algokit devmode) with puyapy 5.8.1.
Protocol: test PASS with guard -> remove guard -> recompile -> test FAIL -> restore -> recompile.

## F-01: add_royalty Authorization

**Guard:** assert Txn.sender == collection_creator in FryMarket.add_royalty
**Test:** test_add_royalty_by_non_creator_fails

| Condition | Result |
|-----------|--------|
| With guard | PASSED - non-creator call rejected |
| Without guard | FAILED - non-creator call succeeded (unauthorized royalty set) |

## F-02: Bid Box Layout (Structural)

**Fix:** BidValue struct stores [amount(8B), timestamp(8B)] at offset 0 in bidder box.
**Test:** test_bid_box_layout

| Condition | Result |
|-----------|--------|
| Structural verification | PASSED - box bytes[0:8] = bid amount, bytes[8:16] = timestamp |

No toggle possible - the fix is the data layout itself.

## F-03: update_application Admin Guard

**Guard:** assert Txn.sender == self.admin.value in FryMarket.update_application baremethod
**Test:** test_non_admin_cannot_update

| Condition | Result |
|-----------|--------|
| With guard | PASSED - non-admin update rejected |
| Without guard (replaced with pass) | FAILED - DID NOT RAISE (non-admin update succeeded) |

## F-04: Cancel During Live Auction

**Guard:** assert Global.latest_timestamp < auction.bidding_start_time.native in FryAuction.cancel_nft_auction
**Test:** test_cancel_after_bidding_starts_fails

| Condition | Result |
|-----------|--------|
| With guard | PASSED - cancel after start rejected |
| Without guard (replaced with pass) | FAILED - DID NOT RAISE (cancel succeeded during live auction) |

Note: Devmode localnet requires forcing a block after sleep to advance Global.LatestTimestamp.

## F-05: Highest Bidder Cannot Cancel

**Guard:** assert Txn.sender != self.highest_bidder.value in FryAuctionBidding.cancel_bid
**Test:** test_highest_bidder_cannot_cancel

| Condition | Result |
|-----------|--------|
| With guard | PASSED - highest bidder cancel rejected |
| Without guard | FAILED - highest bidder cancel succeeded (funds drained) |

## F-07: Factory Pattern Validation

**Fix:** Bidding contract created via inner-txn in FryAuction.list_nft_on_auction. Validated in claim_nft_royalty by checking bidding_app.creator == Global.current_application_address.
**Test:** test_claim_with_unauthorized_bidding_app_fails

| Condition | Result |
|-----------|--------|
| Factory pattern active | PASSED - claim with externally-created app rejected |

No single assert to toggle - the factory architecture IS the fix.

## F-08: Auction Time Validation

**Guard:** assert bidding_start_time > Global.latest_timestamp and assert bidding_end_time > bidding_start_time in FryAuction.list_nft_on_auction
**Test:** test_list_with_past_start_time_fails

| Condition | Result |
|-----------|--------|
| With guard | PASSED - past start time rejected |
| Without guard | FAILED - DID NOT RAISE (auction listed with invalid times) |

---

## Summary

| Finding | Type | Proven | Method |
|---------|------|--------|--------|
| F-01 | Toggle | YES | Assert removal -> test flips |
| F-02 | Structural | YES | Byte layout verified |
| F-03 | Toggle | YES | Assert -> pass -> test flips |
| F-04 | Toggle | YES | Assert -> pass -> test flips |
| F-05 | Toggle | YES | Assert removal -> test flips |
| F-07 | Architectural | YES | Fake app rejected by creator check |
| F-08 | Toggle | YES | Assert removal -> test flips |

All 7 findings proven. Test suite: 14/14 passing.
