from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from megafon_desktop.domain.models import (
    Account,
    AccountSnapshot,
    AccountStatus,
    AvailableOption,
    PersonalOffer,
)

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'new',
    last_error TEXT NOT NULL DEFAULT '',
    last_updated_at TEXT NULL,
    created_at TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    captured_at TEXT NOT NULL,
    balance TEXT NULL,
    commercial_balance TEXT NULL,
    tariff_name TEXT NULL,
    credit_limit TEXT NULL,
    last_action_amount TEXT NULL,
    last_action_name TEXT NULL,
    last_action_at TEXT NULL,
    offers_summary TEXT NOT NULL DEFAULT '',
    blocked INTEGER NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_account_time
ON snapshots(account_id, captured_at DESC);

CREATE TABLE IF NOT EXISTS offer_rules (
    offer_key TEXT PRIMARY KEY,
    match_kind TEXT NOT NULL CHECK(match_kind IN ('id', 'title')),
    action TEXT NOT NULL CHECK(action IN ('keep', 'reject', 'ask')),
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offer_catalog (
    offer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    descript TEXT NOT NULL DEFAULT '',
    descript_full TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS account_offer_state (
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    offer_id TEXT NOT NULL REFERENCES offer_catalog(offer_id) ON DELETE CASCADE,
    start_at TEXT NULL,
    end_at TEXT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY(account_id, offer_id)
);

CREATE TABLE IF NOT EXISTS available_options (
    option_id TEXT PRIMARY KEY,
    option_name TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        self._ensure_column("accounts", "sort_order", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column("snapshots", "last_action_amount", "TEXT NULL")
        self._ensure_column("snapshots", "last_action_name", "TEXT NULL")
        self._ensure_column("snapshots", "last_action_at", "TEXT NULL")
        self._ensure_column("snapshots", "offers_summary", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column("snapshots", "blocked", "INTEGER NULL")

        rows = self._conn.execute(
            "SELECT id,sort_order FROM accounts ORDER BY sort_order,id"
        ).fetchall()
        orders = [int(row["sort_order"]) for row in rows]
        if rows and len(set(orders)) != len(rows):
            for index, row in enumerate(rows):
                self._conn.execute(
                    "UPDATE accounts SET sort_order=? WHERE id=?",
                    (index, int(row["id"])),
                )
            self._conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        names = {
            str(row["name"])
            for row in self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in names:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def normalize_phone(phone: str) -> str:
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        if len(digits) == 10:
            digits = "7" + digits
        if len(digits) != 11 or not digits.startswith("7"):
            raise ValueError("phone must be a Russian mobile number")
        return digits

    def add_account(self, phone: str, label: str = "") -> Account:
        normalized = self.normalize_phone(phone)
        now = datetime.now(UTC).isoformat()
        next_order = int(
            self._conn.execute(
                "SELECT COALESCE(MAX(sort_order),-1)+1 FROM accounts"
            ).fetchone()[0]
        )
        cur = self._conn.execute(
            "INSERT INTO accounts(phone,label,created_at,sort_order) VALUES(?,?,?,?)",
            (normalized, label.strip(), now, next_order),
        )
        self._conn.commit()
        return self.get_account(int(cur.lastrowid))

    def delete_account(self, account_id: int) -> None:
        self._conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        self._conn.commit()
        self.set_account_order([account.id for account in self.list_accounts() if account.id])

    def get_account(self, account_id: int) -> Account:
        row = self._conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if row is None:
            raise KeyError(account_id)
        return self._account_from_row(row)

    def list_accounts(self) -> list[Account]:
        rows = self._conn.execute("SELECT * FROM accounts ORDER BY sort_order,id").fetchall()
        return [self._account_from_row(row) for row in rows]

    def set_account_order(self, account_ids: list[int]) -> None:
        if not account_ids:
            return
        existing = {
            int(row["id"])
            for row in self._conn.execute("SELECT id FROM accounts").fetchall()
        }
        supplied = [int(value) for value in account_ids]
        if set(supplied) != existing or len(supplied) != len(existing):
            raise ValueError("account order must contain every account exactly once")
        with self._conn:
            for position, account_id in enumerate(supplied):
                self._conn.execute(
                    "UPDATE accounts SET sort_order=? WHERE id=?",
                    (position, account_id),
                )

    def update_account_state(
        self,
        account_id: int,
        *,
        status: AccountStatus,
        last_error: str = "",
        updated_at: datetime | None = None,
    ) -> None:
        stamp = (updated_at or datetime.now(UTC)).isoformat()
        self._conn.execute(
            "UPDATE accounts SET status=?,last_error=?,last_updated_at=? WHERE id=?",
            (status.value, last_error, stamp, account_id),
        )
        self._conn.commit()

    def add_snapshot(self, snapshot: AccountSnapshot) -> None:
        self._conn.execute(
            """INSERT INTO snapshots(
                account_id,captured_at,balance,commercial_balance,tariff_name,credit_limit,
                last_action_amount,last_action_name,last_action_at,offers_summary,blocked
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                snapshot.account_id,
                snapshot.captured_at.isoformat(),
                None if snapshot.balance is None else str(snapshot.balance),
                None if snapshot.commercial_balance is None else str(snapshot.commercial_balance),
                snapshot.tariff_name,
                None if snapshot.credit_limit is None else str(snapshot.credit_limit),
                None if snapshot.last_action_amount is None else str(snapshot.last_action_amount),
                snapshot.last_action_name,
                None if snapshot.last_action_at is None else snapshot.last_action_at.isoformat(),
                snapshot.offers_summary,
                None if snapshot.blocked is None else int(snapshot.blocked),
            ),
        )
        self._conn.commit()

    def latest_snapshot(self, account_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM snapshots WHERE account_id=? ORDER BY captured_at DESC LIMIT 1",
            (account_id,),
        ).fetchone()

    def set_latest_blocked(self, account_id: int, blocked: bool) -> None:
        latest = self.latest_snapshot(account_id)
        if latest is None:
            self.add_snapshot(
                AccountSnapshot(
                    account_id=account_id,
                    captured_at=datetime.now(UTC),
                    blocked=blocked,
                )
            )
            return
        self._conn.execute(
            "UPDATE snapshots SET blocked=? WHERE id=?",
            (int(blocked), int(latest["id"])),
        )
        self._conn.commit()

    def sync_offers(self, account_id: int, offers: list[PersonalOffer]) -> None:
        now = datetime.now(UTC).isoformat()
        with self._conn:
            self._conn.execute(
                "UPDATE account_offer_state SET active=0 WHERE account_id=?",
                (account_id,),
            )
            for offer in offers:
                existing = self._conn.execute(
                    "SELECT offer_id FROM offer_catalog WHERE offer_id=?",
                    (offer.offer_id,),
                ).fetchone()
                if existing is None:
                    inherited = self._conn.execute(
                        "SELECT note FROM offer_catalog WHERE name=? "
                        "ORDER BY last_seen_at DESC LIMIT 1",
                        (offer.title,),
                    ).fetchone()
                    note = "" if inherited is None else str(inherited["note"])
                    self._conn.execute(
                        """INSERT INTO offer_catalog(
                            offer_id,name,descript,descript_full,note,first_seen_at,last_seen_at
                        ) VALUES(?,?,?,?,?,?,?)""",
                        (
                            offer.offer_id,
                            offer.title,
                            offer.subtitle or offer.description,
                            offer.full_description or offer.description,
                            note,
                            now,
                            now,
                        ),
                    )
                else:
                    self._conn.execute(
                        "UPDATE offer_catalog SET last_seen_at=? WHERE offer_id=?",
                        (now, offer.offer_id),
                    )

                self._conn.execute(
                    """INSERT INTO account_offer_state(
                        account_id,offer_id,start_at,end_at,active,first_seen_at,last_seen_at
                    ) VALUES(?,?,?,?,1,?,?)
                    ON CONFLICT(account_id,offer_id) DO UPDATE SET
                        start_at=excluded.start_at,
                        end_at=excluded.end_at,
                        active=1,
                        last_seen_at=excluded.last_seen_at""",
                    (
                        account_id,
                        offer.offer_id,
                        None if offer.start_at is None else offer.start_at.isoformat(),
                        None if offer.end_at is None else offer.end_at.isoformat(),
                        now,
                        now,
                    ),
                )

    def set_offer_note(self, offer_id: str, note: str) -> None:
        normalized = note.strip().lower()
        if normalized not in {"", "оставить", "удалить"}:
            raise ValueError("примечание должно быть: оставить, удалить или пусто")
        self._conn.execute(
            "UPDATE offer_catalog SET note=? WHERE offer_id=?",
            (normalized, offer_id),
        )
        self._conn.commit()

    def offer_rows(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """SELECT c.offer_id,c.name,c.descript,c.descript_full,c.note,
                      GROUP_CONCAT(DISTINCT a.phone) AS phones
               FROM offer_catalog c
               LEFT JOIN account_offer_state s ON s.offer_id=c.offer_id
               LEFT JOIN accounts a ON a.id=s.account_id
               GROUP BY c.offer_id,c.name,c.descript,c.descript_full,c.note
               ORDER BY c.last_seen_at DESC,c.name COLLATE NOCASE"""
        ).fetchall()
        return [dict(row) for row in rows]

    def account_offer_summary(self, account_id: int) -> str:
        rows = self._conn.execute(
            """SELECT c.offer_id,c.name,s.start_at,s.end_at
               FROM account_offer_state s
               JOIN offer_catalog c ON c.offer_id=s.offer_id
               WHERE s.account_id=? AND s.active=1 AND c.note<>'удалить'
               ORDER BY c.name COLLATE NOCASE,c.offer_id""",
            (account_id,),
        ).fetchall()
        parts: list[str] = []
        for row in rows:
            value = f"{row['offer_id']} {row['name']}".strip()
            start = self._short_date(row["start_at"])
            end = self._short_date(row["end_at"])
            if start and end:
                value += f" с {start} по {end}"
            elif start:
                value += f" с {start}"
            elif end:
                value += f" по {end}"
            parts.append(value)
        return "; ".join(parts)

    @staticmethod
    def _short_date(value: str | None) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).strftime("%d.%m.%y")
        except ValueError:
            return value

    def sync_available_options(self, options: list[AvailableOption]) -> None:
        now = datetime.now(UTC).isoformat()
        with self._conn:
            for option in options:
                self._conn.execute(
                    """INSERT OR IGNORE INTO available_options(
                        option_id,option_name,raw_json,first_seen_at
                    ) VALUES(?,?,?,?)""",
                    (
                        option.option_id,
                        option.name,
                        json.dumps(option.fields, ensure_ascii=False, sort_keys=True),
                        now,
                    ),
                )

    def available_option_rows(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT option_id,option_name,raw_json FROM available_options "
            "ORDER BY option_name COLLATE NOCASE"
        ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                fields = json.loads(str(row["raw_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                fields = {}
            if not isinstance(fields, dict):
                fields = {}
            fields = dict(fields)
            fields["optionId"] = str(row["option_id"])
            fields["optionName"] = str(row["option_name"])
            result.append(fields)
        return result

    @staticmethod
    def _account_from_row(row: sqlite3.Row) -> Account:
        return Account(
            id=int(row["id"]),
            phone=str(row["phone"]),
            label=str(row["label"]),
            enabled=bool(row["enabled"]),
            status=AccountStatus(row["status"]),
            last_error=str(row["last_error"]),
            last_updated_at=(
                datetime.fromisoformat(row["last_updated_at"])
                if row["last_updated_at"]
                else None
            ),
            sort_order=int(row["sort_order"]),
        )
