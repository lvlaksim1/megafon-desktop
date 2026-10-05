from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from megafon_desktop.domain.models import AccountSnapshot
from .errors import AccountBlocked, AuthenticationError, CaptchaRequired, ProtocolChanged


class DirectHttpTransport:
    """Direct consumer-LK transport reconstructed from the owner's working VBA."""

    API = "https://api.megafon.ru/mlk"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru,en;q=0.9",
                "User-Agent": self.USER_AGENT,
                "x-app-type": "react_lk",
            }
        )
        return session

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError) as exc:
            raise ProtocolChanged(f"unexpected decimal value: {value!r}") from exc

    def login(self, session: requests.Session, phone: str, password: str) -> None:
        response = session.post(
            f"{self.API}/login",
            data={"password": password, "login": phone},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://lk.megafon.ru",
                "Referer": "https://lk.megafon.ru/login",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            timeout=self.timeout,
        )

        body = response.text.lower()
        if "аккаунт заблокирован" in body:
            raise AccountBlocked("account is blocked / password change may be required")
        if "код с картинки" in body or "captcha" in body or "капч" in body:
            raise CaptchaRequired("MegaFon requested CAPTCHA")
        if response.status_code >= 400:
            raise AuthenticationError(f"login failed: HTTP {response.status_code}")

        cookie_names = {cookie.name.upper() for cookie in session.cookies}
        response_headers = {name.upper(): value for name, value in response.headers.items()}
        if "USER-GUID" not in cookie_names and "USER-GUID" not in " ".join(response_headers):
            if "JSESSIONID" not in cookie_names:
                raise AuthenticationError("login response did not establish a recognizable session")

    def _get_json(self, session: requests.Session, path: str) -> dict[str, Any]:
        response = session.get(
            f"{self.API}{path}",
            headers={"X-Cabinet-Capabilities": "authentication-2020"},
            timeout=self.timeout,
        )
        if response.status_code in {401, 403}:
            raise AuthenticationError(f"session rejected: HTTP {response.status_code}")
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProtocolChanged(f"expected JSON from {path}") from exc
        if not isinstance(payload, dict):
            raise ProtocolChanged(f"expected object from {path}")
        return payload

    def refresh_snapshot(self, phone: str, password: str, account_id: int) -> AccountSnapshot:
        session = self._session()
        self.login(session, phone, password)

        main = self._get_json(session, "/api/main/balance")
        commercial = self._get_json(session, "/api/balance/commercial")

        return AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=self._decimal(main.get("balance")),
            commercial_balance=self._decimal(commercial.get("balance")),
            credit_limit=self._decimal(main.get("balanceWithLimit")),
        )
