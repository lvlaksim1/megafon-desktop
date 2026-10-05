import base64
import json

from megafon_desktop.megafon.diagnostics import import_har_payload, redact_url, redact_value


def test_redaction_covers_headers_nested_tokens_and_sensitive_query_values():
    assert redact_value(
        {
            "Authorization": "Bearer secret",
            "nested": {"csrf_token": "abc", "safe": 1},
        }
    ) == {
        "Authorization": "<redacted>",
        "nested": {"csrf_token": "<redacted>", "safe": 1},
    }
    url = redact_url(
        "https://example.test/api?dateFrom=01.10.2026&token=abc&msisdn=79990000000"
    )
    assert "dateFrom=01.10.2026" in url
    assert "token=%3Credacted%3E" in url
    assert "msisdn=%3Credacted%3E" in url


def test_har_import_captures_known_json_and_keeps_sanitized_copy():
    body = {
        "balance": 123.45,
        "sessionToken": "very-secret",
    }
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": "https://lk.megafon.ru/balance/api/main?login=79990000000",
                        "method": "GET",
                        "headers": [{"name": "Cookie", "value": "JSESSIONID=secret"}],
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "Set-Cookie", "value": "token=secret"}],
                        "content": {"text": json.dumps(body)},
                    },
                }
            ]
        }
    }

    imported = import_har_payload(har)
    assert imported.matched_responses == 1
    assert imported.capture.latest("balance/api/main") == body
    safe = imported.sanitized_entries[0]
    assert "79990000000" not in safe["url"]
    assert safe["json"]["sessionToken"] == "<redacted>"


def test_har_import_decodes_base64_json():
    encoded = base64.b64encode(json.dumps({"name": "Test"}).encode()).decode()
    imported = import_har_payload(
        {
            "log": {
                "entries": [
                    {
                        "request": {
                            "url": "https://lk.megafon.ru/api/tariff/2019-3/current",
                            "method": "GET",
                        },
                        "response": {
                            "status": 200,
                            "content": {"encoding": "base64", "text": encoded},
                        },
                    }
                ]
            }
        }
    )
    assert imported.capture.latest("api/tariff/2019-3/current") == {"name": "Test"}
