from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


def make_app_icon(size: int = 256) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = size * 0.06
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#00B956"))
    painter.drawRoundedRect(
        QRectF(margin, margin, size - 2 * margin, size - 2 * margin),
        size * 0.20,
        size * 0.20,
    )

    painter.setBrush(QColor("#6E35C8"))
    dot = size * 0.18
    painter.drawEllipse(QRectF(size * 0.69, size * 0.13, dot, dot))

    painter.setPen(QColor("white"))
    font = QFont("Segoe UI")
    font.setBold(True)
    font.setPixelSize(int(size * 0.52))
    painter.setFont(font)
    painter.drawText(
        QRectF(0, size * 0.03, size, size * 0.94),
        Qt.AlignmentFlag.AlignCenter,
        "M",
    )
    painter.end()
    return QIcon(pixmap)
