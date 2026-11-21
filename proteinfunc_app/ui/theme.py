"""Paleta y hoja de estilos basadas en la maqueta de la diapositiva 18."""
from __future__ import annotations

from PySide6.QtWidgets import QProxyStyle, QSlider, QStyle

BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
TEAL = "#0E9AA7"
TEAL_DARK = "#0B7F8A"
NAVY = "#13294B"
NAVY_DARK = "#0C1D38"
PAGE = "#EEF4FB"
SURFACE = "#FFFFFF"
PANEL = "#F3F6FB"
ROW_ALT = "#F7F9FD"
HEADER_ROW = "#DCE8F8"
BORDER = "#C8D5E6"
TEXT = "#13294B"
MUTED = "#5B6B82"
TRACK = "#E3E9F2"
WARN = "#9A4A06"
WARN_BG = "#FEF3E2"
WARN_BORDER = "#F5C77E"
ERROR = "#B42318"
ERROR_BG = "#FDECEC"
ERROR_BORDER = "#F3B4AE"
OK_BG = "#E6F6F7"

ASPECT_COLORS = {"MF": BLUE, "BP": TEAL, "CC": NAVY}
ASPECT_NAMES = {"MF": "Función molecular", "BP": "Proceso biológico", "CC": "Componente celular"}
ORIGIN_LABELS = {"direct": "Directo", "propagated": "Propagado"}

FONT_FAMILY = "Segoe UI"  # Windows; Qt usa una fuente equivalente en Linux.

STYLESHEET = f"""
QWidget {{
    color: {TEXT};
    font-size: 10pt;
}}
QMainWindow, QDialog {{ background: {PAGE}; }}

/* Barra superior como en la maqueta */
#HeaderBar {{ background: {NAVY}; }}
#HeaderTitle {{ color: white; font-size: 13pt; font-weight: 600; }}
#HeaderSubtitle {{ color: #AFC2DD; font-size: 9pt; }}
#HeaderButton {{
    color: white; background: transparent; border: 1px solid #3A5277;
    border-radius: 6px; padding: 5px 12px;
}}
#HeaderButton:hover {{ background: #1E3A64; }}
#HeaderButton:focus {{ border-color: #8FB3F5; }}
#ModelChip {{
    color: white; background: #1E3A64; border-radius: 10px; padding: 3px 10px; font-size: 9pt;
}}
#ModelChip[state="ok"] {{ background: {TEAL_DARK}; }}
#ModelChip[state="error"] {{ background: {ERROR}; }}

/* Tarjetas */
#Card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
#SectionLabel {{ color: {MUTED}; font-size: 9pt; }}
#Muted {{ color: {MUTED}; }}
#Title {{ font-size: 12pt; font-weight: 600; }}

/* Botones */
QPushButton {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 7px;
    padding: 7px 14px; min-height: 18px;
}}
QPushButton:hover {{ background: {PANEL}; }}
QPushButton:focus {{ border: 2px solid {BLUE}; }}
QPushButton:disabled {{ color: #9AA8BC; background: {PANEL}; border-color: {TRACK}; }}
QPushButton#Primary {{
    background: {BLUE}; color: white; border: none; font-weight: 600; padding: 10px 14px;
}}
QPushButton#Primary:hover {{ background: {BLUE_DARK}; }}
QPushButton#Primary:focus {{ border: 2px solid {NAVY}; }}
QPushButton#Primary:disabled {{ background: #9DB7EE; color: #EEF3FD; }}
QPushButton#Accent {{
    background: {TEAL}; color: white; border: none; font-weight: 600; padding: 9px 22px;
}}
QPushButton#Accent:hover {{ background: {TEAL_DARK}; }}
QPushButton#Accent:focus {{ border: 2px solid {NAVY}; }}
QPushButton#Accent:disabled {{ background: #9CCFD4; color: #F1FAFB; }}
QPushButton#Link {{
    background: transparent; border: none; color: {BLUE}; padding: 0; text-decoration: underline;
}}
QPushButton#Link:focus {{ border: 1px dotted {BLUE}; }}

/* Filtros MF / BP / CC */
QPushButton#AspectToggle {{
    font-weight: 600; border-radius: 8px; padding: 6px 0; min-width: 52px;
    background: {SURFACE}; color: {MUTED}; border: 1px dashed {BORDER};
}}
QPushButton#AspectToggle[aspect="MF"]:checked {{ background: {BLUE}; color: white; border: none; }}
QPushButton#AspectToggle[aspect="BP"]:checked {{ background: {TEAL}; color: white; border: none; }}
QPushButton#AspectToggle[aspect="CC"]:checked {{ background: {NAVY}; color: white; border: none; }}
QPushButton#AspectToggle:focus {{ border: 2px solid {BLUE_DARK}; }}

/* Campos */
QLineEdit, QPlainTextEdit, QComboBox, QDateEdit {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 7px; padding: 6px 8px;
    selection-background-color: {BLUE};
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 2px solid {BLUE}; }}
QLineEdit#FileField {{ qproperty-alignment: AlignCenter; color: {MUTED}; }}
QPlainTextEdit {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 9pt; }}

/* Progreso */
QProgressBar {{
    background: {TRACK}; border: none; border-radius: 6px; height: 12px; text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background: {TEAL}; border-radius: 6px; }}

/* Deslizador de umbral */
QSlider {{ background: transparent; border: none; min-height: 24px; }}
QSlider:focus {{ background: #E3ECFC; border-radius: 6px; }}
QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {BLUE}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {BLUE}; width: 18px; height: 18px; margin: -8px 0; border-radius: 9px;
    border: 2px solid white;
}}

/* Tabla */
QTableView {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    gridline-color: transparent; alternate-background-color: {ROW_ALT};
    selection-background-color: #D6E4FB; selection-color: {TEXT};
}}
QTableView:focus {{ border: 2px solid {BLUE}; }}
QHeaderView::section {{
    background: {HEADER_ROW}; color: {TEXT}; font-weight: 600; border: none;
    padding: 9px 8px;
}}
QTableCornerButton::section {{ background: {HEADER_ROW}; border: none; }}

/* Avisos */
#Banner {{ border-radius: 8px; padding: 8px 10px; }}
#Banner[kind="warning"] {{ background: {WARN_BG}; border: 1px solid {WARN_BORDER}; color: {WARN}; }}
#Banner[kind="error"] {{ background: {ERROR_BG}; border: 1px solid {ERROR_BORDER}; color: {ERROR}; }}
#Banner[kind="info"] {{ background: {OK_BG}; border: 1px solid #A7DDE2; color: {TEAL_DARK}; }}

QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; color: {MUTED}; }}
QStatusBar QLabel {{ color: {MUTED}; padding: 0 8px; }}
QSplitter::handle {{ background: transparent; }}
QToolTip {{ background: {NAVY}; color: white; border: none; padding: 5px; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE}; }}
QTabBar::tab {{ padding: 7px 14px; background: {PANEL}; border: 1px solid {BORDER};
    border-bottom: none; border-top-left-radius: 7px; border-top-right-radius: 7px; margin-right: 2px; }}
QTabBar::tab:selected {{ background: {SURFACE}; color: {BLUE}; font-weight: 600; }}
QRadioButton, QCheckBox {{ spacing: 8px; }}
"""


def num(value: float, digits: int = 3) -> str:
    """Número con coma decimal para la interfaz en español (las exportaciones usan punto)."""
    return f"{value:.{digits}f}".replace(".", ",")


class AppStyle(QProxyStyle):
    """Fusion sin el recuadro de foco genérico del deslizador: el foco se indica con el
    borde del tirador (ver STYLESHEET), que es más visible y coherente con la maqueta."""

    def __init__(self):
        super().__init__("Fusion")

    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: N802
        if element == QStyle.PE_FrameFocusRect and isinstance(widget, QSlider):
            return
        super().drawPrimitive(element, option, painter, widget)
