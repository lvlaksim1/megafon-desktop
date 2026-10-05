from datetime import UTC, datetime
from decimal import Decimal

import pytest

from megafon_desktop.domain.models import AccountRefresh, AccountSnapshot, AccountStatus
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.megafon.transport import CaptchaSolver
from megafon_desktop.services.account_service import AccountService


class FakeTransport:
    def __init__(self) -> None:
        self.forgotten: list[int] = []
        self.blocked = False

    def refresh_account(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> AccountRefresh:
        assert phone == "79991234567"
        assert password == "secret"
        assert captcha_solver is None
        return AccountRefresh(
            AccountSnapshot(
                account_id=account_id,
                captured_at=datetime.now(UTC),
                balance=Decimal("42.50"),
                commercial_balance=Decimal("40.00"),
                blocked=self.blocked,
            )
        )

    def set_blocking(
        self,
        phone: str,
        password: str,
        account_id: int,
        enabled: bool,
        captcha_solver: CaptchaSolver | None = None,
    ) -> bool:
        del account_id, captcha_solver
        assert phone == "79991234567"
        assert password == "secret"
        self.blocked = enabled
        return enabled

    def forget_session(self, account_id: int) -> None:
        self.forgotten.append(account_id)


def test_add_refresh_and_block_account(tmp_path):
    db = Database(tmp_path / "test.db")
    service = AccountService(db, MemorySecretStore(), FakeTransport())
    account = service.add_account("9991234567", "secret", "main")
    assert account.id is not None

    result = service.refresh(account.id)
    assert result.snapshot is not None
    assert result.snapshot.balance == Decimal("42.50")
    assert result.account.status == AccountStatus.OK

    updated, blocked = service.set_blocking(account.id, True)
    assert blocked is True
    assert updated.status == AccountStatus.OK
    latest = db.latest_snapshot(account.id)
    assert latest is not None
    assert latest["blocked"] == 1


def test_delete_account_removes_password_session_and_database_row(tmp_path):
    db = Database(tmp_path / "test.db")
    secrets = MemorySecretStore()
    transport = FakeTransport()
    service = AccountService(db, secrets, transport)
    account = service.add_account("9991234567", "secret", "main")
    assert account.id is not None

    secrets.set(f"account-{account.id}-http-session", "saved")
    service.delete_account(account.id)

    assert secrets.get(f"account-{account.id}-password") is None
    assert transport.forgotten == [account.id]
    with pytest.raises(KeyError):
        db.get_account(account.id)
