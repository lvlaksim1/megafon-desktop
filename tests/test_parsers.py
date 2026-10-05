from datetime import datetime
from decimal import Decimal

from megafon_desktop.megafon.parsers import (
    latest_expense_event,
    parse_remainders,
    parse_services,
)


def test_parse_remainders_matches_mbplugin_shapes():
    value = parse_remainders(
        {
            "remainders": [
                {"remainderType": "VOICE", "availableValue": {"value": 120, "unit": "MIN"}},
                {"remainderType": "MESSAGE", "availableValue": {"value": 50, "unit": "SMS"}},
                {"remainderType": "INTERNET", "availableValue": {"value": 2, "unit": "ГБ"}},
                {"remainderType": "INTERNET", "availableValue": {"value": 512, "unit": "МБ"}},
            ]
        }
    )
    assert value.minutes == Decimal(120)
    assert value.sms == Decimal(50)
    assert value.internet_kb == Decimal(2 * 1024**2 + 512 * 1024)


def test_parse_services_matches_mbplugin_shapes():
    services = parse_services(
        {"ratePlanCharges": {"price": {"value": "550,00"}}},
        {
            "paid": [
                {
                    "optionId": "paid-1",
                    "optionName": "Платная услуга",
                    "previewImportantInformation": [{"title": "200 ₽ за 30 дней"}],
                }
            ],
            "free": [{"optionId": "free-1", "optionName": "Бесплатная услуга"}],
        },
        "Тест",
    )
    assert [(item.name, item.price) for item in services] == [
        ("Тариф Тест", Decimal("550.00")),
        ("Платная услуга", Decimal(200)),
        ("Бесплатная услуга", Decimal(0)),
    ]


def test_latest_expense_event_recurses_and_deduplicates():
    event = latest_expense_event(
        [
            {
                "items": [
                    {"dateTime": "2026-09-01T10:00:00+03:00", "amount": 5, "definition": "SMS"},
                    {
                        "dateTime": "2026-10-01T11:00:00+03:00",
                        "amount": "12,50",
                        "definition": "Интернет",
                    },
                ]
            }
        ]
    )
    assert event is not None
    assert event.occurred_at == datetime(2026, 10, 1, 11, 0, tzinfo=event.occurred_at.tzinfo)
    assert event.amount == Decimal("12.50")
    assert event.definition == "Интернет"
