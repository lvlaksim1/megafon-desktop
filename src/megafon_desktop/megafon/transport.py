from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from megafon_desktop.domain.models import AccountRefresh, PersonalOffer

CaptchaSolver = Callable[[bytes], str | None]


class MegafonTransport(Protocol):
    def refresh_account(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> AccountRefresh: ...

    def reject_offers(
        self,
        phone: str,
        password: str,
        account_id: int,
        offer_ids: list[str],
        captcha_solver: CaptchaSolver | None = None,
    ) -> list[PersonalOffer]: ...

    def set_blocking(
        self,
        phone: str,
        password: str,
        account_id: int,
        enabled: bool,
        captcha_solver: CaptchaSolver | None = None,
    ) -> bool: ...

    def forget_session(self, account_id: int) -> None: ...
