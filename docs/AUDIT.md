# fry.market Smart Contract Audit - Remediation Tracking

## Status matrix

| ID   | Severity | Target                      | Status                                     |
|------|----------|-----------------------------|--------------------------------------------|
| F-01 | HIGH     | addRoyalty (market+auction) | TODO: creator-only auth                    |
| F-02 | HIGH     | FryAuctionBidding.bid       | TODO: box offset 40 -> 8                   |
| F-03 | MEDIUM   | Admin rotation              | TODO: updateApplication handler (admin-only) |
| F-04 | MEDIUM   | cancelNftAuction            | TODO: end-time guard                       |
| F-05 | MEDIUM   | cancelBid                   | TODO: validate previousHighestBidder       |
| F-06 | LOW      | frontend cosmetic           | out of scope (frontend workstream)         |
| F-07 | LOW      | biddingContract app ID      | TODO: factory pattern or creator check     |
| F-08 | LOW      | bidStart/bidEnd             | TODO: timestamp guards                     |
| F-09 | INFO     | fee truncation              | documented, not practically exploitable    |
| F-10 | HIGH     | backend /buy-nft etc        | FIXED (backend hardening phase)            |
| F-11 | HIGH     | testingTxn rekeyTo          | FIXED (backend hardening phase)            |
| F-12 | LOW      | AlgoMarket/ARC18 tests      | out of scope (contracts deferred)          |
| F-13 | LOW      | FryNftAuction bid           | out of scope (contract not rewritten)      |
| F-14 | INFO     | unused client bundle        | out of scope (frontend workstream)         |

## Design notes

### addRoyalty creator-only auth (F-01)
createCollection stores creator in the collection box. addRoyalty reads
that box and asserts Txn.sender == box.creator.

### Admin rotation (F-03)
Admin-only updateApplication. New admin address passed as argument, old
admin signs the update.

### Creator -> collection mapping
Inherent in createCollection boxes. Exact box schema confirmed during
Phase 5 contract recon.
