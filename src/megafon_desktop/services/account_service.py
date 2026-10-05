from __future__ import annotations

from dataclasses import dataclass

from megafon_desktop.domain.models import Account, AccountSnapshot, AccountStatus
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import SecretStore
from megafon_desktop.megafon.errors import (
    AccountBlocked,
    AuthenticationError,
    CaptchaRequired,
    MegafonError,
)
from megafon_desktop.megafon.transport import CaptchaSolver, MegafonTransport


@dataclass(slots=True)
class RefreshResult:
    account: Account
    snapshot: AccountSnapshot | None


class AccountService:
    def __init__(self, db: Database, secrets: SecretStore, transport: MegafonTransport) -> None:
        self.db = db
        self.secrets = secrets
        self.transport = transport

    @staticmethod
    def _secret_key(account_id: int) -> str:
        return f"account-{account_id}-password"

    def add_account(self, phone: str, password: str, label: str = "") -> Account:
        account = self.db.add_account(phone, label)
        assert account.id is not None
        try:
            self.secrets.set(self._secret_key(account.id), password)
        except Exception:
            self.db.delete_account(account.id)
            raise
        return account

    def list_accounts(self) -> list[Account]:
        return self.db.list_accounts()

    def refresh(
        self,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> RefreshResult:
        account = self.db.get_account(account_id)
        password = self.secrets.get(self._secret_key(account_id))
        if not password:
            self.db.update_account_state(
                account_id,
                status=AccountStatus.AUTH_REQUIRED,
                last_error="password is missing",
            )
            return RefreshResult(self.db.get_account(account_id), None)

        try:
            snapshot = self.transport.refresh_snapshot(
                account.phone,
                password,
                account_id,
                captcha_solver,
            )
        except CaptchaRequired as exc:
            self.db.update_account_state(
                account_id,
                status=AccountStatus.CAPTCHA,
                last_error=str(exc),
            )
            return RefreshResult(self.db.get_account(account_id), None)
        except AccountBlocked as exc:
            self.db.update_account_state(
                account_id,
                status=AccountStatus.BLOCKED,
                last_error=str(exc),
            )
            return RefreshResult(self.db.get_account(account_id), None)
        except AuthenticationError as exc:
            self.db.update_account_state(
                account_id,
                status=AccountStatus.AUTH_REQUIRED,
                last_error=str(exc),
            )
            return RefreshResult(self.db.get_account(account_id), None)
        except MegafonError as exc:
            self.db.update_account_state(
                account_id,
                status=AccountStatus.ERROR,
                last_error=str(exc),
            )
            return RefreshResult(self.db.get_account(account_id), None)

        self.db.add_snapshot(snapshot)
        self.db.update_account_state(account_id, status=AccountStatus.OK)
        return RefreshResult(self.db.get_account(account_id), snapshot)
