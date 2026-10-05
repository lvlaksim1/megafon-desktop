from __future__ import annotations

import sqlite3
from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
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

from megafon_desktop import __version__
from megafon_desktop.domain.models import AccountStatus
from megafon_desktop.services.account_service import AccountService
from megafon_desktop.ui.icon import make_app_icon


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


class CaptchaDialog(QDialog):
    def __init__(self, image_bytes: bytes, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Megafon Desktop — CAPTCHA")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("МегаФон просит ввести код с картинки:"))

        pixmap = QPixmap()
        if not pixmap.loadFromData(image_bytes):
            raise ValueError("Не удалось отобразить изображение CAPTCHA")

        image = QLabel()
        image.setPixmap(pixmap)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image)

        self.code = QLineEdit()
        self.code.setPlaceholderText("Код с картинки")
        self.code.returnPressed.connect(self.accept)
        layout.addWidget(self.code)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Продолжить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.code.setFocus()

    @classmethod
    def solve(cls, image_bytes: bytes, parent: QWidget | None = None) -> str | None:
        dialog = cls(image_bytes, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        code = dialog.code.text().strip()
        return code or None


class MainWindow(QMainWindow):
    HEADERS = (
        "Номер",
        "Метка",
        "Баланс",
        "Фин. баланс",
        "Статус",
        "Обновлено",
        "Действие",
    )
    STATUS_LABELS: ClassVar[dict[AccountStatus, str]] = {
        AccountStatus.NEW: "Новый",
        AccountStatus.OK: "Готов",
        AccountStatus.AUTH_REQUIRED: "Нужна авторизация",
        AccountStatus.CAPTCHA: "Нужна CAPTCHA",
        AccountStatus.BLOCKED: "Заблокирован",
        AccountStatus.ERROR: "Ошибка",
    }

    def __init__(self, service: AccountService) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle(f"Megafon Desktop v{__version__}")
        self.setWindowIcon(make_app_icon())
        self.resize(1040, 580)

        central = QWidget()
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(make_app_icon().pixmap(30, 30))
        toolbar.addWidget(logo)

        self.add_button = QPushButton("Добавить номер")
        self.refresh_button = QPushButton("Обновить выбранные")
        self.refresh_all_button = QPushButton("Обновить всё")
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.refresh_all_button)
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
        self.refresh_all_button.clicked.connect(self._refresh_all)
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
                (
                    ""
                    if latest is None or latest["commercial_balance"] is None
                    else latest["commercial_balance"]
                ),
                self.STATUS_LABELS.get(account.status, account.status.value),
                (
                    ""
                    if account.last_updated_at is None
                    else account.last_updated_at.astimezone().strftime("%d.%m.%Y %H:%M")
                ),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, account.id)
                self.table.setItem(row_index, column, item)

            refresh = QPushButton("Обновить")
            refresh.clicked.connect(
                lambda _checked=False, account_id=account.id: self._refresh_ids([account_id])
            )
            self.table.setCellWidget(row_index, 6, refresh)

    def _add_account(self) -> None:
        dialog = AddAccountDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_account(
                dialog.phone.text(),
                dialog.password.text(),
                dialog.label.text(),
            )
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

    def _solve_captcha(self, image_bytes: bytes) -> str | None:
        self.status_label.setText("Требуется CAPTCHA")
        QApplication.processEvents()
        try:
            return CaptchaDialog.solve(image_bytes, self)
        except ValueError as exc:
            QMessageBox.critical(self, "CAPTCHA", str(exc))
            return None

    def _set_refresh_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.refresh_all_button.setEnabled(enabled)
        self.table.setEnabled(enabled)

    def _refresh_ids(self, ids: list[int]) -> None:
        if not ids:
            return
        self._set_refresh_enabled(False)
        try:
            for index, account_id in enumerate(ids, start=1):
                self.status_label.setText(f"Обновление {index}/{len(ids)}")
                QApplication.processEvents()
                self.service.refresh(account_id, self._solve_captcha)
        finally:
            self._set_refresh_enabled(True)
            self.status_label.setText("Готово")
            self.reload()

    def _refresh_selected(self) -> None:
        ids = self._selected_account_ids()
        if not ids:
            QMessageBox.information(self, "Обновление", "Выберите хотя бы один номер.")
            return
        self._refresh_ids(ids)

    def _refresh_all(self) -> None:
        ids = [account.id for account in self.service.list_accounts() if account.id is not None]
        if not ids:
            QMessageBox.information(self, "Обновление", "Список номеров пуст.")
            return
        self._refresh_ids(ids)
