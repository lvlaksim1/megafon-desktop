from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QApplication

from megafon_desktop.domain.models import AccountRefresh, AccountSnapshot
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.secret_store import MemorySecretStore
from megafon_desktop.infra.settings import SettingsStore
from megafon_desktop.services.account_service import AccountService
from megafon_desktop.ui.main_window import MainWindow
from megafon_desktop.ui.theme import ThemeController


class FakeTransport:
    def refresh_account(self, phone, password, account_id, captcha_solver=None):
        del phone, password, captcha_solver
        return AccountRefresh(
            AccountSnapshot(
                account_id=account_id,
                captured_at=datetime.now(UTC),
                balance=Decimal("42.00"),
                commercial_balance=Decimal("40.00"),
            )
        )

    def reject_offers(self, phone, password, account_id, offer_ids, captcha_solver=None):
        del phone, password, account_id, offer_ids, captcha_solver
        return []

    def set_blocking(self, phone, password, account_id, enabled, captcha_solver=None):
        del phone, password, account_id, captcha_solver
        return enabled

    def forget_session(self, account_id):
        del account_id


def _build_window(tmp_path):
    app = QApplication.instance() or QApplication([])
    db = Database(tmp_path / "ui.db")
    secrets = MemorySecretStore()
    service = AccountService(db, secrets, FakeTransport())

    first = service.add_account("89991234567", "secret", "Первая метка")
    second = service.add_account("89991234568", "secret", "Вторая метка")
    assert first.id is not None and second.id is not None

    db.add_snapshot(
        AccountSnapshot(
            account_id=first.id,
            captured_at=datetime.now(UTC),
            balance=Decimal("10.00"),
            commercial_balance=Decimal("8.00"),
        )
    )

    settings = SettingsStore(tmp_path / "settings.json")
    theme = ThemeController(app)
    theme.apply("dark")
    window = MainWindow(service, settings, theme)
    app.processEvents()
    return app, db, service, window


def test_widgets_account_table_loads_with_spreadsheet_interaction(tmp_path):
    app, db, _service, window = _build_window(tmp_path)
    table = window.table

    assert table.rowCount() == 2
    assert table.columnCount() == len(window.HEADERS)
    assert table.selectionBehavior() == QAbstractItemView.SelectionBehavior.SelectItems
    assert table.selectionMode() == QAbstractItemView.SelectionMode.ExtendedSelection
    assert table.editTriggers() & QAbstractItemView.EditTrigger.DoubleClicked
    assert table.dragDropMode() == QAbstractItemView.DragDropMode.NoDragDrop

    # Account id is available from every cell, so a reordered row can never lose identity.
    for column in range(table.columnCount()):
        assert table.item(0, column).data(Qt.ItemDataRole.UserRole) == 1

    # Local label persists in SQLite.
    table.item(0, 1).setText("Изменённая метка")
    app.processEvents()
    assert db.get_account(1).label == "Изменённая метка"

    # Server-derived edits are intentionally temporary.
    table.item(0, 2).setText("999")
    assert table.item(0, 2).text() == "999"
    window._reload_accounts()
    assert table.item(0, 2).text() == "10.00"

    # We do not repeat cell values in hover tooltips.
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            assert table.item(row, column).toolTip() == ""

    window.close()
    window.deleteLater()
    app.processEvents()


def test_row_header_reorder_emits_complete_order_and_updates_database(tmp_path):
    app, _db, service, window = _build_window(tmp_path)
    table = window.table

    table.verticalHeader().moveSection(0, 1)
    app.processEvents()

    assert [account.id for account in service.list_accounts()] == [2, 1]
    assert table.verticalHeader().visualIndex(0) == 0
    assert table.verticalHeader().visualIndex(1) == 1

    window.close()
    window.deleteLater()
    app.processEvents()


def test_ctrl_f_search_moves_to_matching_cell(tmp_path):
    app, _db, _service, window = _build_window(tmp_path)

    find_shortcuts = [action.shortcut() for action in window.actions()]
    standard_find = QKeySequence(QKeySequence.StandardKey.Find)
    assert any(shortcut.matches(standard_find) == QKeySequence.SequenceMatch.ExactMatch
               for shortcut in find_shortcuts)

    assert window._find_in_widget_table(window.table, "Вторая метка", 1)
    assert window.table.currentRow() == 1
    assert window.table.currentColumn() == 1

    assert window._find_in_widget_table(window.table, "метка", 1)
    first_position = (window.table.currentRow(), window.table.currentColumn())
    assert window._find_in_widget_table(window.table, "метка", 1)
    second_position = (window.table.currentRow(), window.table.currentColumn())
    assert first_position != second_position

    window.close()
    window.deleteLater()
    app.processEvents()
