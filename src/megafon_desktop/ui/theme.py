from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


class ThemeController:
    """Apply one app-wide palette so current and future standard widgets inherit the theme."""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.system_style_name = app.style().objectName()
        self.current = "system"
        hints = app.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._system_scheme_changed)

    def apply(self, theme: str) -> None:
        if theme not in {"system", "light", "dark"}:
            theme = "system"
        self.current = theme
        hints = self.app.styleHints()

        if theme == "system":
            if hasattr(hints, "unsetColorScheme"):
                hints.unsetColorScheme()
            style = QStyleFactory.create(self.system_style_name)
            if style is not None:
                self.app.setStyle(style)
            self.app.setPalette(QPalette())
            return

        scheme = Qt.ColorScheme.Light if theme == "light" else Qt.ColorScheme.Dark
        if hasattr(hints, "setColorScheme"):
            hints.setColorScheme(scheme)
        fusion = QStyleFactory.create("Fusion")
        if fusion is not None:
            self.app.setStyle(fusion)
        self.app.setPalette(self._light_palette() if theme == "light" else self._dark_palette())

    def _system_scheme_changed(self, _scheme: Qt.ColorScheme) -> None:
        if self.current == "system":
            self.app.setPalette(QPalette())

    @staticmethod
    def _light_palette() -> QPalette:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(24, 24, 24))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(247, 247, 247))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 225))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(24, 24, 24))
        palette.setColor(QPalette.ColorRole.Text, QColor(24, 24, 24))
        palette.setColor(QPalette.ColorRole.Button, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(24, 24, 24))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(180, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 92, 180))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(48, 114, 190))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(110, 110, 110))
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(140, 140, 140)
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(140, 140, 140)
        )
        return palette

    @staticmethod
    def _dark_palette() -> QPalette:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(238, 238, 238))
        palette.setColor(QPalette.ColorRole.Base, QColor(22, 22, 22))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(36, 36, 36))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(48, 48, 48))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.Text, QColor(238, 238, 238))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(238, 238, 238))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 110, 110))
        palette.setColor(QPalette.ColorRole.Link, QColor(104, 170, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(65, 115, 175))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(155, 155, 155))
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(115, 115, 115)
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(115, 115, 115)
        )
        return palette
