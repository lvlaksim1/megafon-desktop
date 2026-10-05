from __future__ import annotations

from megafon_desktop.domain.models import AccountSnapshot
from .errors import ProtocolChanged


class BrowserCaptureTransport:
    """Playwright fallback boundary.

    MBplugin demonstrates the useful pattern: log in through the real cabinet, persist a dedicated
    browser profile and collect JSON responses for known URL fragments (balance, tariff,
    remainders, services, expenses). We deliberately keep that mechanism behind the same transport
    contract as the direct HTTP client. The native desktop UI never becomes a browser extension.
    """

    def refresh_snapshot(self, phone: str, password: str, account_id: int) -> AccountSnapshot:
        raise ProtocolChanged(
            "browser fallback is not implemented in v0.1; capture engine is the next milestone"
        )
