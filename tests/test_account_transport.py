from __future__ import annotations

import requests

from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.megafon.account_transport import AccountHttpTransport


class FakeResponse:
    def __init__(self, status_code: int, payload=None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload


class MutationSession:
    def __init__(self, option_states) -> None:
        self.cookies = requests.cookies.RequestsCookieJar()
        self.cookies.set("csrf-token", "csrf-value", domain=".megafon.ru", path="/")
        self.option_states = list(option_states)
        self.posts: list[tuple[str, dict[str, str]]] = []
        self.deletes: list[tuple[str, dict[str, str]]] = []

    def get(self, url, *, params, headers, timeout):
        del headers, timeout
        assert url.endswith("/api/options/list/current")
        assert params == {"showVASP": "true"}
        return FakeResponse(200, self.option_states.pop(0))

    def post(self, url, *, data, headers, timeout):
        del data, timeout
        self.posts.append((url, dict(headers)))
        return FakeResponse(200, {})

    def delete(self, url, *, headers, timeout):
        del timeout
        self.deletes.append((url, dict(headers)))
        return FakeResponse(200, {})


class TestTransport(AccountHttpTransport):
    __test__ = False

    def __init__(self, session) -> None:
        super().__init__(secrets=MemorySecretStore())
        self.fake_session = session

    def _authenticated_context(self, phone, password, account_id, captcha_solver):
        del phone, password, account_id, captcha_solver
        return self.fake_session, "https://api.megafon.ru/mlk", {
            "X-Cabinet-Id-Param": "id",
            "X-Cabinet-Check-Info": "check",
            "X-Cabinet-Validation-Param": "validation",
        }


def test_blocking_uses_vba_connect_option_id_and_csrf():
    blocked_payload = {
        "paid": [],
        "free": [{"optionId": "actual-block-id", "optionName": "Блокировка номера"}],
    }
    session = MutationSession([{"paid": [], "free": []}, blocked_payload])
    transport = TestTransport(session)

    assert transport.set_blocking("79991234567", "secret", 1, True) is True
    assert len(session.posts) == 1
    url, headers = session.posts[0]
    assert url.endswith("/api/options/Q0L16QxY-nvN6dgAV04woA")
    assert headers["X-CSRF-TOKEN"] == "csrf-value"
    assert headers["X-Cabinet-Capabilities"] == "authentication-2020"


def test_unblocking_deletes_actual_current_option_id():
    blocked_payload = {
        "paid": [],
        "free": [{"optionId": "runtime-block-id", "optionName": "Блокировка номера"}],
    }
    session = MutationSession([blocked_payload, {"paid": [], "free": []}])
    transport = TestTransport(session)

    assert transport.set_blocking("79991234567", "secret", 1, False) is False
    assert len(session.deletes) == 1
    url, headers = session.deletes[0]
    assert url.endswith("/api/options/runtime-block-id")
    assert headers["X-CSRF-TOKEN"] == "csrf-value"
