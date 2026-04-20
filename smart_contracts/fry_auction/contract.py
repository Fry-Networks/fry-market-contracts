# SPDX-License-Identifier: MIT
# fry-market-contracts :: fry_auction

from algopy import (
    ARC4Contract,
    Account,
    Application,
    Asset,
    BoxMap,
    Bytes,
    Global,
    GlobalState,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
)


class AuctionValue(arc4.Struct):
    seller: arc4.Address
    asset_id: arc4.UInt64
    bid_start_amount: arc4.UInt64
    min_bid_amount: arc4.UInt64
    bidding_app_id: arc4.UInt64
    highest_bidder: arc4.Address
    highest_bid: arc4.UInt64
    bidding_start_time: arc4.UInt64
    bidding_end_time: arc4.UInt64
    status: arc4.UInt64
    collection_id: arc4.UInt64


class FryAuction(ARC4Contract):
    def __init__(self) -> None:
        self.admin = GlobalState(Account)
        self.fry_id = GlobalState(UInt64)
        self.primary_fee = GlobalState(UInt64)
        self.secondary_fee = GlobalState(UInt64)
        self.auctions = BoxMap(UInt64, AuctionValue, key_prefix=b"a")
        self.royalties = BoxMap(Account, UInt64, key_prefix=b"r")
        self.collections = BoxMap(UInt64, Account, key_prefix=b"c")

    @arc4.abimethod(create="require")
    def create(self, fry_id: UInt64, primary_fee: UInt64, secondary_fee: UInt64) -> None:
        self.admin.value = Txn.sender
        self.fry_id.value = fry_id
        self.primary_fee.value = primary_fee
        self.secondary_fee.value = secondary_fee

    @arc4.abimethod
    def asset_opt_in(self, asset: Asset) -> None:
        assert Txn.sender == self.admin.value
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    @arc4.abimethod
    def add_royalty(self, collection_id: UInt64, royalty_percent: UInt64) -> None:
        # F-01: Only the collection creator can set royalties
        collection_creator = self.collections[collection_id]
        assert Txn.sender == collection_creator
        self.royalties[Txn.sender] = royalty_percent

    @arc4.abimethod
    def list_nft_on_auction(
        self,
        asset: Asset,
        bid_start_amount: UInt64,
        min_bid_amount: UInt64,
        bidding_start_time: UInt64,
        bidding_end_time: UInt64,
        collection_id: UInt64,
        nft_txn: gtxn.AssetTransferTransaction,
        bidding_approval: Bytes,
        bidding_clear: Bytes,
    ) -> None:
        # Verify NFT sent to this contract
        assert nft_txn.asset_receiver == Global.current_application_address
        assert nft_txn.xfer_asset == asset
        assert nft_txn.asset_amount == UInt64(1)

        # F-08: Time validation guards
        assert bidding_start_time > Global.latest_timestamp
        assert bidding_end_time > bidding_start_time

        # F-07: Factory pattern - create bidding app via inner txn
        create_txn = itxn.ApplicationCall(
            approval_program=bidding_approval,
            clear_state_program=bidding_clear,
            global_num_uint=UInt64(9),
            global_num_bytes=UInt64(2),
            app_args=(
                arc4.arc4_signature("create(uint64,address,uint64,uint64,uint64,uint64)void"),
                arc4.UInt64(asset.id).bytes,
                arc4.Address(Txn.sender).bytes,
                arc4.UInt64(bid_start_amount).bytes,
                arc4.UInt64(min_bid_amount).bytes,
                arc4.UInt64(bidding_start_time).bytes,
                arc4.UInt64(bidding_end_time).bytes,
            ),
            accounts=(Txn.sender,),
        ).submit()

        bidding_app_id = create_txn.created_app.id

        # Store auction data
        self.auctions[asset.id] = AuctionValue(
            seller=arc4.Address(Txn.sender),
            asset_id=arc4.UInt64(asset.id),
            bid_start_amount=arc4.UInt64(bid_start_amount),
            min_bid_amount=arc4.UInt64(min_bid_amount),
            bidding_app_id=arc4.UInt64(bidding_app_id),
            highest_bidder=arc4.Address(Global.zero_address),
            highest_bid=arc4.UInt64(0),
            bidding_start_time=arc4.UInt64(bidding_start_time),
            bidding_end_time=arc4.UInt64(bidding_end_time),
            status=arc4.UInt64(1),
            collection_id=arc4.UInt64(collection_id),
        )

    @arc4.abimethod
    def cancel_nft_auction(self, asset: Asset) -> None:
        auction = self.auctions[asset.id].copy()
        assert auction.seller == arc4.Address(Txn.sender)
        assert auction.status == arc4.UInt64(1)

        # F-04: Can only cancel BEFORE bidding starts
        assert Global.latest_timestamp < auction.bidding_start_time.native

        # Return NFT to seller
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Txn.sender,
            asset_amount=1,
        ).submit()

        # Mark cancelled
        self.auctions[asset.id] = AuctionValue(
            seller=auction.seller,
            asset_id=auction.asset_id,
            bid_start_amount=auction.bid_start_amount,
            min_bid_amount=auction.min_bid_amount,
            bidding_app_id=auction.bidding_app_id,
            highest_bidder=auction.highest_bidder,
            highest_bid=auction.highest_bid,
            bidding_start_time=auction.bidding_start_time,
            bidding_end_time=auction.bidding_end_time,
            status=arc4.UInt64(0),
            collection_id=auction.collection_id,
        )

    @arc4.abimethod
    def claim_nft_royalty(
        self,
        asset: Asset,
        bidding_app: Application,
    ) -> None:
        auction = self.auctions[asset.id].copy()
        assert auction.status == arc4.UInt64(1)
        assert auction.bidding_app_id.native == bidding_app.id

        # F-07: Validate bidding app creator is this contract
        assert bidding_app.creator == Global.current_application_address

        # Auction must have ended
        assert Global.latest_timestamp > auction.bidding_end_time.native

        # Read winning bid from bidding app state
        highest_bid, bid_exists = op.AppGlobal.get_ex_uint64(bidding_app, b"highest_bid")
        assert bid_exists
        winning_amount = highest_bid

        highest_bidder_bytes, bidder_exists = op.AppGlobal.get_ex_bytes(bidding_app, b"highest_bidder")
        assert bidder_exists
        winner = Account.from_bytes(highest_bidder_bytes)

        assert winning_amount > UInt64(0)

        seller = auction.seller.native

        # Platform fee
        fee_bps = self.secondary_fee.value
        fee_amount = winning_amount * fee_bps // UInt64(10000)
        seller_amount = winning_amount - fee_amount

        # Royalty to collection creator
        collection_id = auction.collection_id.native
        if collection_id in self.collections:
            creator = self.collections[collection_id]
            if creator in self.royalties:
                royalty_bps = self.royalties[creator]
                royalty_amount = winning_amount * royalty_bps // UInt64(10000)
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

        # Transfer NFT to winner
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=winner,
            asset_amount=1,
        ).submit()

        # Mark settled
        self.auctions[asset.id] = AuctionValue(
            seller=auction.seller,
            asset_id=auction.asset_id,
            bid_start_amount=auction.bid_start_amount,
            min_bid_amount=auction.min_bid_amount,
            bidding_app_id=auction.bidding_app_id,
            highest_bidder=arc4.Address(winner),
            highest_bid=arc4.UInt64(winning_amount),
            bidding_start_time=auction.bidding_start_time,
            bidding_end_time=auction.bidding_end_time,
            status=arc4.UInt64(2),
            collection_id=auction.collection_id,
        )

    @arc4.baremethod(allow_actions=["UpdateApplication"])
    def update_application(self) -> None:
        # F-03: Only admin can update the application
        assert Txn.sender == self.admin.value
