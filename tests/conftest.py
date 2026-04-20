"""Shared pytest fixtures for fry-market-contracts.

Phase 6 will populate these fixtures with:
  - algokit_utils.AlgorandClient pointed at ATLAS00 localnet
  - KMD-managed dispenser account (no mnemonic handling)
  - Per-test fresh creator/buyer/bidder accounts funded from dispenser
  - Compiled + deployed fresh contract instances per test class

Populate in Phase 6. Skeleton only for now.
"""
import pytest


@pytest.fixture(scope="session")
def algorand_client():
    """algokit_utils.AlgorandClient pointed at localnet."""
    raise NotImplementedError("Populate in Phase 6")


@pytest.fixture(scope="session")
def dispenser(algorand_client):
    """KMD-managed dispenser account."""
    raise NotImplementedError("Populate in Phase 6")


@pytest.fixture
def creator(algorand_client, dispenser):
    """Fresh funded creator account per test."""
    raise NotImplementedError("Populate in Phase 6")


@pytest.fixture
def buyer(algorand_client, dispenser):
    """Fresh funded buyer account per test."""
    raise NotImplementedError("Populate in Phase 6")


@pytest.fixture
def bidder_a(algorand_client, dispenser):
    raise NotImplementedError("Populate in Phase 6")


@pytest.fixture
def bidder_b(algorand_client, dispenser):
    raise NotImplementedError("Populate in Phase 6")
