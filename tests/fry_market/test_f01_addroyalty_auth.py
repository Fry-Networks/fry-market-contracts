"""F-01: Only collection creator can set royalties."""
import pytest
from algokit_utils.models.amount import AlgoAmount
from algokit_utils import AppClientMethodCallParams
from algokit_utils.applications.app_client import LogicError
from algosdk.encoding import decode_address


def test_add_royalty_by_creator_succeeds(deploy_market, algorand, creator):
    """Collection creator CAN add royalty."""
    app = deploy_market
    # Create a collection with creator as the collection creator
    app.send.call(AppClientMethodCallParams(
        method="create_collection",
        args=[1, creator.address],
    ))
    # Creator adds royalty - should succeed
    app.send.call(AppClientMethodCallParams(
        method="add_royalty",
        args=[1, 500],  # 5% royalty
        box_references=[b"r" + decode_address(creator.address)],
    ))


def test_add_royalty_by_non_creator_fails(deploy_market, algorand, creator, buyer):
    """Non-creator CANNOT add royalty (F-01 guard)."""
    app = deploy_market
    # Create collection with creator as owner
    app.send.call(AppClientMethodCallParams(
        method="create_collection",
        args=[2, creator.address],
    ))
    # Buyer (non-creator) tries to add royalty - must fail
    with pytest.raises(LogicError):
        app.send.call(AppClientMethodCallParams(
            method="add_royalty",
            args=[2, 500],
            sender=buyer.address,
            signer=buyer.signer,
        ))
