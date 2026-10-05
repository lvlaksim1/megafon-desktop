from __future__ import annotations

import json
import re
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
    """HTTP-only transport for the consumer MegaFon web cabinet."""

    WEB = "https://lk.megafon.ru"
    LOGIN_URL = f"{WEB}/login?channel=PERSONAL_OFFERS"
    DEFAULT_API = "https://api.megafon.ru/mlk"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    )
    SESSION_FORMAT = 1
    MAX_CAPTCHA_ATTEMPTS = 5
    CABINET_HEADER_NAMES = (
        "X-Cabinet-Id-Param",
        "X-Cabinet-Check-Info",
        "X-Cabinet-Validation-Param",
    )

    def __init__(self, timeout: float = 20.0, secrets: SecretStore | None = None) -> None:
        self.timeout = timeout
        self.secrets = secrets

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Origin": self.WEB,
                "User-Agent": self.USER_AGENT,
                "X-App-Type": "react_lk",
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
    def _phone_key(phone: str) -> str:
        digits = "".join(ch for ch in str(phone) if ch.isdigit())
        if len(digits) == 11 and digits[0] in {"7", "8"}:
            return digits[-10:]
        return digits

    @classmethod
    def _same_phone(cls, expected: str, actual: str | None) -> bool:
        if actual is None:
            return False
        return cls._phone_key(expected) == cls._phone_key(actual)

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
        self.secrets.set(
            self._session_key(account_id),
            json.dumps(payload, separators=(",", ":")),
        )

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
    def _cookie_value(session: requests.Session, *names: str) -> str | None:
        wanted = {name.lower() for name in names}
        for cookie in reversed(list(session.cookies)):
            if cookie.name.lower() in wanted and cookie.value:
                return cookie.value
        return None

    @staticmethod
    def _json_object(response: Any, context: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProtocolChanged(f"expected JSON from {context}") from exc
        if not isinstance(payload, dict):
            raise ProtocolChanged(f"expected object from {context}")
        return payload

    def _bootstrap_frontend(
        self,
        session: requests.Session,
    ) -> tuple[str, dict[str, str]]:
        try:
            landing = session.get(
                self.LOGIN_URL,
                headers={"Accept": "text/html,application/xhtml+xml"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"failed to open consumer login page: {exc}") from exc
        if landing.status_code >= 400:
            raise ProtocolChanged(
                f"consumer login page failed: HTTP {landing.status_code}"
            )

        api_base = self.DEFAULT_API
        try:
            settings = session.get(
                f"{self.WEB}/settings.json",
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
            if settings.status_code == 200:
                payload = settings.json()
                candidate = payload.get("api_url") if isinstance(payload, dict) else None
                if (
                    isinstance(candidate, str)
                    and candidate.startswith("https://api.megafon.ru/")
                ):
                    api_base = candidate.rstrip("/")
        except (requests.RequestException, ValueError):
            pass

        app_path: str | None = None
        try:
            service_worker = session.get(
                f"{self.WEB}/public/rwlk/service-worker.js",
                headers={"Accept": "text/javascript,application/javascript,*/*"},
                timeout=self.timeout,
            )
            if service_worker.status_code == 200:
                match = re.search(
                    r"(/public/rwlk/app\.[^\"'\s]+\.js)",
                    service_worker.text,
                    flags=re.IGNORECASE,
                )
                if match:
                    app_path = match.group(1)
        except requests.RequestException:
            pass

        if app_path is None:
            match = re.search(
                r"""src=["'](?P<path>/public/rwlk/app\.[^"'?]+\.js)["']""",
                landing.text,
                flags=re.IGNORECASE,
            )
            if match:
                app_path = match.group("path")

        if app_path is None:
            raise ProtocolChanged("current MegaFon app.<hash>.js was not found")

        try:
            app_response = session.get(
                f"{self.WEB}{app_path}",
                headers={"Accept": "text/javascript,application/javascript,*/*"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"failed to load current MegaFon frontend: {exc}") from exc
        if app_response.status_code >= 400:
            raise ProtocolChanged(
                f"current MegaFon frontend failed: HTTP {app_response.status_code}"
            )

        headers: dict[str, str] = {}
        for name in self.CABINET_HEADER_NAMES:
            match = re.search(
                rf"""["']?{re.escape(name)}["']?\s*:\s*["']([^"']+)["']""",
                app_response.text,
                flags=re.IGNORECASE,
            )
            if match is None:
                raise ProtocolChanged(f"current frontend does not expose {name}")
            headers[name] = match.group(1)

        return api_base, headers

    def _api_headers(
        self,
        frontend_headers: dict[str, str],
        *,
        content_type: str | None = None,
        referer: str | None = None,
    ) -> dict[str, str]:
        headers = {
            **frontend_headers,
            "Origin": self.WEB,
            "X-App-Type": "react_lk",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if referer:
            headers["Referer"] = referer
        return headers

    def _login_headers(
        self,
        session: requests.Session,
        frontend_headers: dict[str, str],
    ) -> dict[str, str]:
        headers = self._api_headers(
            frontend_headers,
            content_type="application/x-www-form-urlencoded; charset=UTF-8",
            referer=self.LOGIN_URL,
        )
        headers["Cache-Control"] = "no-cache"
        headers["Pragma"] = "no-cache"
        headers["X-Cabinet-Key-Operation-Id"] = "manual-auth"
        csrf = self._cookie_value(session, "NEW-CSRF-TOKEN", "csrf-token")
        if csrf:
            headers["X-CSRF-TOKEN"] = csrf
        return headers

    @staticmethod
    def _is_captcha_response(response: Any) -> bool:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("code") == "a211":
            return True
        body = str(getattr(response, "text", "")).lower()
        return "код с картинки" in body or "captcha" in body or "капч" in body

    @staticmethod
    def _response_error(response: Any) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            code = payload.get("code")
            message = payload.get("message")
            if code and message:
                return f"{code}: {message}"
            if message:
                return str(message)
        return f"HTTP {response.status_code}"

    def _fetch_captcha(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
    ) -> bytes:
        try:
            response = session.get(
                f"{api_base}/api/captcha/next",
                headers=self._api_headers(
                    frontend_headers,
                    referer=self.LOGIN_URL,
                ),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"failed to load CAPTCHA: {exc}") from exc
        if response.status_code >= 400:
            raise ProtocolChanged(
                f"failed to load CAPTCHA: {self._response_error(response)}"
            )
        if not response.content:
            raise ProtocolChanged("MegaFon returned an empty CAPTCHA image")
        return response.content

    def _session_check(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
    ) -> dict[str, Any]:
        try:
            response = session.get(
                f"{api_base}/api/auth/sessionCheck",
                headers=self._api_headers(
                    frontend_headers,
                    content_type="application/x-www-form-urlencoded;charset=UTF-8",
                ),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"sessionCheck failed: {exc}") from exc

        if response.status_code in {401, 403}:
            return {"authenticated": False}
        if response.status_code >= 400:
            raise ProtocolChanged(
                f"sessionCheck failed: {self._response_error(response)}"
            )
        return self._json_object(response, "/api/auth/sessionCheck")

    def login(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
        phone: str,
        password: str,
        captcha_solver: CaptchaSolver | None = None,
    ) -> dict[str, Any]:
        captcha: str | None = None

        for _attempt in range(self.MAX_CAPTCHA_ATTEMPTS):
            data = {"password": password, "login": phone}
            if captcha:
                data["captcha"] = captcha

            try:
                response = session.post(
                    f"{api_base}/api/login",
                    data=data,
                    headers=self._login_headers(session, frontend_headers),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise ProtocolChanged(f"login request failed: {exc}") from exc

            error_text = self._response_error(response)
            if "a216" in error_text.lower() or "аккаунт заблокирован" in error_text.lower():
                raise AccountBlocked(error_text)

            if self._is_captcha_response(response):
                if captcha_solver is None:
                    raise CaptchaRequired("MegaFon requested CAPTCHA")
                image = self._fetch_captcha(session, api_base, frontend_headers)
                answer = captcha_solver(image)
                if answer is None or not answer.strip():
                    raise CaptchaRequired("CAPTCHA entry was cancelled")
                captcha = answer.strip()
                continue

            if response.status_code >= 400:
                raise AuthenticationError(f"login failed: {error_text}")

            payload = self._json_object(response, "/api/login")
            if payload.get("code"):
                raise AuthenticationError(
                    f"login failed: {payload.get('code')}: {payload.get('message', '')}".rstrip()
                )
            if payload.get("authenticated") is not True:
                raise AuthenticationError(
                    "login response did not confirm authenticated=true"
                )
            return payload

        raise CaptchaRequired("CAPTCHA was not accepted after several attempts")

    def _get_json(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
        path: str,
    ) -> dict[str, Any]:
        try:
            response = session.get(
                f"{api_base}{path}",
                headers=self._api_headers(frontend_headers),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProtocolChanged(f"request failed for {path}: {exc}") from exc

        if response.status_code in {401, 403}:
            raise AuthenticationError(
                f"authenticated session rejected by {path}: HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise ProtocolChanged(f"{path} failed: {self._response_error(response)}")
        return self._json_object(response, path)

    def _read_snapshot(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
        account_id: int,
    ) -> AccountSnapshot:
        main = self._get_json(
            session,
            api_base,
            frontend_headers,
            "/api/main/balance",
        )
        commercial = self._get_json(
            session,
            api_base,
            frontend_headers,
            "/api/balance/commercial",
        )

        return AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=self._decimal(main.get("balance")),
            commercial_balance=self._decimal(commercial.get("balance")),
            credit_limit=self._decimal(
                main.get("balanceWithLimit", main.get("limit"))
            ),
        )

    def _authenticated_for_phone(
        self,
        state: dict[str, Any],
        phone: str,
    ) -> bool:
        return state.get("authenticated") is True and self._same_phone(
            phone,
            state.get("phone"),
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
        api_base, frontend_headers = self._bootstrap_frontend(session)

        if restored:
            state = self._session_check(session, api_base, frontend_headers)
            if self._authenticated_for_phone(state, phone):
                self._save_session(account_id, session)
                snapshot = self._read_snapshot(
                    session,
                    api_base,
                    frontend_headers,
                    account_id,
                )
                self._save_session(account_id, session)
                return snapshot

            self.forget_session(account_id)
            session = self._session()
            api_base, frontend_headers = self._bootstrap_frontend(session)

        login_payload = self.login(
            session,
            api_base,
            frontend_headers,
            phone,
            password,
            captcha_solver,
        )

        if not self._same_phone(phone, login_payload.get("phone")):
            raise AuthenticationError(
                "MegaFon authenticated a different account than requested"
            )

        # Persist immediately. A later data endpoint failure must not discard
        # an already successful password/CAPTCHA authorization.
        self._save_session(account_id, session)

        state = self._session_check(session, api_base, frontend_headers)
        if not self._authenticated_for_phone(state, phone):
            raise AuthenticationError(
                "login succeeded but sessionCheck did not confirm this account"
            )
        self._save_session(account_id, session)

        snapshot = self._read_snapshot(
            session,
            api_base,
            frontend_headers,
            account_id,
        )
        self._save_session(account_id, session)
        return snapshot
