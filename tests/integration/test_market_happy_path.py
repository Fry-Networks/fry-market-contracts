"""Happy path: list NFT -> buy NFT on FryMarket."""
import pytest
from algokit_utils import (
    AppClientMethodCallParams,
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryParams,
)
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.applications.app_client import FundAppAccountParams
from algosdk.transaction import AssetTransferTxn, PaymentTxn
from algosdk.atomic_transaction_composer import TransactionWithSigner
from tests.conftest import _load_spec, create_test_nft, opt_in_asset


def test_list_and_buy(algorand, creator, buyer, dispenser):
    """Full lifecycle: create market -> list NFT -> buyer purchases."""
    # Deploy market
    spec = _load_spec("fry_market/FryMarket.arc56.json")
    factory = AppFactory(AppFactoryParams(
        algorand=algorand, app_spec=spec,
        default_sender=creator.address, default_signer=creator.signer,
    ))
    app_client, _ = factory.send.create(
        AppFactoryCreateMethodCallParams(method="create", args=[0, 250, 500])
    )
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount(algo=10)))

    # Create NFT
    asset_id = create_test_nft(algorand, creator)

    # App opts in to NFT
    app_client.send.call(AppClientMethodCallParams(
        method="asset_opt_in", args=[asset_id],
        extra_fee=AlgoAmount(micro_algo=1000),
    ))

    # List the NFT at 5 ALGO
    price = 5_000_000
    sp = algorand.client.algod.suggested_params()
    nft_txn = AssetTransferTxn(
        sender=creator.address, sp=sp,
        receiver=app_client.app_address, amt=1, index=asset_id,
    )
    tws = TransactionWithSigner(txn=nft_txn, signer=creator.signer)

    app_client.send.call(AppClientMethodCallParams(
        method="list_asset",
        args=[asset_id, price, 0, 1, tws],  # collection=0, is_primary=1
        box_references=[b"l" + asset_id.to_bytes(8, "big")],
        asset_references=[asset_id],
    ))

    # Buyer opts in to NFT
    opt_in_asset(algorand, buyer, asset_id)

    # Buyer purchases
    sp = algorand.client.algod.suggested_params()
    pay_txn = PaymentTxn(
        sender=buyer.address, sp=sp,
        receiver=app_client.app_address, amt=price,
    )
    pay_tws = TransactionWithSigner(txn=pay_txn, signer=buyer.signer)

    app_client.send.call(AppClientMethodCallParams(
        method="buy_nft_royalty",
        extra_fee=AlgoAmount(micro_algo=3000),
        args=[asset_id, pay_tws],
        sender=buyer.address, signer=buyer.signer,
        box_references=[b"l" + asset_id.to_bytes(8, "big")],
        asset_references=[asset_id],
        account_references=[creator.address],
    ))

    # Verify buyer now holds the NFT
    buyer_info = algorand.client.algod.account_asset_info(buyer.address, asset_id)
    assert buyer_info["asset-holding"]["amount"] == 1
