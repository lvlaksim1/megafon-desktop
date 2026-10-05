from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .browser_transport import ResponseCapture

_REDACTED = "<redacted>"
_SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "password",
    "passwd",
    "secret",
    "token",
    "csrf",
    "session",
    "guid",
    "device-id",
    "device_id",
    "msisdn",
    "phone",
    "login",
)


def _sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("_", "-")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def redact_value(value: Any) -> Any:
    """Return a JSON-safe copy with credential-like fields removed."""
    if isinstance(value, dict):
        return {
            str(key): _REDACTED if _sensitive_key(str(key)) else redact_value(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_value(child) for child in value]
    return value


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        query.append((key, _REDACTED if _sensitive_key(key) else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def _response_json(content: dict[str, Any]) -> Any | None:
    text = content.get("text")
    if not isinstance(text, str) or not text:
        return None
    if content.get("encoding") == "base64":
        try:
            text = base64.b64decode(text).decode("utf-8", errors="replace")
        except (ValueError, UnicodeError):
            return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@dataclass(slots=True)
class DiagnosticImport:
    capture: ResponseCapture
    matched_responses: int
    sanitized_entries: list[dict[str, Any]]


def import_har_payload(payload: dict[str, Any]) -> DiagnosticImport:
    """Import Chrome/Playwright HAR JSON without retaining raw secrets in diagnostics."""
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise TypeError("HAR log.entries must be an array")

    capture = ResponseCapture()
    sanitized_entries: list[dict[str, Any]] = []
    matched = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request") if isinstance(entry.get("request"), dict) else {}
        response = entry.get("response") if isinstance(entry.get("response"), dict) else {}
        url = str(request.get("url") or "")
        status = response.get("status")
        if not isinstance(status, int):
            continue

        content = response.get("content") if isinstance(response.get("content"), dict) else {}
        body = _response_json(content)
        if capture.observe(url, status, body):
            matched += 1

        sanitized_entries.append(
            {
                "url": redact_url(url),
                "method": str(request.get("method") or ""),
                "status": status,
                "request_headers": redact_value(request.get("headers") or []),
                "response_headers": redact_value(response.get("headers") or []),
                "json": redact_value(body) if body is not None else None,
            }
        )

    return DiagnosticImport(capture, matched, sanitized_entries)


def import_har(path: Path | str) -> DiagnosticImport:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid HAR JSON: {source}") from exc
    if not isinstance(payload, dict):
        raise TypeError("HAR root must be an object")
    return import_har_payload(payload)
