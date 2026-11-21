"""Modelo de tabla, delegados (insignia de aspecto, barra de puntaje) y piezas reutilizables."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QStyle, QStyledItemDelegate,
                               QStyleOptionViewItem, QVBoxLayout, QWidget)

from ..core.results import Row
from . import theme

COL_PROTEIN, COL_TERM, COL_NAME, COL_ASPECT, COL_ORIGIN, COL_SCORE = range(6)
HEADERS = ["Proteína", "Término GO", "Nombre", "Aspecto", "Origen", "Puntuación"]
ROW_ROLE = Qt.UserRole + 1


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[Row] = []

    def set_rows(self, rows: list[Row]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_at(self, index: int) -> Row | None:
        return self._rows[index] if 0 <= index < len(self._rows) else None

    def rowCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return HEADERS[section]
        if orientation == Qt.Horizontal and role == Qt.ToolTipRole and section == COL_SCORE:
            return "Salida sigmoid con propagación GO. No es una probabilidad calibrada."
        if orientation == Qt.Horizontal and role == Qt.ToolTipRole and section == COL_ORIGIN:
            return "Directo: puntaje del propio término. Propagado: heredado de un término más específico."
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == ROW_ROLE:
            return row
        if role == Qt.DisplayRole:
            return [row.protein_id, row.go_term, row.name, row.aspect,
                    theme.ORIGIN_LABELS.get(row.origin, row.origin), theme.num(row.score)][col]
        if role == Qt.UserRole:  # Valor para ordenar.
            return [row.protein_id, row.go_term, row.name.lower(), row.aspect, row.origin, row.score][col]
        if role == Qt.ToolTipRole:
            if col == COL_ASPECT:
                return theme.ASPECT_NAMES.get(row.aspect, row.aspect)
            if col == COL_SCORE:
                text = f"Puntuación {theme.num(row.score, 4)}"
                if row.origin == "propagated":
                    text += f" (propagada; directa {theme.num(row.direct_score, 4)})"
                return text
            if col == COL_NAME:
                return row.name
        if role == Qt.AccessibleTextRole:
            return f"{HEADERS[col]}: {self.data(index, Qt.DisplayRole)}"
        if role == Qt.ForegroundRole and col == COL_ORIGIN and row.origin == "propagated":
            return QBrush(QColor(theme.MUTED))
        if role == Qt.FontRole and col in (COL_PROTEIN, COL_TERM):
            font = QFont()
            font.setFamilies(["Consolas", "DejaVu Sans Mono", "monospace"])
            return font
        return None


class AspectBadgeDelegate(QStyledItemDelegate):
    """Insignia de color MF / BP / CC como en la maqueta."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        self.initStyleOption(option, index)
        option.text = ""
        option.widget.style().drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)
        aspect = index.data(Qt.DisplayRole) or ""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = 46, 22
        rect = QRectF(option.rect.center().x() - w / 2, option.rect.center().y() - h / 2, w, h)
        painter.setBrush(QColor(theme.ASPECT_COLORS.get(aspect, theme.MUTED)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)
        font = QFont(option.font)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(rect, Qt.AlignCenter, aspect)
        painter.restore()

    def sizeHint(self, option, index):  # noqa: N802
        return QSize(70, 34)


class ScoreBarDelegate(QStyledItemDelegate):
    """Barra turquesa + valor numérico (el número mantiene la información accesible)."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        self.initStyleOption(option, index)
        option.text = ""
        option.widget.style().drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)
        row: Row = index.data(ROW_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        text_w = 46
        bar = QRectF(option.rect.left() + 8, option.rect.center().y() - 5,
                     max(20, option.rect.width() - text_w - 18), 10)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(theme.TRACK))
        painter.drawRoundedRect(bar, 5, 5)
        filled = QRectF(bar)
        filled.setWidth(max(4.0, bar.width() * max(0.0, min(1.0, row.score))))
        painter.setBrush(QColor(theme.TEAL if row.origin == "direct" else "#5FBEC6"))
        painter.drawRoundedRect(filled, 5, 5)
        painter.setPen(QPen(QColor(theme.TEXT)))
        text_rect = QRectF(bar.right() + 6, option.rect.top(), text_w, option.rect.height())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, theme.num(row.score))
        painter.restore()

    def sizeHint(self, option, index):  # noqa: N802
        return QSize(170, 34)


class Card(QFrame):
    def __init__(self, parent=None, margins=(16, 16, 16, 16), spacing=10):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(*margins)
        self.body.setSpacing(spacing)


class Banner(QFrame):
    """Aviso en línea: info / warning / error."""

    def __init__(self, kind="info", text="", parent=None):
        super().__init__(parent)
        self.setObjectName("Banner")
        self.setProperty("kind", kind)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setStyleSheet("color: inherit; background: transparent;")
        layout.addWidget(self.label)

    def set(self, kind: str, text: str) -> None:
        self.setProperty("kind", kind)
        self.style().unpolish(self)
        self.style().polish(self)
        self.label.setText(text)
        self.setVisible(bool(text))


def section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionLabel")
    return label


def muted(text: str, wrap=True) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Muted")
    label.setWordWrap(wrap)
    return label


def hbox(*widgets, spacing=8, margins=(0, 0, 0, 0)) -> QWidget:
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    for item in widgets:
        if item is None:
            layout.addStretch(1)
        else:
            layout.addWidget(item)
    return w
