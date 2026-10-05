from __future__ import annotations

import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from megafon_desktop.domain.models import AccountSnapshot
from megafon_desktop.infra.paths import app_data_dir

from .errors import AuthenticationError, CaptchaRequired, ProtocolChanged


class ResponseCapture:
    """Small, MegaFon-specific JSON response collector.

    This intentionally keeps only endpoint payloads useful to the application. It mirrors the
    successful MBplugin pattern without importing its generic browser-controller framework.
    """

    KNOWN_FRAGMENTS = (
        "balance/api/main",
        "/api/auth/sessionCheck",
        "api/tariff/2019-3/current",
        "remainders/mini",
        "api/services/currentServices/list",
        "api/reports/expenses",
    )

    def __init__(self) -> None:
        self._responses: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def observe(self, url: str, status: int, payload: Any) -> bool:
        if status != 200 or not isinstance(payload, dict):
            return False
        matched = False
        for fragment in self.KNOWN_FRAGMENTS:
            if fragment in url:
                self._responses[fragment].append(payload)
                matched = True
        return matched

    def latest(self, fragment: str) -> dict[str, Any] | None:
        values = self._responses.get(fragment, [])
        return values[-1] if values else None

    def has(self, fragment: str) -> bool:
        return self.latest(fragment) is not None


class BrowserCaptureTransport:
    """Playwright fallback using the real consumer web cabinet.

    Chromium is an internal transport only; the product UI remains native Qt. Each account gets a
    persistent browser profile, so MegaFon's own current bootstrap/session flow can be reused across
    refreshes. JSON responses are captured from a small allow-list of known consumer endpoints.
    """

    LOGIN_URL = "https://lk.megafon.ru/"
    OPTIONS_URL = "https://lk.megafon.ru/options"
    EXPENSES_URL = "https://lk.megafon.ru/expenses"
    PAID_OPTIONS_URL = "https://lk.megafon.ru/options/connected/paid"

    def __init__(
        self,
        *,
        profiles_root: Path | None = None,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        self.profiles_root = profiles_root or (app_data_dir() / "browser_profiles")
        self.profiles_root.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.timeout_ms = timeout_ms

    def _profile_dir(self, account_id: int) -> Path:
        path = self.profiles_root / str(account_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _payload_value(payload: dict[str, Any] | None, *names: str) -> Any:
        if not payload:
            return None
        for name in names:
            if name in payload:
                return payload[name]
        data = payload.get("data")
        if isinstance(data, dict):
            for name in names:
                if name in data:
                    return data[name]
        return None

    def _login_if_needed(self, page: Any, phone: str, password: str) -> None:
        phone_input = page.locator("input.phone-input__field")
        login_visible = phone_input.count() > 0 and phone_input.first.is_visible()
        if not login_visible:
            return

        password_mode = page.get_by_role("button", name="По паролю")
        if password_mode.count() > 0:
            password_mode.first.click(timeout=3_000)

        phone_input.first.fill(phone)
        password_input = page.locator("input[type=password]")
        if password_input.count() == 0:
            raise AuthenticationError("password login form was not found")
        password_input.first.fill(password)

        submit = page.get_by_role("button", name="Войти", exact=True)
        if submit.count() == 0:
            raise AuthenticationError("login submit button was not found")
        submit.first.click()

    def _wait_for_balance_or_auth_gate(
        self, page: Any, capture: ResponseCapture, playwright_error: type[Exception]
    ) -> None:
        deadline = time.monotonic() + self.timeout_ms / 1000
        while time.monotonic() < deadline:
            if capture.has("balance/api/main"):
                return
            try:
                text = page.locator("body").inner_text(timeout=1_000).lower()
            except playwright_error:
                text = ""
            if "капч" in text or "код с картинки" in text:
                raise CaptchaRequired("MegaFon requested CAPTCHA in browser login")
            time.sleep(0.25)
        raise AuthenticationError("browser login did not reach an authenticated balance response")

    @staticmethod
    def _on_response(
        capture: ResponseCapture, response: Any, playwright_error: type[Exception]
    ) -> None:
        if not any(fragment in response.url for fragment in capture.KNOWN_FRAGMENTS):
            return
        try:
            capture.observe(response.url, response.status, response.json())
        except (ValueError, playwright_error):
            return

    def refresh_snapshot(self, phone: str, password: str, account_id: int) -> AccountSnapshot:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ProtocolChanged(
                'Playwright fallback is not installed; install with pip install -e ".[browser]"'
            ) from exc

        capture = ResponseCapture()
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=self._profile_dir(account_id),
                headless=self.headless,
            )
            context.on(
                "response",
                lambda response: self._on_response(capture, response, PlaywrightError),
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(self.timeout_ms)
            try:
                page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
                self._login_if_needed(page, phone, password)
                self._wait_for_balance_or_auth_gate(page, capture, PlaywrightError)

                for url in (self.OPTIONS_URL, self.EXPENSES_URL, self.PAID_OPTIONS_URL):
                    try:
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_timeout(1_000)
                    except PlaywrightError:
                        # Optional collector page failed; core captured account data stays valid.
                        continue
            finally:
                context.close()

        balance = capture.latest("balance/api/main")
        if balance is None:
            raise ProtocolChanged("browser flow produced no balance/api/main JSON")
        tariff = capture.latest("api/tariff/2019-3/current")

        from .http_transport import DirectHttpTransport

        tariff_name = self._payload_value(tariff, "name")
        return AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=DirectHttpTransport._decimal(self._payload_value(balance, "balance")),
            credit_limit=DirectHttpTransport._decimal(
                self._payload_value(balance, "balanceWithLimit")
            ),
            tariff_name=str(tariff_name) if tariff_name is not None else None,
        )
