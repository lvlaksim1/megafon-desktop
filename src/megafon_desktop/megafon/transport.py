from __future__ import annotations

from typing import Protocol

from megafon_desktop.domain.models import AccountSnapshot


class MegafonTransport(Protocol):
    def refresh_snapshot(self, phone: str, password: str, account_id: int) -> AccountSnapshot: ...
