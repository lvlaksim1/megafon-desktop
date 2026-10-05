from decimal import Decimal

import requests

from megafon_desktop.infra.secret_store import MemorySecretStore
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


class CaptchaSession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.posts: list[dict[str, str]] = []

    def post(self, _url, *, data, headers, timeout):
        del headers, timeout
        self.posts.append(dict(data))
        if len(self.posts) == 1:
            return FakeResponse(
                401,
                payload={"code": "a211", "message": "Введите код с картинки"},
                text='{"code":"a211","message":"Введите код с картинки"}',
            )
        self.cookies.set("X-Cabinet-Access-Token", "token", domain=".megafon.ru", path="/")
        return FakeResponse(200, payload={"authenticated": True}, text='{"authenticated":true}')

    def get(self, _url, *, headers, timeout):
        del headers, timeout
        return FakeResponse(200, content=b"jpeg-image")


def test_decimal_parser():
    assert DirectHttpTransport._decimal("12,34") == Decimal("12.34")
    assert DirectHttpTransport._decimal(5) == Decimal(5)
    assert DirectHttpTransport._decimal(None) is None


def test_captcha_is_solved_inside_same_http_login_flow():
    transport = DirectHttpTransport()
    session = CaptchaSession()
    seen: list[bytes] = []

    def solve(image: bytes) -> str:
        seen.append(image)
        return "29p16m"

    transport.login(session, "79991234567", "secret", solve)

    assert seen == [b"jpeg-image"]
    assert session.posts == [
        {"password": "secret", "login": "79991234567"},
        {"password": "secret", "login": "79991234567", "captcha": "29p16m"},
    ]


def test_cookie_jar_is_persisted_in_secret_store():
    secrets = MemorySecretStore()
    transport = DirectHttpTransport(secrets=secrets)
    original = requests.Session()
    original.cookies.set(
        "X-Cabinet-Refresh-Token",
        "refresh-token",
        domain=".megafon.ru",
        path="/",
    )

    transport._save_session(7, original)

    restored = requests.Session()
    assert transport._restore_session(7, restored)
    assert restored.cookies.get("X-Cabinet-Refresh-Token") == "refresh-token"
