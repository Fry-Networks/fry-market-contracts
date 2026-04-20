"""F-08: listNftOnAuction must validate bidStart and bidEnd.

Phase 6 implementation notes:
- listNftOnAuction with bidStartTime < current round -> MUST FAIL.
- listNftOnAuction with bidEndTime <= bidStartTime -> MUST FAIL.
- listNftOnAuction with future bidStart + bidEnd > bidStart -> MUST SUCCEED.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_past_bid_start_rejected():
    raise NotImplementedError()


@pytest.mark.skip(reason="Phase 6")
def test_bid_end_before_start_rejected():
    raise NotImplementedError()
