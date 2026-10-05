from decimal import Decimal

import pytest
import requests

from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.megafon.errors import ProtocolChanged
from megafon_desktop.megafon.http_transport import DirectHttpTransport


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        *,
        payload: dict | None = None,
        text: str = "",
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.content = content

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FlowSession:
    def __init__(self, *, fail_balance: bool = False) -> None:
        self.headers: dict[str, str] = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        self.posts: list[dict[str, str]] = []
        self.session_checks = 0
        self.fail_balance = fail_balance

    def get(self, url, *, headers, timeout):
        del timeout
        self.calls.append(("GET", url, dict(headers)))

        if url.endswith("/login?channel=PERSONAL_OFFERS"):
            return FakeResponse(
                200,
                text='<script src="/public/rwlk/app.fresh.js"></script>',
            )
        if url.endswith("/settings.json"):
            return FakeResponse(
                200,
                payload={"api_url": "https://api.megafon.ru/mlk"},
            )
        if url.endswith("/public/rwlk/service-worker.js"):
            return FakeResponse(
                200,
                text="{'revision':null,'url':'/public/rwlk/app.fresh.js'}",
            )
        if url.endswith("/public/rwlk/app.fresh.js"):
            return FakeResponse(
                200,
                text=(
                    '"X-Cabinet-Id-Param":"id-param",'
                    '"X-Cabinet-Check-Info":"check-info",'
                    '"X-Cabinet-Validation-Param":"validation-param"'
                ),
            )
        if url.endswith("/api/auth/sessionCheck"):
            self.session_checks += 1
            if self.session_checks == 1:
                return FakeResponse(200, payload={"authenticated": False})
            return FakeResponse(
                200,
                payload={"authenticated": True, "phone": "9319979968"},
            )
        if url.endswith("/api/captcha/next"):
            return FakeResponse(200, content=b"jpeg-image")
        if url.endswith("/api/main/balance"):
            if self.fail_balance:
                return FakeResponse(
                    500,
                    payload={"message": "balance temporarily unavailable"},
                )
            return FakeResponse(
                200,
                payload={"balance": 42.5, "balanceWithLimit": 100},
            )
        if url.endswith("/api/balance/commercial"):
            return FakeResponse(200, payload={"balance": 40})
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url, *, data, headers, timeout):
        del timeout
        self.calls.append(("POST", url, dict(headers)))
        self.posts.append(dict(data))
        if len(self.posts) == 1:
            return FakeResponse(
                401,
                payload={"code": "a211", "message": "Введите код с картинки"},
                text='{"code":"a211","message":"Введите код с картинки"}',
            )

        self.cookies.set(
            "X-Cabinet-Access-Token",
            "access-token",
            domain=".megafon.ru",
            path="/",
        )
        self.cookies.set(
            "X-Cabinet-Refresh-Token",
            "refresh-token",
            domain=".megafon.ru",
            path="/",
        )
        return FakeResponse(
            200,
            payload={"authenticated": True, "phone": "9319979968"},
        )


class RestoredSession(FlowSession):
    def __init__(self) -> None:
        super().__init__()
        self.session_checks = 1

    def post(self, url, *, data, headers, timeout):
        raise AssertionError(f"login must not run for restored session: {url}")


def _assert_cabinet_headers(calls):
    api_calls = [
        call
        for call in calls
        if call[1].startswith("https://api.megafon.ru/mlk/")
    ]
    assert api_calls
    for _method, _url, headers in api_calls:
        assert headers["X-Cabinet-Id-Param"] == "id-param"
        assert headers["X-Cabinet-Check-Info"] == "check-info"
        assert headers["X-Cabinet-Validation-Param"] == "validation-param"


def test_decimal_parser():
    assert DirectHttpTransport._decimal("12,34") == Decimal("12.34")
    assert DirectHttpTransport._decimal(5) == Decimal(5)
    assert DirectHttpTransport._decimal(None) is None


def test_full_b2c_captcha_flow_uses_frontend_headers_and_same_session():
    secrets = MemorySecretStore()
    transport = DirectHttpTransport(secrets=secrets)
    session = FlowSession()
    transport._session = lambda: session
    seen: list[bytes] = []

    snapshot = transport.refresh_snapshot(
        "79319979968",
        "secret",
        7,
        lambda image: seen.append(image) or "29p16m",
    )

    assert snapshot.balance == Decimal("42.5")
    assert seen == [b"jpeg-image"]
    assert session.posts == [
        {"password": "secret", "login": "79319979968"},
        {
            "password": "secret",
            "login": "79319979968",
            "captcha": "29p16m",
        },
    ]
    _assert_cabinet_headers(session.calls)

    login_headers = [
        headers
        for method, url, headers in session.calls
        if method == "POST" and url.endswith("/api/login")
    ]
    assert all(
        headers["X-Cabinet-Key-Operation-Id"] == "manual-auth"
        for headers in login_headers
    )
    assert secrets.get("account-7-http-session") is not None


def test_successful_login_is_persisted_before_data_failure():
    secrets = MemorySecretStore()
    transport = DirectHttpTransport(secrets=secrets)
    session = FlowSession(fail_balance=True)
    transport._session = lambda: session

    with pytest.raises(ProtocolChanged):
        transport.refresh_snapshot(
            "79319979968",
            "secret",
            9,
            lambda _image: "29p16m",
        )

    saved = secrets.get("account-9-http-session")
    assert saved is not None
    assert "X-Cabinet-Refresh-Token" in saved


def test_restored_session_is_checked_before_password_login():
    secrets = MemorySecretStore()
    seed = DirectHttpTransport(secrets=secrets)
    original = requests.Session()
    original.cookies.set(
        "X-Cabinet-Access-Token",
        "access-token",
        domain=".megafon.ru",
        path="/",
    )
    seed._save_session(4, original)

    transport = DirectHttpTransport(secrets=secrets)
    session = RestoredSession()
    transport._session = lambda: session

    snapshot = transport.refresh_snapshot("79319979968", "secret", 4)

    assert snapshot.balance == Decimal("42.5")
    assert session.posts == []
    _assert_cabinet_headers(session.calls)
