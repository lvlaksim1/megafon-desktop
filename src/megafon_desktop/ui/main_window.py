from __future__ import annotations

import base64
import json
import sqlite3
from datetime import datetime
from typing import ClassVar

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from megafon_desktop import __version__
from megafon_desktop.domain.models import AccountStatus
from megafon_desktop.infra.settings import SettingsStore
from megafon_desktop.services.account_service import AccountService
from megafon_desktop.ui.icon import make_app_icon
from megafon_desktop.ui.theme import ThemeController


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


class AccountTable(QTableWidget):
    rowsReordered = Signal(list)

    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(True)

    def account_ids(self) -> list[int]:
        result: list[int] = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item is not None:
                account_id = item.data(Qt.ItemDataRole.UserRole)
                if account_id is not None:
                    result.append(int(account_id))
        return result

    def selected_account_ids(self) -> list[int]:
        rows = sorted({index.row() for index in self.selectionModel().selectedRows()})
        if not rows and self.currentRow() >= 0:
            rows = [self.currentRow()]
        result: list[int] = []
        for row in rows:
            item = self.item(row, 0)
            if item is not None:
                account_id = item.data(Qt.ItemDataRole.UserRole)
                if account_id is not None:
                    result.append(int(account_id))
        return result

    def dropEvent(self, event: QDropEvent) -> None:
        if event.source() is not self:
            super().dropEvent(event)
            return

        selected_rows = sorted({index.row() for index in self.selectionModel().selectedRows()})
        if not selected_rows:
            event.ignore()
            return

        order = self.account_ids()
        moved = [order[row] for row in selected_rows]
        remaining = [value for index, value in enumerate(order) if index not in selected_rows]
        target = self.indexAt(event.position().toPoint()).row()
        if target < 0:
            target = len(order)
        removed_before = sum(1 for row in selected_rows if row < target)
        insert_at = max(0, min(len(remaining), target - removed_before))
        new_order = remaining[:insert_at] + moved + remaining[insert_at:]

        if new_order != order:
            self.rowsReordered.emit(new_order)
        event.acceptProposedAction()


class OfferNoteDelegate(QStyledItemDelegate):
    VALUES = ("", "оставить", "удалить")

    def createEditor(self, parent, _option, _index):
        editor = QComboBox(parent)
        editor.addItems(self.VALUES)
        return editor

    def setEditorData(self, editor, index) -> None:
        value = str(index.data(Qt.ItemDataRole.EditRole) or "")
        editor.setCurrentText(value if value in self.VALUES else "")

    def setModelData(self, editor, model, index) -> None:
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class MainWindow(QMainWindow):
    HEADERS = (
        "Номер",
        "Метка",
        "Баланс",
        "Фин. баланс",
        "Сумма последнего действия",
        "Название платежа",
        "Дата последнего действия",
        "Предложения",
        "Блокировка",
        "Статус",
        "Обновлено",
    )
    STATUS_LABELS: ClassVar[dict[AccountStatus, str]] = {
        AccountStatus.NEW: "Новый",
        AccountStatus.OK: "Готов",
        AccountStatus.AUTH_REQUIRED: "Нужна авторизация",
        AccountStatus.CAPTCHA: "Нужна CAPTCHA",
        AccountStatus.BLOCKED: "Заблокирован",
        AccountStatus.ERROR: "Ошибка",
    }

    def __init__(
        self,
        service: AccountService,
        settings: SettingsStore,
        theme: ThemeController,
    ) -> None:
        super().__init__()
        self.service = service
        self.settings = settings
        self.theme = theme
        self._header_ready = False
        self._loading_offers = False
        self.setWindowTitle(f"Megafon Desktop v{__version__}")
        self.setWindowIcon(make_app_icon())
        self.resize(1500, 720)

        central = QWidget()
        root = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self.add_button = QPushButton("Добавить номер")
        self.refresh_selected_button = QPushButton("Обновить выбранные")
        self.delete_button = QPushButton("Удалить")
        self.block_button = QPushButton("Установить блокировку")
        self.unblock_button = QPushButton("Снять блокировку")
        for button in (
            self.add_button,
            self.refresh_selected_button,
            self.delete_button,
            self.block_button,
            self.unblock_button,
        ):
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        self.settings_button = self._build_settings_button()
        toolbar.addWidget(self.settings_button)
        root.addLayout(toolbar)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        accounts_page = QWidget()
        accounts_layout = QVBoxLayout(accounts_page)
        accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.table = AccountTable(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)
        accounts_layout.addWidget(self.table)
        self.tabs.addTab(accounts_page, "Аккаунты")

        self.offer_table = QTableWidget(0, 6)
        self.offer_table.setHorizontalHeaderLabels(
            ("ID", "Название", "Описание", "Полное описание", "Примечание", "Номера")
        )
        self.offer_table.setAlternatingRowColors(True)
        self.offer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.offer_table.horizontalHeader().setSectionsMovable(True)
        self.offer_table.setItemDelegateForColumn(4, OfferNoteDelegate(self.offer_table))
        self.tabs.addTab(self.offer_table, "База оферов")

        self.options_table = QTableWidget(0, 0)
        self.options_table.setAlternatingRowColors(True)
        self.options_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.options_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.options_table.horizontalHeader().setSectionsMovable(True)
        self.tabs.addTab(self.options_table, "Доступные опции")

        self.status_label = QLabel("Готово")
        root.addWidget(self.status_label)
        self.setCentralWidget(central)

        self.add_button.clicked.connect(self._add_account)
        self.refresh_selected_button.clicked.connect(self._refresh_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        self.block_button.clicked.connect(lambda: self._set_blocking_selected(True))
        self.unblock_button.clicked.connect(lambda: self._set_blocking_selected(False))
        self.table.rowsReordered.connect(self._rows_reordered)
        self.offer_table.itemChanged.connect(self._offer_item_changed)

        self.reload()
        self._restore_header_state()
        header.sectionMoved.connect(self._save_header_state)
        header.sectionResized.connect(self._save_header_state)
        self._header_ready = True

    def _build_settings_button(self) -> QToolButton:
        button = QToolButton()
        button.setText("Настройки")
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(button)
        theme_menu = menu.addMenu("Тема")
        group = QActionGroup(theme_menu)
        group.setExclusive(True)
        labels = {"system": "Системная", "light": "Светлая", "dark": "Тёмная"}
        for value, label in labels.items():
            action = QAction(label, group)
            action.setCheckable(True)
            action.setChecked(self.settings.data.theme == value)
            action.triggered.connect(
                lambda checked=False, theme_name=value: self._set_theme(theme_name)
                if checked
                else None
            )
            theme_menu.addAction(action)
        button.setMenu(menu)
        return button

    def _set_theme(self, theme_name: str) -> None:
        self.settings.set_theme(theme_name)
        self.theme.apply(theme_name)

    def _restore_header_state(self) -> None:
        encoded = self.settings.data.account_header_state
        if encoded:
            try:
                raw = base64.b64decode(encoded.encode("ascii"), validate=True)
                if self.table.horizontalHeader().restoreState(QByteArray(raw)):
                    return
            except (ValueError, UnicodeError):
                pass
        self.table.resizeColumnsToContents()
        for column in range(self.table.columnCount()):
            self.table.setColumnWidth(column, min(max(self.table.columnWidth(column), 90), 330))

    def _save_header_state(self, *_args) -> None:
        if not self._header_ready:
            return
        raw = bytes(self.table.horizontalHeader().saveState())
        self.settings.set_account_header_state(base64.b64encode(raw).decode("ascii"))

    @staticmethod
    def _format_timestamp(value: str | None) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).astimezone().strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return str(value)

    def reload(self) -> None:
        self._reload_accounts()
        self._reload_offers()
        self._reload_options()

    def _reload_accounts(self) -> None:
        accounts = self.service.list_accounts()
        self.table.setRowCount(len(accounts))
        for row_index, account in enumerate(accounts):
            assert account.id is not None
            latest = self.service.db.latest_snapshot(account.id)
            blocked = None if latest is None else latest["blocked"]
            values = [
                account.phone,
                account.label,
                "" if latest is None or latest["balance"] is None else latest["balance"],
                ""
                if latest is None or latest["commercial_balance"] is None
                else latest["commercial_balance"],
                ""
                if latest is None or latest["last_action_amount"] is None
                else latest["last_action_amount"],
                "" if latest is None else latest["last_action_name"] or "",
                ""
                if latest is None
                else self._format_timestamp(latest["last_action_at"]),
                self.service.db.account_offer_summary(account.id),
                "" if blocked is None else ("Да" if bool(blocked) else "Нет"),
                self.STATUS_LABELS.get(account.status, account.status.value),
                ""
                if account.last_updated_at is None
                else account.last_updated_at.astimezone().strftime("%d.%m.%Y %H:%M"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, account.id)
                if column == 9 and account.last_error:
                    item.setToolTip(account.last_error)
                self.table.setItem(row_index, column, item)

    def _reload_offers(self) -> None:
        rows = self.service.offer_rows()
        self._loading_offers = True
        self.offer_table.blockSignals(True)
        try:
            self.offer_table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                values = (
                    row.get("offer_id", ""),
                    row.get("name", ""),
                    row.get("descript", ""),
                    row.get("descript_full", ""),
                    row.get("note", ""),
                    row.get("phones", "") or "",
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if column != 4:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if column == 0:
                        item.setData(Qt.ItemDataRole.UserRole, str(row.get("offer_id", "")))
                    self.offer_table.setItem(row_index, column, item)
        finally:
            self.offer_table.blockSignals(False)
            self._loading_offers = False

    def _reload_options(self) -> None:
        rows = self.service.available_option_rows()
        keys = {key for row in rows for key in row}
        leading = [key for key in ("optionId", "optionName") if key in keys]
        columns = leading + sorted(keys.difference(leading), key=str.casefold)
        self.options_table.setColumnCount(len(columns))
        self.options_table.setHorizontalHeaderLabels(columns)
        self.options_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(columns):
                value = row.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                self.options_table.setItem(row_index, column, QTableWidgetItem(str(value)))
        if rows and columns:
            self.options_table.resizeColumnsToContents()
            for column in range(self.options_table.columnCount()):
                self.options_table.setColumnWidth(
                    column, min(max(self.options_table.columnWidth(column), 90), 360)
                )

    def _offer_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading_offers or item.column() != 4:
            return
        id_item = self.offer_table.item(item.row(), 0)
        if id_item is None:
            return
        offer_id = str(id_item.data(Qt.ItemDataRole.UserRole) or id_item.text())
        try:
            self.service.set_offer_note(offer_id, item.text())
        except (ValueError, sqlite3.Error) as exc:
            QMessageBox.warning(self, "База оферов", str(exc))
            self._reload_offers()
            return
        self._reload_accounts()

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

    def _selected_ids(self, action_name: str) -> list[int]:
        ids = self.table.selected_account_ids()
        if not ids:
            QMessageBox.information(self, action_name, "Выделите хотя бы одну строку аккаунта.")
        return ids

    def _delete_selected(self) -> None:
        ids = self._selected_ids("Удаление номера")
        if not ids:
            return
        if len(ids) != 1:
            QMessageBox.information(
                self,
                "Удаление номера",
                "Для удаления выделите одну строку аккаунта.",
            )
            return
        account_id = ids[0]
        try:
            account = self.service.db.get_account(account_id)
        except KeyError:
            self.reload()
            return
        answer = QMessageBox.question(
            self,
            "Удаление номера",
            f"Удалить номер {account.phone} и его сохранённую авторизацию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_account(account_id)
        except (OSError, sqlite3.Error, KeyError) as exc:
            QMessageBox.critical(self, "Не удалось удалить номер", str(exc))
            return
        self.reload()

    def _solve_captcha(self, image_bytes: bytes) -> str | None:
        self.status_label.setText("Требуется CAPTCHA")
        QApplication.processEvents()
        try:
            return CaptchaDialog.solve(image_bytes, self)
        except ValueError as exc:
            QMessageBox.critical(self, "CAPTCHA", str(exc))
            return None

    def _set_busy(self, enabled: bool) -> None:
        for widget in (
            self.add_button,
            self.refresh_selected_button,
            self.delete_button,
            self.block_button,
            self.unblock_button,
            self.settings_button,
            self.tabs,
        ):
            widget.setEnabled(not enabled)

    def _refresh_ids(self, ids: list[int]) -> None:
        failures: list[str] = []
        self._set_busy(True)
        try:
            for index, account_id in enumerate(ids, start=1):
                self.status_label.setText(f"Обновление {index}/{len(ids)}")
                QApplication.processEvents()
                result = self.service.refresh(account_id, self._solve_captcha)
                if result.snapshot is None:
                    detail = result.account.last_error or "неизвестная ошибка"
                    failures.append(f"{result.account.phone}: {detail}")
        finally:
            self._set_busy(False)
            self.reload()
        if failures:
            self.status_label.setText("Готово с ошибками")
            QMessageBox.warning(self, "Обновление не завершено", "\n".join(failures))
        else:
            self.status_label.setText("Готово")

    def _refresh_selected(self) -> None:
        ids = self._selected_ids("Обновление")
        if ids:
            self._refresh_ids(ids)

    def _set_blocking_selected(self, enabled: bool) -> None:
        title = "Установить блокировку" if enabled else "Снять блокировку"
        ids = self._selected_ids(title)
        if not ids:
            return
        failures: list[str] = []
        self._set_busy(True)
        try:
            for index, account_id in enumerate(ids, start=1):
                self.status_label.setText(f"{title}: {index}/{len(ids)}")
                QApplication.processEvents()
                account, result = self.service.set_blocking(
                    account_id,
                    enabled,
                    self._solve_captcha,
                )
                if result is None:
                    detail = account.last_error or "неизвестная ошибка"
                    failures.append(f"{account.phone}: {detail}")
        finally:
            self._set_busy(False)
            self.reload()
        if failures:
            self.status_label.setText("Готово с ошибками")
            QMessageBox.warning(self, title, "\n".join(failures))
        else:
            self.status_label.setText("Готово")

    def _rows_reordered(self, account_ids: list[int]) -> None:
        try:
            self.service.set_account_order(account_ids)
        except (ValueError, sqlite3.Error) as exc:
            QMessageBox.warning(self, "Порядок строк", str(exc))
        self._reload_accounts()
