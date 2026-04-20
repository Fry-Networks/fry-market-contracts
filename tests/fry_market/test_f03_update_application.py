"""F-03: Admin rotation via updateApplication.

Phase 6 implementation notes:
- Deploy fresh FryMarket with admin A.
- Non-admin B calls updateApplication -> MUST FAIL.
- Admin A calls updateApplication -> MUST SUCCEED.
- After update, confirm approval program hash changed.
"""
import pytest


@pytest.mark.skip(reason="Phase 6")
def test_non_admin_cannot_update_application():
    raise NotImplementedError()


@pytest.mark.skip(reason="Phase 6")
def test_admin_can_update_application():
    raise NotImplementedError()
