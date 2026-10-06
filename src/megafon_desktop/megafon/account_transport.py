from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests

from megafon_desktop.domain.models import AccountRefresh, AccountSnapshot, PersonalOffer

from .errors import AuthenticationError, ProtocolChanged
from .http_transport import DirectHttpTransport
from .parsers import (
    current_option_id,
    latest_expense_event,
    offer_full_description,
    parse_available_options,
    parse_personal_offers,
)
from .transport import CaptchaSolver


class AccountHttpTransport(DirectHttpTransport):
    """Consumer B2C account transport layered on the verified v0.2.1 auth flow."""

    BLOCKING_CONNECT_OPTION_ID = "Q0L16QxY-nvN6dgAV04woA"
    BLOCKING_OPTION_NAME = "Блокировка номера"
    EXPENSE_SUFFIXES = (
        "",
        "/aggregated/calls",
        "/aggregated/services",
        "/aggregated/subscription",
        "/aggregated/sms",
    )
    OFFER_GAME_LIMIT = 100
    OFFER_GAME_STOP_MARKERS = (
        "pers.82",
        "что-то пошло не так",
        "error.00",
        "возникла ошибка",
    )

    def _authenticated_context(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None,
    ) -> tuple[requests.Session, str, dict[str, str]]:
        session = self._session()
        restored = self._restore_session(account_id, session)
        api_base, frontend_headers = self._bootstrap_frontend(session)

        state = self._session_check(session, api_base, frontend_headers)
        if self._authenticated_for_phone(state, phone):
            self._save_session(account_id, session)
            return session, api_base, frontend_headers

        if restored or state.get("authenticated") is True:
            if restored:
                self.forget_session(account_id)
            session = self._session()
            api_base, frontend_headers = self._bootstrap_frontend(session)
            state = self._session_check(session, api_base, frontend_headers)
            if self._authenticated_for_phone(state, phone):
                self._save_session(account_id, session)
                return session, api_base, frontend_headers

        login_payload = self.login(
            session,
            api_base,
            frontend_headers,
            phone,
            password,
            captcha_solver,
        )
        if not self._same_phone(phone, login_payload.get("phone")):
            raise AuthenticationError("MegaFon authenticated a different account than requested")

        self._save_session(account_id, session)
        state = self._session_check(session, api_base, frontend_headers)
        if not self._authenticated_for_phone(state, phone):
            raise AuthenticationError(
                "login succeeded but sessionCheck did not confirm this account"
            )
        self._save_session(account_id, session)
        return session, api_base, frontend_headers

    def _account_headers(
        self,
        frontend_headers: dict[str, str],
        *,
        session: requests.Session | None = None,
        content_type: str | None = None,
    ) -> dict[str, str]:
        headers = self._api_headers(frontend_headers, content_type=content_type)
        headers["X-Cabinet-Capabilities"] = "authentication-2020"
        if session is not None:
            csrf = self._cookie_value(session, "NEW-CSRF-TOKEN", "csrf-token")
            if csrf:
                headers["X-CSRF-TOKEN"] = csrf
        return headers

    @staticmethod
    def _json_value(response: Any, context: str) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise ProtocolChanged(f"expected JSON from {context}") from exc

    def _request_json(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
        path: str,
        *,
        params: dict[str, str] | None = None,
        optional: bool = False,
    ) -> Any | None:
        try:
            response = session.get(
                f"{api_base}{path}",
                params=params,
                headers=self._account_headers(frontend_headers),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            if optional:
                return None
            raise ProtocolChanged(f"request failed for {path}: {exc}") from exc

        if response.status_code in {401, 403}:
            raise AuthenticationError(
                f"authenticated session rejected by {path}: HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            if optional:
                return None
            raise ProtocolChanged(f"{path} failed: {self._response_error(response)}")
        try:
            return self._json_value(response, path)
        except ProtocolChanged:
            if optional:
                return None
            raise

    def _current_options(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
        *,
        optional: bool = False,
    ) -> Any | None:
        return self._request_json(
            session,
            api_base,
            frontend_headers,
            "/api/options/list/current",
            params={"showVASP": "true"},
            optional=optional,
        )

    def _read_expenses(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
    ) -> tuple[Any, ...]:
        today = datetime.now(UTC).astimezone().date()
        params = {
            "dateTo": today.strftime("%d.%m.%Y"),
            "dateFrom": (today - timedelta(days=88)).strftime("%d.%m.%Y"),
        }
        payloads: list[Any] = []
        for suffix in self.EXPENSE_SUFFIXES:
            value = self._request_json(
                session,
                api_base,
                frontend_headers,
                f"/api/reports/expenses{suffix}",
                params=params,
                optional=True,
            )
            if value is not None and "k1011" not in str(value):
                payloads.append(value)
        return tuple(payloads)

    def _prime_personal_offers(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
    ) -> None:
        """Mirror VBA's /personaloffer/game loop before reading available offers."""
        for _attempt in range(self.OFFER_GAME_LIMIT):
            try:
                response = session.get(
                    f"{api_base}/api/personaloffer/game",
                    headers=self._account_headers(frontend_headers),
                    timeout=self.timeout,
                )
            except requests.RequestException:
                return
            if response.status_code in {401, 403}:
                raise AuthenticationError("session rejected by /api/personaloffer/game")
            body = str(response.text or "").casefold()
            if response.status_code >= 400:
                return
            if "авторизуйтесь, чтобы продолжить" in body:
                raise AuthenticationError("MegaFon requested authorization for personal offers")
            if any(marker in body for marker in self.OFFER_GAME_STOP_MARKERS):
                return

    def _read_offers(
        self,
        session: requests.Session,
        api_base: str,
        frontend_headers: dict[str, str],
    ) -> list[PersonalOffer]:
        self._prime_personal_offers(session, api_base, frontend_headers)

        payload = self._request_json(
            session,
            api_base,
            frontend_headers,
            "/api/personaloffer/availableOffers",
            optional=True,
        )
        offers = parse_personal_offers(payload) if payload is not None else []
        for offer in offers:
            detail = self._request_json(
                session,
                api_base,
                frontend_headers,
                f"/api/personaloffer/v2/{quote(offer.offer_id, safe='')}",
                params={"channel": "PERSONAL_OFFERS"},
                optional=True,
            )
            if detail is not None:
                offer.full_description = offer_full_description(detail)
                offer.options = parse_available_options(detail)
        return offers

    def refresh_account(
        self,
        phone: str,
        password: str,
        account_id: int,
        captcha_solver: CaptchaSolver | None = None,
    ) -> AccountRefresh:
        session, api_base, frontend_headers = self._authenticated_context(
            phone,
            password,
            account_id,
            captcha_solver,
        )

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

        expense_payloads: list[dict[str, Any]] = []
        for payload in self._read_expenses(session, api_base, frontend_headers):
            if isinstance(payload, dict):
                expense_payloads.append(payload)
            elif isinstance(payload, list):
                expense_payloads.append({"items": payload})
        last_event = latest_expense_event(expense_payloads)

        current_options = self._current_options(
            session,
            api_base,
            frontend_headers,
            optional=True,
        )
        blocked = (
            None
            if current_options is None
            else current_option_id(current_options, self.BLOCKING_OPTION_NAME) is not None
        )
        offers = self._read_offers(session, api_base, frontend_headers)

        snapshot = AccountSnapshot(
            account_id=account_id,
            captured_at=datetime.now(UTC),
            balance=self._decimal(main.get("balance")),
            commercial_balance=self._decimal(commercial.get("balance")),
            credit_limit=self._decimal(main.get("balanceWithLimit", main.get("limit"))),
            last_action_amount=None if last_event is None else last_event.amount,
            last_action_name=None if last_event is None else last_event.definition,
            last_action_at=None if last_event is None else last_event.occurred_at,
            blocked=blocked,
        )
        self._save_session(account_id, session)
        return AccountRefresh(snapshot, offers)

    def reject_offers(
        self,
        phone: str,
        password: str,
        account_id: int,
        offer_ids: list[str],
        captcha_solver: CaptchaSolver | None = None,
    ) -> list[PersonalOffer]:
        session, api_base, frontend_headers = self._authenticated_context(
            phone,
            password,
            account_id,
            captcha_solver,
        )
        for offer_id in dict.fromkeys(offer_ids):
            path = f"/api/personaloffer/rejected/{quote(str(offer_id), safe='')}"
            try:
                response = session.post(
                    f"{api_base}{path}",
                    params={"channel": "PERSONAL_OFFERS"},
                    headers=self._account_headers(frontend_headers, session=session),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise ProtocolChanged(f"failed to reject personal offer {offer_id}: {exc}") from exc
            if response.status_code in {401, 403}:
                raise AuthenticationError("session rejected while rejecting personal offer")
            if response.status_code >= 400:
                raise ProtocolChanged(
                    f"reject personal offer {offer_id} failed: {self._response_error(response)}"
                )

        self._save_session(account_id, session)
        return self._read_offers(session, api_base, frontend_headers)

    def set_blocking(
        self,
        phone: str,
        password: str,
        account_id: int,
        enabled: bool,
        captcha_solver: CaptchaSolver | None = None,
    ) -> bool:
        session, api_base, frontend_headers = self._authenticated_context(
            phone,
            password,
            account_id,
            captcha_solver,
        )
        current = self._current_options(session, api_base, frontend_headers)
        current_id = current_option_id(current, self.BLOCKING_OPTION_NAME)

        if enabled and current_id is None:
            path = f"/api/options/{self.BLOCKING_CONNECT_OPTION_ID}"
            try:
                response = session.post(
                    f"{api_base}{path}",
                    data=None,
                    headers=self._account_headers(
                        frontend_headers,
                        session=session,
                        content_type="application/x-www-form-urlencoded;charset=UTF-8",
                    ),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise ProtocolChanged(f"failed to enable blocking: {exc}") from exc
            if response.status_code in {401, 403}:
                raise AuthenticationError("session rejected while enabling blocking")
            if response.status_code >= 400:
                raise ProtocolChanged(
                    f"enable blocking failed: {self._response_error(response)}"
                )
            self._save_session(account_id, session)
            return True

        if not enabled and current_id is not None:
            path = f"/api/options/{quote(current_id, safe='')}"
            try:
                response = session.delete(
                    f"{api_base}{path}",
                    headers=self._account_headers(
                        frontend_headers,
                        session=session,
                        content_type="application/json;charset=UTF-8",
                    ),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise ProtocolChanged(f"failed to disable blocking: {exc}") from exc
            if response.status_code in {401, 403}:
                raise AuthenticationError("session rejected while disabling blocking")
            if response.status_code >= 400:
                raise ProtocolChanged(
                    f"disable blocking failed: {self._response_error(response)}"
                )

        self._save_session(account_id, session)
        return enabled
