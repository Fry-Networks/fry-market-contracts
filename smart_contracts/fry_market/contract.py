# SPDX-License-Identifier: MIT
# fry-market-contracts :: fry_market

from algopy import (
    ARC4Contract,
    Account,
    Asset,
    BoxMap,
    Global,
    GlobalState,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
)


class ListingValue(arc4.Struct):
    seller: arc4.Address
    price: arc4.UInt64
    status: arc4.UInt64
    listed_at: arc4.UInt64
    collection_id: arc4.UInt64
    is_primary: arc4.UInt64
    reserved: arc4.UInt64


class FryMarket(ARC4Contract):
    def __init__(self) -> None:
        self.admin = GlobalState(Account)
        self.fry_id = GlobalState(UInt64)
        self.primary_fee = GlobalState(UInt64)
        self.secondary_fee = GlobalState(UInt64)
        self.listings = BoxMap(UInt64, ListingValue, key_prefix=b"l")
        self.royalties = BoxMap(Account, UInt64, key_prefix=b"r")
        self.collections = BoxMap(UInt64, Account, key_prefix=b"c")

    @arc4.abimethod(create="require")
    def create(self, fry_id: UInt64, primary_fee: UInt64, secondary_fee: UInt64) -> None:
        self.admin.value = Txn.sender
        self.fry_id.value = fry_id
        self.primary_fee.value = primary_fee
        self.secondary_fee.value = secondary_fee

    @arc4.abimethod
    def update_primary_fee(self, fee: UInt64) -> None:
        assert Txn.sender == self.admin.value
        self.primary_fee.value = fee

    @arc4.abimethod
    def update_secondary_fee(self, fee: UInt64) -> None:
        assert Txn.sender == self.admin.value
        self.secondary_fee.value = fee

    @arc4.abimethod
    def asset_opt_in(self, asset: Asset) -> None:
        assert Txn.sender == self.admin.value
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    @arc4.abimethod
    def create_collection(self, collection_id: UInt64, creator: Account) -> None:
        assert Txn.sender == self.admin.value
        self.collections[collection_id] = creator

    @arc4.abimethod
    def add_royalty(self, collection_id: UInt64, royalty_percent: UInt64) -> None:
        # F-01: Only the collection creator can set royalties
        collection_creator = self.collections[collection_id]
        assert Txn.sender == collection_creator
        self.royalties[Txn.sender] = royalty_percent

    @arc4.abimethod
    def list_asset(
        self,
        asset: Asset,
        price: UInt64,
        collection_id: UInt64,
        is_primary: UInt64,
        nft_txn: gtxn.AssetTransferTransaction,
    ) -> None:
        assert nft_txn.asset_receiver == Global.current_application_address
        assert nft_txn.xfer_asset == asset
        assert nft_txn.asset_amount == UInt64(1)
        self.listings[asset.id] = ListingValue(
            seller=arc4.Address(Txn.sender),
            price=arc4.UInt64(price),
            status=arc4.UInt64(1),
            listed_at=arc4.UInt64(Global.latest_timestamp),
            collection_id=arc4.UInt64(collection_id),
            is_primary=arc4.UInt64(is_primary),
            reserved=arc4.UInt64(0),
        )

    @arc4.abimethod
    def update_price(self, asset: Asset, new_price: UInt64) -> None:
        listing = self.listings[asset.id].copy()
        assert listing.seller == arc4.Address(Txn.sender)
        self.listings[asset.id] = ListingValue(
            seller=listing.seller,
            price=arc4.UInt64(new_price),
            status=listing.status,
            listed_at=listing.listed_at,
            collection_id=listing.collection_id,
            is_primary=listing.is_primary,
            reserved=listing.reserved,
        )

    @arc4.abimethod
    def cancel_list(self, asset: Asset) -> None:
        listing = self.listings[asset.id].copy()
        assert listing.seller == arc4.Address(Txn.sender)
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Txn.sender,
            asset_amount=1,
        ).submit()
        del self.listings[asset.id]

    @arc4.abimethod
    def buy_nft_royalty(self, asset: Asset, payment: gtxn.PaymentTransaction) -> None:
        listing = self.listings[asset.id].copy()
        assert listing.status == arc4.UInt64(1)

        price = listing.price.native
        assert payment.amount >= price
        assert payment.receiver == Global.current_application_address

        seller = listing.seller.native
        collection_id = listing.collection_id.native
        is_primary = listing.is_primary.native

        # Platform fee
        if is_primary:
            fee_bps = self.primary_fee.value
        else:
            fee_bps = self.secondary_fee.value
        fee_amount = price * fee_bps // UInt64(10000)
        seller_amount = price - fee_amount

        # Royalty to collection creator (if set)
        if collection_id in self.collections:
            creator = self.collections[collection_id]
            if creator in self.royalties:
                royalty_bps = self.royalties[creator]
                royalty_amount = price * royalty_bps // UInt64(10000)
                seller_amount = seller_amount - royalty_amount
                itxn.Payment(
                    receiver=creator,
                    amount=royalty_amount,
                ).submit()

        # Pay seller
        itxn.Payment(
            receiver=seller,
            amount=seller_amount,
        ).submit()

        # Transfer NFT to buyer
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Txn.sender,
            asset_amount=1,
        ).submit()

        # Mark as sold
        self.listings[asset.id] = ListingValue(
            seller=listing.seller,
            price=listing.price,
            status=arc4.UInt64(2),
            listed_at=listing.listed_at,
            collection_id=listing.collection_id,
            is_primary=listing.is_primary,
            reserved=listing.reserved,
        )

    @arc4.baremethod(allow_actions=["UpdateApplication"])
    def update_application(self) -> None:
        # F-03: Only admin can update the application
        assert Txn.sender == self.admin.value
