# fry-market-contracts

AlgoPy smart contracts for fry.market NFT marketplace.

## Contracts

- FryMarket - primary NFT listing/buy marketplace
- FryAuction - NFT auction coordinator
- FryAuctionBidding - per-auction bidding sub-app

## Development

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .[dev]

Compile (AlgoPy via puyapy):

    python3 -m puyapy smart_contracts/fry_market/contract.py --out-dir smart_contracts/artifacts/fry_market

## Deployment targets

- Localnet: ATLAS00 (100.69.195.100) via algokit localnet
- Mainnet: via WC signer on HERMES00

## Audit remediation tracking

See docs/AUDIT.md for F-01..F-14 findings and remediation status.
