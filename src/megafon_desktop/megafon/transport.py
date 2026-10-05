from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from megafon_desktop.domain.models import AccountSnapshot

CaptchaSolver = Callable[[bytes], str | None]


class MegafonTransport(Protocol):
    def refresh_snapshot(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> AccountSnapshot: ...

    def forget_session(self, account_id: int) -> None: ...
