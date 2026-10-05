from datetime import UTC, datetime
from decimal import Decimal

from megafon_desktop.domain.models import AccountSnapshot, AccountStatus
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.services.account_service import AccountService


class FakeTransport:
    def refresh_snapshot(self, phone: str, password: str, account_id: int) -> AccountSnapshot:
        assert phone == "79991234567"
        assert password == "secret"
        return AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=Decimal("42.50"),
            commercial_balance=Decimal("40.00"),
        )


def test_add_and_refresh_account(tmp_path):
    db = Database(tmp_path / "test.db")
    service = AccountService(db, MemorySecretStore(), FakeTransport())
    account = service.add_account("9991234567", "secret", "main")
    assert account.id is not None

    result = service.refresh(account.id)
    assert result.snapshot is not None
    assert result.snapshot.balance == Decimal("42.50")
    assert result.account.status == AccountStatus.OK
