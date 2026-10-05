from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from megafon_desktop.domain.models import Account, AccountSnapshot, AccountStatus


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
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    captured_at TEXT NOT NULL,
    balance TEXT NULL,
    commercial_balance TEXT NULL,
    tariff_name TEXT NULL,
    credit_limit TEXT NULL
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
"""


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

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
        cur = self._conn.execute(
            "INSERT INTO accounts(phone,label,created_at) VALUES(?,?,?)",
            (normalized, label.strip(), now),
        )
        self._conn.commit()
        return self.get_account(int(cur.lastrowid))

    def delete_account(self, account_id: int) -> None:
        self._conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        self._conn.commit()

    def get_account(self, account_id: int) -> Account:
        row = self._conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if row is None:
            raise KeyError(account_id)
        return self._account_from_row(row)

    def list_accounts(self) -> list[Account]:
        rows = self._conn.execute("SELECT * FROM accounts ORDER BY phone").fetchall()
        return [self._account_from_row(row) for row in rows]

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
                account_id,captured_at,balance,commercial_balance,tariff_name,credit_limit
            ) VALUES(?,?,?,?,?,?)""",
            (
                snapshot.account_id,
                snapshot.captured_at.isoformat(),
                None if snapshot.balance is None else str(snapshot.balance),
                None if snapshot.commercial_balance is None else str(snapshot.commercial_balance),
                snapshot.tariff_name,
                None if snapshot.credit_limit is None else str(snapshot.credit_limit),
            ),
        )
        self._conn.commit()

    def latest_snapshot(self, account_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM snapshots WHERE account_id=? ORDER BY captured_at DESC LIMIT 1",
            (account_id,),
        ).fetchone()

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
        )
