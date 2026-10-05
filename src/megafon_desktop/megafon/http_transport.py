from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import requests
from requests.cookies import create_cookie

from megafon_desktop.domain.models import AccountSnapshot
from megafon_desktop.infra.secret_store import SecretStore

from .errors import AccountBlocked, AuthenticationError, CaptchaRequired, ProtocolChanged
from .transport import CaptchaSolver


class DirectHttpTransport:
    """Direct consumer-LK transport with persistent per-account HTTP authorization."""

    API = "https://api.megafon.ru/mlk"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    )
    SESSION_FORMAT = 1
    MAX_CAPTCHA_ATTEMPTS = 5

    def __init__(self, timeout: float = 20.0, secrets: SecretStore | None = None) -> None:
        self.timeout = timeout
        self.secrets = secrets

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
    def _session_key(account_id: int) -> str:
        return f"account-{account_id}-http-session"

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError) as exc:
            raise ProtocolChanged(f"unexpected decimal value: {value!r}") from exc

    @staticmethod
    def _cookie_payload(session: requests.Session) -> list[dict[str, Any]]:
        return [
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
            }
            for cookie in session.cookies
        ]

    def _save_session(self, account_id: int, session: requests.Session) -> None:
        if self.secrets is None:
            return
        payload = {
            "version": self.SESSION_FORMAT,
            "cookies": self._cookie_payload(session),
        }
        self.secrets.set(self._session_key(account_id), json.dumps(payload, separators=(",", ":")))

    def _restore_session(self, account_id: int, session: requests.Session) -> bool:
        if self.secrets is None:
            return False
        raw = self.secrets.get(self._session_key(account_id))
        if not raw:
            return False
        try:
            payload = json.loads(raw)
            if payload.get("version") != self.SESSION_FORMAT:
                return False
            cookies = payload.get("cookies")
            if not isinstance(cookies, list):
                return False
            for item in cookies:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                value = item.get("value")
                if not isinstance(name, str) or not isinstance(value, str):
                    continue
                session.cookies.set_cookie(
                    create_cookie(
                        name=name,
                        value=value,
                        domain=str(item.get("domain") or ""),
                        path=str(item.get("path") or "/"),
                        secure=bool(item.get("secure")),
                        expires=item.get("expires"),
                    )
                )
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
        return len(session.cookies) > 0

    def forget_session(self, account_id: int) -> None:
        if self.secrets is not None:
            self.secrets.delete(self._session_key(account_id))

    @staticmethod
    def _csrf_token(session: requests.Session) -> str | None:
        for name in ("NEW-CSRF-TOKEN", "csrf-token"):
            value = session.cookies.get(name)
            if value:
                return value
        return None

    def _login_headers(self, session: requests.Session) -> dict[str, str]:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://lk.megafon.ru",
            "Referer": "https://lk.megafon.ru/login",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        csrf = self._csrf_token(session)
        if csrf:
            headers["X-CSRF-TOKEN"] = csrf
        return headers

    @staticmethod
    def _is_captcha_response(response: requests.Response) -> bool:
        body = response.text.lower()
        if "код с картинки" in body or "captcha" in body or "капч" in body:
            return True
        try:
            payload = response.json()
        except ValueError:
            return False
        return isinstance(payload, dict) and payload.get("code") == "a211"

    def _fetch_captcha(self, session: requests.Session) -> bytes:
        try:
            response = session.get(
                f"{self.API}/api/captcha/next",
                headers={
                    "Origin": "https://lk.megafon.ru",
                    "Referer": "https://lk.megafon.ru/login",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"failed to load CAPTCHA: {exc}") from exc
        if response.status_code >= 400:
            raise ProtocolChanged(f"failed to load CAPTCHA: HTTP {response.status_code}")
        if not response.content:
            raise ProtocolChanged("MegaFon returned an empty CAPTCHA image")
        return response.content

    def login(
        self,
        session: requests.Session,
        phone: str,
        password: str,
        captcha_solver: CaptchaSolver | None = None,
    ) -> None:
        captcha: str | None = None

        for _attempt in range(self.MAX_CAPTCHA_ATTEMPTS):
            data = {"password": password, "login": phone}
            if captcha:
                data["captcha"] = captcha

            try:
                response = session.post(
                    f"{self.API}/api/login",
                    data=data,
                    headers=self._login_headers(session),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise ProtocolChanged(f"login request failed: {exc}") from exc

            body = response.text.lower()
            if "аккаунт заблокирован" in body:
                raise AccountBlocked("account is blocked / password change may be required")

            if self._is_captcha_response(response):
                if captcha_solver is None:
                    raise CaptchaRequired("MegaFon requested CAPTCHA")
                image = self._fetch_captcha(session)
                answer = captcha_solver(image)
                if answer is None or not answer.strip():
                    raise CaptchaRequired("CAPTCHA entry was cancelled")
                captcha = answer.strip()
                continue

            if response.status_code >= 400:
                raise AuthenticationError(f"login failed: HTTP {response.status_code}")

            authenticated = False
            try:
                payload = response.json()
                authenticated = isinstance(payload, dict) and payload.get("authenticated") is True
            except ValueError:
                pass

            cookie_names = {cookie.name.upper() for cookie in session.cookies}
            recognizable_cookie = bool(
                {
                    "USER-GUID",
                    "JSESSIONID",
                    "X-CABINET-ACCESS-TOKEN",
                    "X-CABINET-ID-TOKEN",
                }
                & cookie_names
            )
            if not authenticated and not recognizable_cookie:
                raise AuthenticationError(
                    "login response did not establish a recognizable session"
                )
            return

        raise CaptchaRequired("CAPTCHA was not accepted after several attempts")

    def _get_json(self, session: requests.Session, path: str) -> dict[str, Any]:
        try:
            response = session.get(
                f"{self.API}{path}",
                headers={"X-Cabinet-Capabilities": "authentication-2020"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"request failed for {path}: {exc}") from exc

        if response.status_code in {401, 403}:
            raise AuthenticationError(f"session rejected: HTTP {response.status_code}")
        if response.status_code >= 400:
            raise ProtocolChanged(f"{path} failed: HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProtocolChanged(f"expected JSON from {path}") from exc
        if not isinstance(payload, dict):
            raise ProtocolChanged(f"expected object from {path}")
        return payload

    def _read_snapshot(
        self,
        session: requests.Session,
        account_id: int,
    ) -> AccountSnapshot:
        main = self._get_json(session, "/api/main/balance")
        commercial = self._get_json(session, "/api/balance/commercial")

        return AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=self._decimal(main.get("balance")),
            commercial_balance=self._decimal(commercial.get("balance")),
            credit_limit=self._decimal(main.get("balanceWithLimit")),
        )

    def refresh_snapshot(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> AccountSnapshot:
        session = self._session()
        restored = self._restore_session(account_id, session)

        if restored:
            try:
                snapshot = self._read_snapshot(session, account_id)
                self._save_session(account_id, session)
                return snapshot
            except AuthenticationError:
                self.forget_session(account_id)
                session = self._session()

        self.login(session, phone, password, captcha_solver)
        snapshot = self._read_snapshot(session, account_id)
        self._save_session(account_id, session)
        return snapshot
