from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from megafon_desktop.domain.models import ExpenseEvent, Remainders, ServiceOption

_DATA_UNITS_KB = {
    "KB": Decimal(1),
    "КБ": Decimal(1),
    "MB": Decimal(1024),
    "МБ": Decimal(1024),
    "GB": Decimal(1024) ** 2,
    "ГБ": Decimal(1024) ** 2,
    "TB": Decimal(1024) ** 3,
    "ТБ": Decimal(1024) ** 3,
}


def decimal_value(value: Any, default: Decimal | None = None) -> Decimal | None:
    if value is None or value == "":
        return default
    if isinstance(value, dict):
        value = value.get("value")
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return default


def parse_remainders(payload: dict[str, Any]) -> Remainders:
    result = Remainders()
    items = payload.get("remainders") or []
    if not isinstance(items, list):
        return result

    for item in items:
        if not isinstance(item, dict):
            continue
        available = item.get("availableValue")
        if not isinstance(available, dict):
            continue
        value = decimal_value(available.get("value"), Decimal(0)) or Decimal(0)
        kind = str(item.get("remainderType", "")).upper()
        if kind == "VOICE":
            result.minutes += value
        elif kind == "MESSAGE":
            result.sms += value
        elif kind == "INTERNET":
            unit = str(available.get("unit", "KB")).upper()
            result.internet_kb += value * _DATA_UNITS_KB.get(unit, Decimal(1))
    return result


def _leading_price(text: str) -> Decimal:
    match = re.match(r"\s*(\d+(?:[.,]\d+)?)", text or "")
    return decimal_value(match.group(1), Decimal(0)) if match else Decimal(0)


def parse_services(
    tariff_payload: dict[str, Any] | None,
    services_payload: dict[str, Any] | None,
    tariff_name: str = "",
) -> list[ServiceOption]:
    result: list[ServiceOption] = []
    tariff_payload = tariff_payload or {}
    services_payload = services_payload or {}

    tariff_price = decimal_value(
        tariff_payload.get("ratePlanCharges", {}).get("price", {}).get("value"), Decimal(0)
    ) or Decimal(0)
    if tariff_name or tariff_price:
        result.append(
            ServiceOption(
                option_id="__tariff__",
                name=f"Тариф {tariff_name}".strip(),
                paid=tariff_price != 0,
                price=tariff_price,
            )
        )

    for paid, bucket in ((True, "paid"), (False, "free")):
        items = services_payload.get(bucket) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            info = item.get("previewImportantInformation") or []
            title = info[0].get("title", "") if info and isinstance(info[0], dict) else ""
            price = _leading_price(title) if paid else Decimal(0)
            option_id = str(item.get("optionId") or item.get("id") or item.get("optionName") or "")
            name = str(item.get("optionName") or item.get("name") or option_id)
            result.append(ServiceOption(option_id=option_id, name=name, paid=paid, price=price))

    return sorted(result, key=lambda item: (-(item.price or Decimal(0)), item.name.lower()))


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        pass
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def parse_expense_events(payloads: Iterable[dict[str, Any]]) -> list[ExpenseEvent]:
    events: list[ExpenseEvent] = []
    seen: set[tuple[datetime, Decimal, str]] = set()
    for payload in payloads:
        for item in _walk(payload):
            occurred_at = _parse_datetime(item.get("dateTime"))
            amount = decimal_value(item.get("amount"))
            if occurred_at is None or amount is None:
                continue
            definition_value = item.get("definition", "")
            definition = (
                str(definition_value.get("name") or definition_value.get("title") or "")
                if isinstance(definition_value, dict)
                else str(definition_value or "")
            )
            category = str(item.get("category") or item.get("type") or "")
            key = (occurred_at, amount, definition)
            if key in seen:
                continue
            seen.add(key)
            events.append(ExpenseEvent(occurred_at, amount, definition, category))
    events.sort(key=lambda event: event.occurred_at, reverse=True)
    return events


def latest_expense_event(payloads: Iterable[dict[str, Any]]) -> ExpenseEvent | None:
    events = parse_expense_events(payloads)
    return events[0] if events else None
