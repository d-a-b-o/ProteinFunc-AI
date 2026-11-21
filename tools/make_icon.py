"""Genera el icono de la app (doble hélice con los colores de la maqueta).
    python tools/make_icon.py   ->  proteinfunc_app/icon.png e installer/icon.ico
"""
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIZE = 512
app = QGuiApplication(sys.argv[:1])
img = QImage(SIZE, SIZE, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
p.setBrush(QColor("#13294B"))
p.setPen(Qt.NoPen)
p.drawRoundedRect(QRectF(16, 16, SIZE - 32, SIZE - 32), 110, 110)

top, bottom, cx, amp = 92, SIZE - 92, SIZE / 2, 118


def strand(phase):
    path = QPainterPath()
    for i in range(0, 201):
        y = top + (bottom - top) * i / 200
        x = cx + amp * math.sin(2 * math.pi * 1.25 * i / 200 + phase)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    return path


p.setPen(QPen(QColor("#8FB3F5"), 10, Qt.SolidLine, Qt.RoundCap))
for k in range(1, 12):
    t = k / 12
    y = top + (bottom - top) * t
    a = cx + amp * math.sin(2 * math.pi * 1.25 * t)
    b = cx + amp * math.sin(2 * math.pi * 1.25 * t + math.pi)
    if abs(a - b) > 30:
        p.drawLine(QPointF(a, y), QPointF(b, y))
for color, phase in (("#0E9AA7", math.pi), ("#2563EB", 0.0)):
    p.setPen(QPen(QColor(color), 34, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawPath(strand(phase))
p.end()

png = ROOT / "proteinfunc_app" / "icon.png"
img.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(str(png))
try:
    from PIL import Image

    Image.open(png).save(ROOT / "installer" / "icon.ico",
                         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
except ImportError:
    print("Pillow no está instalado: no se generó icon.ico")
print(png)
