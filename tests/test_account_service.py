from datetime import UTC, datetime
from decimal import Decimal

import pytest

from megafon_desktop.domain.models import (
    AccountRefresh,
    AccountSnapshot,
    AccountStatus,
    PersonalOffer,
)
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.megafon.transport import CaptchaSolver
from megafon_desktop.services.account_service import AccountService


class FakeTransport:
    def __init__(self) -> None:
        self.forgotten: list[int] = []
        self.blocked = False
        self.offers: list[PersonalOffer] = []
        self.rejected: list[str] = []

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
            ),
            list(self.offers),
        )

    def reject_offers(
        self,
        phone: str,
        password: str,
        account_id: int,
        offer_ids: list[str],
        captcha_solver: CaptchaSolver | None = None,
    ) -> list[PersonalOffer]:
        del phone, password, account_id, captcha_solver
        self.rejected.extend(offer_ids)
        rejected = set(offer_ids)
        self.offers = [offer for offer in self.offers if offer.offer_id not in rejected]
        return list(self.offers)

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


def test_add_refresh_and_block_account_preserves_label(tmp_path):
    db = Database(tmp_path / "test.db")
    service = AccountService(db, MemorySecretStore(), FakeTransport())
    account = service.add_account("9991234567", "secret", "Моя метка")
    assert account.id is not None

    result = service.refresh(account.id)
    assert result.snapshot is not None
    assert result.snapshot.balance == Decimal("42.50")
    assert result.account.status == AccountStatus.OK
    assert db.get_account(account.id).label == "Моя метка"

    updated, blocked = service.set_blocking(account.id, True)
    assert blocked is True
    assert updated.status == AccountStatus.OK
    assert db.get_account(account.id).label == "Моя метка"
    latest = db.latest_snapshot(account.id)
    assert latest is not None
    assert latest["blocked"] == 1


def test_offer_rules_inherit_by_name_reject_and_remember_unknown_decision(tmp_path):
    db = Database(tmp_path / "test.db")
    transport = FakeTransport()
    service = AccountService(db, MemorySecretStore(), transport)
    account = service.add_account("9991234567", "secret", "main")
    assert account.id is not None

    old = PersonalOffer("old-id", "Ненужный офер")
    db.sync_offers(account.id, [old])
    db.set_offer_note("old-id", "удалить")

    transport.offers = [
        PersonalOffer("new-id", "Ненужный офер"),
        PersonalOffer("keep-id", "Новый полезный офер"),
    ]

    def decide(offers):
        assert [offer.offer_id for offer in offers] == ["keep-id"]
        return {"keep-id": "оставить"}

    result = service.refresh(account.id, offer_decider=decide)
    assert result.snapshot is not None
    assert transport.rejected == ["new-id"]
    assert db.offer_note("new-id") == "удалить"
    assert db.offer_note("keep-id") == "оставить"
    assert "keep-id Новый полезный офер" in db.account_offer_summary(account.id)
    assert "new-id" not in db.account_offer_summary(account.id)


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
