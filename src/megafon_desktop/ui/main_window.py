from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from megafon_desktop.services.account_service import AccountService


class AddAccountDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавить номер")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+7 999 123-45-67")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label = QLineEdit()

        form = QFormLayout(self)
        form.addRow("Номер", self.phone)
        form.addRow("Пароль ЛК", self.password)
        form.addRow("Метка", self.label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class MainWindow(QMainWindow):
    HEADERS = ("Номер", "Метка", "Баланс", "Фин. баланс", "Статус", "Обновлено")

    def __init__(self, service: AccountService) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle("MegaFon Desktop")
        self.resize(980, 560)

        central = QWidget()
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self.add_button = QPushButton("Добавить номер")
        self.refresh_button = QPushButton("Обновить выбранные")
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.status_label = QLabel("Готово")
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)

        self.add_button.clicked.connect(self._add_account)
        self.refresh_button.clicked.connect(self._refresh_selected)
        self.reload()

    def reload(self) -> None:
        accounts = self.service.list_accounts()
        self.table.setRowCount(len(accounts))
        for row_index, account in enumerate(accounts):
            assert account.id is not None
            latest = self.service.db.latest_snapshot(account.id)
            values = [
                account.phone,
                account.label,
                "" if latest is None or latest["balance"] is None else latest["balance"],
                "" if latest is None or latest["commercial_balance"] is None else latest["commercial_balance"],
                account.status.value,
                "" if account.last_updated_at is None else account.last_updated_at.astimezone().strftime("%d.%m.%Y %H:%M"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, account.id)
                self.table.setItem(row_index, column, item)

    def _add_account(self) -> None:
        dialog = AddAccountDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_account(dialog.phone.text(), dialog.password.text(), dialog.label.text())
        except (ValueError, OSError, sqlite3.Error) as exc:
            QMessageBox.critical(self, "Не удалось добавить номер", str(exc))
            return
        self.reload()

    def _selected_account_ids(self) -> list[int]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        result: list[int] = []
        for row in rows:
            item = self.table.item(row, 0)
            if item is not None:
                result.append(int(item.data(Qt.ItemDataRole.UserRole)))
        return result

    def _refresh_selected(self) -> None:
        ids = self._selected_account_ids()
        if not ids:
            QMessageBox.information(self, "Обновление", "Выберите хотя бы один номер.")
            return
        self.status_label.setText(f"Обновляем: {len(ids)}")
        self.refresh_button.setEnabled(False)
        try:
            for index, account_id in enumerate(ids, start=1):
                self.status_label.setText(f"Обновление {index}/{len(ids)}")
                self.service.refresh(account_id)
        finally:
            self.refresh_button.setEnabled(True)
            self.status_label.setText("Готово")
            self.reload()
