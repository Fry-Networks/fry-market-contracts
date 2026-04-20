import json
import pytest
from pathlib import Path

from algokit_utils import (
    AlgorandClient,
    AppClient,
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryParams,
    AppClientMethodCallParams,
)
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.applications.app_client import FundAppAccountParams
from algosdk.transaction import AssetCreateTxn, AssetTransferTxn, PaymentTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner

ARTIFACTS = Path(__file__).parent.parent / "smart_contracts" / "artifacts"


@pytest.fixture(scope="session")
def algorand():
    return AlgorandClient.default_localnet()


@pytest.fixture(scope="session")
def dispenser(algorand):
    return algorand.account.localnet_dispenser()


@pytest.fixture
def creator(algorand, dispenser):
    acct = algorand.account.random()
    algorand.account.ensure_funded(acct, dispenser, AlgoAmount(algo=100))
    return acct


@pytest.fixture
def buyer(algorand, dispenser):
    acct = algorand.account.random()
    algorand.account.ensure_funded(acct, dispenser, AlgoAmount(algo=100))
    return acct


@pytest.fixture
def bidder_a(algorand, dispenser):
    acct = algorand.account.random()
    algorand.account.ensure_funded(acct, dispenser, AlgoAmount(algo=100))
    return acct


@pytest.fixture
def bidder_b(algorand, dispenser):
    acct = algorand.account.random()
    algorand.account.ensure_funded(acct, dispenser, AlgoAmount(algo=100))
    return acct


def _load_spec(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text())


@pytest.fixture
def market_factory(algorand, creator):
    spec = _load_spec("fry_market/FryMarket.arc56.json")
    return AppFactory(AppFactoryParams(
        algorand=algorand,
        app_spec=spec,
        default_sender=creator.address,
        default_signer=creator.signer,
    ))


@pytest.fixture
def auction_factory(algorand, creator):
    spec = _load_spec("fry_auction/FryAuction.arc56.json")
    return AppFactory(AppFactoryParams(
        algorand=algorand,
        app_spec=spec,
        default_sender=creator.address,
        default_signer=creator.signer,
    ))


@pytest.fixture
def bidding_factory(algorand, creator):
    spec = _load_spec("fry_auction_bidding/FryAuctionBidding.arc56.json")
    return AppFactory(AppFactoryParams(
        algorand=algorand,
        app_spec=spec,
        default_sender=creator.address,
        default_signer=creator.signer,
    ))


@pytest.fixture
def deploy_market(market_factory, algorand, creator):
    """Deploy a fresh FryMarket with default params, return AppClient."""
    app_client, _ = market_factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create",
            args=[0, 250, 500],  # fry_id=0, primary=2.5%, secondary=5%
        )
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))
    return app_client


@pytest.fixture
def deploy_auction(auction_factory, algorand, creator):
    """Deploy a fresh FryAuction with default params, return AppClient."""
    app_client, _ = auction_factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create",
            args=[0, 250, 500],
        )
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))
    return app_client


@pytest.fixture
def deploy_bidding(bidding_factory, algorand, creator):
    """Deploy a fresh FryAuctionBidding, return AppClient."""
    import time
    now = int(time.time())
    app_client, _ = bidding_factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create",
            args=[
                1,                  # asset_id
                creator.address,    # seller
                1_000_000,          # bid_start_amount (1 ALGO)
                100_000,            # min_bid_amount (0.1 ALGO)
                now + 10,           # bidding_start_time (10s from now)
                now + 3600,         # bidding_end_time (1h from now)
            ],
        )
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))
    return app_client


def create_test_nft(algorand, creator) -> int:
    """Create a test NFT (ASA with total=1, decimals=0) and return asset ID."""
    sp = algorand.client.algod.suggested_params()
    txn = AssetCreateTxn(
        sender=creator.address,
        sp=sp,
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name="TNFT",
        asset_name="Test NFT",
    )
    signed = txn.sign(creator.private_key)
    txid = algorand.client.algod.send_transaction(signed)
    result = algorand.client.algod.pending_transaction_info(txid)
    # Wait for confirmation
    from algosdk.transaction import wait_for_confirmation
    result = wait_for_confirmation(algorand.client.algod, txid, 4)
    return result["asset-index"]


def opt_in_asset(algorand, account, asset_id: int):
    """Opt account into an asset."""
    sp = algorand.client.algod.suggested_params()
    txn = AssetTransferTxn(
        sender=account.address,
        sp=sp,
        receiver=account.address,
        amt=0,
        index=asset_id,
    )
    signed = txn.sign(account.private_key)
    txid = algorand.client.algod.send_transaction(signed)
    from algosdk.transaction import wait_for_confirmation
    wait_for_confirmation(algorand.client.algod, txid, 4)


def transfer_nft(algorand, sender, receiver_addr: str, asset_id: int):
    """Transfer 1 unit of asset from sender to receiver."""
    sp = algorand.client.algod.suggested_params()
    txn = AssetTransferTxn(
        sender=sender.address,
        sp=sp,
        receiver=receiver_addr,
        amt=1,
        index=asset_id,
    )
    signed = txn.sign(sender.private_key)
    txid = algorand.client.algod.send_transaction(signed)
    from algosdk.transaction import wait_for_confirmation
    wait_for_confirmation(algorand.client.algod, txid, 4)
