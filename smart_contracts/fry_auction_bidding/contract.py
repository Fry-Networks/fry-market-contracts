# SPDX-License-Identifier: MIT
# fry-market-contracts :: fry_auction_bidding

from algopy import (
    ARC4Contract,
    Account,
    BoxMap,
    Global,
    GlobalState,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
)


class BidValue(arc4.Struct):
    amount: arc4.UInt64
    timestamp: arc4.UInt64


class FryAuctionBidding(ARC4Contract):
    def __init__(self) -> None:
        self.asset_id = GlobalState(UInt64)
        self.seller = GlobalState(Account)
        self.bid_start_amount = GlobalState(UInt64)
        self.min_bid_amount = GlobalState(UInt64)
        self.bidding_start_time = GlobalState(UInt64)
        self.bidding_end_time = GlobalState(UInt64)
        self.highest_bid = GlobalState(UInt64)
        self.highest_bidder = GlobalState(Account)
        self.total_bidders = GlobalState(UInt64)
        self.bids = BoxMap(Account, BidValue, key_prefix=b"b")

    @arc4.abimethod(create="require")
    def create(
        self,
        asset_id: UInt64,
        seller: Account,
        bid_start_amount: UInt64,
        min_bid_amount: UInt64,
        bidding_start_time: UInt64,
        bidding_end_time: UInt64,
    ) -> None:
        self.asset_id.value = asset_id
        self.seller.value = seller
        self.bid_start_amount.value = bid_start_amount
        self.min_bid_amount.value = min_bid_amount
        self.bidding_start_time.value = bidding_start_time
        self.bidding_end_time.value = bidding_end_time
        self.highest_bid.value = UInt64(0)
        self.highest_bidder.value = Global.zero_address
        self.total_bidders.value = UInt64(0)

    @arc4.abimethod
    def bid(self, payment: gtxn.PaymentTransaction) -> None:
        assert Global.latest_timestamp >= self.bidding_start_time.value
        assert Global.latest_timestamp <= self.bidding_end_time.value
        assert payment.amount >= self.bid_start_amount.value
        assert payment.amount >= self.highest_bid.value + self.min_bid_amount.value
        assert payment.receiver == Global.current_application_address

        # Track new bidders before writing box
        is_new = Txn.sender not in self.bids
        if is_new:
            self.total_bidders.value = self.total_bidders.value + UInt64(1)

        # F-02: Write [amount, timestamp] at offset 0 — full 16B box
        self.bids[Txn.sender] = BidValue(
            amount=arc4.UInt64(payment.amount),
            timestamp=arc4.UInt64(Global.latest_timestamp),
        )

        self.highest_bid.value = payment.amount
        self.highest_bidder.value = Txn.sender

    @arc4.abimethod
    def cancel_bid(self) -> None:
        # F-05: Read caller's OWN box, not a passed-in address
        assert Txn.sender in self.bids
        bid = self.bids[Txn.sender].copy()

        # Cannot cancel if you are the highest bidder
        assert Txn.sender != self.highest_bidder.value

        refund_amount = bid.amount.native

        # Delete box and update counter
        del self.bids[Txn.sender]
        self.total_bidders.value = self.total_bidders.value - UInt64(1)

        # Refund the bidder
        itxn.Payment(
            receiver=Txn.sender,
            amount=refund_amount,
        ).submit()
