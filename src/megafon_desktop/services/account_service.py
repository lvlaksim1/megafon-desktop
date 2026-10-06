from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from megafon_desktop.domain.models import Account, AccountSnapshot, AccountStatus, PersonalOffer
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import SecretStore
from megafon_desktop.megafon.errors import (
    AccountBlocked,
    AuthenticationError,
    CaptchaRequired,
    MegafonError,
)
from megafon_desktop.megafon.transport import CaptchaSolver, MegafonTransport

OfferDecisionSolver = Callable[[list[PersonalOffer]], dict[str, str] | None]


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

    def delete_account(self, account_id: int) -> None:
        self.db.get_account(account_id)
        self.secrets.delete(self._secret_key(account_id))
        self.transport.forget_session(account_id)
        self.db.delete_account(account_id)

    def list_accounts(self) -> list[Account]:
        return self.db.list_accounts()

    def set_account_order(self, account_ids: list[int]) -> None:
        self.db.set_account_order(account_ids)

    def set_account_label(self, account_id: int, label: str) -> None:
        self.db.set_account_label(account_id, label)

    def offer_rows(self) -> list[dict[str, Any]]:
        return self.db.offer_rows()

    def set_offer_note(self, offer_id: str, note: str) -> None:
        self.db.set_offer_note(offer_id, note)

    def available_option_rows(self) -> list[dict[str, Any]]:
        return self.db.available_option_rows()

    def _missing_password(self, account_id: int) -> RefreshResult:
        self.db.update_account_state(
            account_id,
            status=AccountStatus.AUTH_REQUIRED,
            last_error="password is missing",
        )
        return RefreshResult(self.db.get_account(account_id), None)

    def _record_error(self, account_id: int, exc: MegafonError) -> Account:
        if isinstance(exc, CaptchaRequired):
            status = AccountStatus.CAPTCHA
        elif isinstance(exc, AccountBlocked):
            status = AccountStatus.BLOCKED
        elif isinstance(exc, AuthenticationError):
            status = AccountStatus.AUTH_REQUIRED
        else:
            status = AccountStatus.ERROR
        self.db.update_account_state(account_id, status=status, last_error=str(exc))
        return self.db.get_account(account_id)

    def _process_offers(
        self,
        account: Account,
        password: str,
        offers: list[PersonalOffer],
        captcha_solver: CaptchaSolver | None,
        offer_decider: OfferDecisionSolver | None,
    ) -> list[PersonalOffer]:
        assert account.id is not None
        sent_rejections: set[str] = set()

        for _cycle in range(12):
            self.db.sync_offers(account.id, offers)

            reject_ids = [
                offer.offer_id
                for offer in offers
                if self.db.offer_note(offer.offer_id) == "удалить"
                and offer.offer_id not in sent_rejections
            ]
            if reject_ids:
                sent_rejections.update(reject_ids)
                offers = self.transport.reject_offers(
                    account.phone,
                    password,
                    account.id,
                    reject_ids,
                    captcha_solver,
                )
                continue

            unknown = [
                offer for offer in offers if self.db.offer_note(offer.offer_id) == ""
            ]
            if unknown and offer_decider is not None:
                decisions = offer_decider(unknown)
                if decisions:
                    changed = False
                    for offer in unknown:
                        decision = str(decisions.get(offer.offer_id, "")).strip().lower()
                        if decision in {"оставить", "удалить"}:
                            self.db.set_offer_note(offer.offer_id, decision)
                            changed = True
                    if changed:
                        continue
            break

        self.db.sync_offers(account.id, offers)
        return offers

    def refresh(
        self,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
        offer_decider: OfferDecisionSolver | None = None,
    ) -> RefreshResult:
        account = self.db.get_account(account_id)
        password = self.secrets.get(self._secret_key(account_id))
        if not password:
            return self._missing_password(account_id)

        try:
            refreshed = self.transport.refresh_account(
                account.phone,
                password,
                account_id,
                captcha_solver,
            )
            refreshed.offers = self._process_offers(
                account,
                password,
                refreshed.offers,
                captcha_solver,
                offer_decider,
            )
        except MegafonError as exc:
            return RefreshResult(self._record_error(account_id, exc), None)

        refreshed.snapshot.offers_summary = self.db.account_offer_summary(account_id)
        self.db.add_snapshot(refreshed.snapshot)
        self.db.update_account_state(account_id, status=AccountStatus.OK)
        return RefreshResult(self.db.get_account(account_id), refreshed.snapshot)

    def set_blocking(
        self,
        account_id: int,
        enabled: bool,
        captcha_solver: CaptchaSolver | None = None,
    ) -> tuple[Account, bool | None]:
        account = self.db.get_account(account_id)
        password = self.secrets.get(self._secret_key(account_id))
        if not password:
            result = self._missing_password(account_id)
            return result.account, None

        try:
            blocked = self.transport.set_blocking(
                account.phone,
                password,
                account_id,
                enabled,
                captcha_solver,
            )
        except MegafonError as exc:
            return self._record_error(account_id, exc), None

        self.db.set_latest_blocked(account_id, blocked)
        self.db.update_account_state(account_id, status=AccountStatus.OK)
        return self.db.get_account(account_id), blocked
