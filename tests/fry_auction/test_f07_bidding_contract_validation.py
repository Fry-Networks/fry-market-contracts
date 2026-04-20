"""F-07: listNftOnAuction must validate biddingContract app ID.

Phase 6 implementation notes:
- Attacker deploys fake bidding contract.
- Attacker calls listNftOnAuction with fake biddingContract ID -> MUST FAIL.
- Legitimate listNftOnAuction with factory-created biddingContract -> MUST SUCCEED.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_malicious_bidding_contract_rejected():
    raise NotImplementedError()
