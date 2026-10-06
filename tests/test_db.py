from datetime import UTC, datetime
from decimal import Decimal

import pytest

from megafon_desktop.domain.models import AccountSnapshot, AvailableOption, PersonalOffer
from megafon_desktop.infra.db import Database


def test_phone_normalization_snapshot_and_account_order(tmp_path):
    db = Database(tmp_path / "test.db")
    first = db.add_account("8 (999) 123-45-67", "test")
    second = db.add_account("8 (999) 123-45-68", "second")
    assert first.phone == "79991234567"
    assert first.id is not None and second.id is not None

    db.add_snapshot(
        AccountSnapshot(
            account_id=first.id,
            captured_at=datetime.now(UTC),
            balance=Decimal("123.45"),
            commercial_balance=Decimal("100.00"),
            last_action_amount=Decimal("5.50"),
            last_action_name="Платёж",
            blocked=True,
        )
    )
    latest = db.latest_snapshot(first.id)
    assert latest is not None
    assert latest["balance"] == "123.45"
    assert latest["last_action_amount"] == "5.50"
    assert latest["blocked"] == 1

    db.set_account_order([second.id, first.id])
    assert [account.id for account in db.list_accounts()] == [second.id, first.id]


def test_offer_base_inherits_note_and_offer_options_are_unique_by_option_id(tmp_path):
    db = Database(tmp_path / "test.db")
    account = db.add_account("89991234567")
    assert account.id is not None

    first = PersonalOffer(
        "offer-1",
        "Один тариф",
        subtitle="Описание",
        options=[
            AvailableOption(
                "o1",
                "Опция",
                {
                    "optionId": "o1",
                    "optionName": "Опция",
                    "shortDescription": "Коротко",
                    "order": 7,
                },
            )
        ],
    )
    db.sync_offers(account.id, [first])
    db.set_offer_note("offer-1", "оставить")

    second = PersonalOffer(
        "offer-2",
        "Один тариф",
        subtitle="Новое описание",
        options=[
            AvailableOption(
                "o1",
                "Опция 2",
                {"optionId": "o1", "optionName": "Опция 2", "order": 99},
            )
        ],
    )
    db.sync_offers(account.id, [second])
    rows = {row["offer_id"]: row for row in db.offer_rows()}
    assert rows["offer-2"]["note"] == "оставить"
    assert "79991234567" in rows["offer-2"]["phones"]

    options = db.available_option_rows()
    assert len(options) == 1
    assert options[0]["id_офера"] == "offer-1"
    assert options[0]["opt_name"] == "Опция"
    assert options[0]["id_opt"] == "o1"
    assert options[0]["id_order"] == "7"
    assert options[0]["opt_shortDescription"] == "Коротко"


@pytest.mark.parametrize("value", ["123", "7999", "+1 555 123 4567"])
def test_invalid_phone_rejected(tmp_path, value):
    db = Database(tmp_path / "test.db")
    with pytest.raises(ValueError):
        db.add_account(value)
