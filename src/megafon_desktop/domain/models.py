from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any


class AccountStatus(StrEnum):
    NEW = "new"
    OK = "ok"
    AUTH_REQUIRED = "auth_required"
    CAPTCHA = "captcha"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass(slots=True)
class Account:
    id: int | None
    phone: str
    label: str = ""
    enabled: bool = True
    status: AccountStatus = AccountStatus.NEW
    last_error: str = ""
    last_updated_at: datetime | None = None
    sort_order: int = 0


@dataclass(slots=True)
class AccountSnapshot:
    account_id: int
    captured_at: datetime
    balance: Decimal | None = None
    commercial_balance: Decimal | None = None
    tariff_name: str | None = None
    credit_limit: Decimal | None = None
    last_action_amount: Decimal | None = None
    last_action_name: str | None = None
    last_action_at: datetime | None = None
    offers_summary: str = ""
    blocked: bool | None = None


@dataclass(slots=True)
class Remainders:
    minutes: Decimal = Decimal(0)
    sms: Decimal = Decimal(0)
    internet_kb: Decimal = Decimal(0)


@dataclass(slots=True)
class ServiceOption:
    option_id: str
    name: str
    paid: bool
    price: Decimal | None = None


@dataclass(slots=True)
class ExpenseEvent:
    occurred_at: datetime
    amount: Decimal
    definition: str = ""
    category: str = ""


@dataclass(slots=True)
class AvailableOption:
    option_id: str
    name: str
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PersonalOffer:
    offer_id: str
    title: str
    subtitle: str = ""
    description: str = ""
    full_description: str = ""
    start_at: datetime | None = None
    end_at: datetime | None = None
    options: list[AvailableOption] = field(default_factory=list)


@dataclass(slots=True)
class AccountRefresh:
    snapshot: AccountSnapshot
    offers: list[PersonalOffer] = field(default_factory=list)
