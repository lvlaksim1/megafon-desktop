from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


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


@dataclass(slots=True)
class AccountSnapshot:
    account_id: int
    captured_at: datetime
    balance: Decimal | None = None
    commercial_balance: Decimal | None = None
    tariff_name: str | None = None
    credit_limit: Decimal | None = None


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
class PersonalOffer:
    offer_id: str
    title: str
    subtitle: str = ""
    description: str = ""
    start_at: datetime | None = None
    end_at: datetime | None = None
