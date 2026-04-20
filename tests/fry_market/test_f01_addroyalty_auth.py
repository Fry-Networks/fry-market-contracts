"""F-01: addRoyalty authorization must be creator-restricted.

Phase 6 implementation notes:
- Deploy fresh FryMarket.
- Creator A creates collection X.
- Attacker B calls addRoyalty(royalty_basis, collection_X) -> MUST FAIL.
- Creator A calls addRoyalty for their own collection -> MUST SUCCEED.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_non_creator_cannot_set_royalty():
    raise NotImplementedError()


@pytest.mark.skip(reason="Phase 6")
def test_creator_can_set_own_royalty():
    raise NotImplementedError()
