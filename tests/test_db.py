from decimal import Decimal
from datetime import UTC, datetime

import pytest

from megafon_desktop.domain.models import AccountSnapshot
from megafon_desktop.infra.db import Database


def test_phone_normalization_and_snapshot(tmp_path):
    db = Database(tmp_path / "test.db")
    account = db.add_account("8 (999) 123-45-67", "test")
    assert account.phone == "79991234567"
    assert account.id is not None

    db.add_snapshot(
        AccountSnapshot(
            account_id=account.id,
            captured_at=datetime.now(UTC),
            balance=Decimal("123.45"),
            commercial_balance=Decimal("100.00"),
        )
    )
    latest = db.latest_snapshot(account.id)
    assert latest is not None
    assert latest["balance"] == "123.45"


@pytest.mark.parametrize("value", ["123", "7999", "+1 555 123 4567"])
def test_invalid_phone_rejected(tmp_path, value):
    db = Database(tmp_path / "test.db")
    with pytest.raises(ValueError):
        db.add_account(value)
