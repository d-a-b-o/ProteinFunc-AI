"""Recolección de basura solo en el hilo gráfico.

El recolector automático de Python se ejecuta en el hilo que esté reservando memoria en
ese momento. Si es el hilo de inferencia y entre la basura hay objetos de Qt, Qt los
destruye fuera del hilo gráfico y el proceso termina con un fallo de segmentación. Se
desactiva el recolector automático y se ejecuta periódicamente desde el hilo gráfico
(mismo enfoque que pyqtgraph.util.garbage_collector).
"""
from __future__ import annotations

import gc

from PySide6.QtCore import QObject, QTimer


class GarbageCollector(QObject):
    def __init__(self, parent=None, interval_ms: int = 1000):
        super().__init__(parent)
        self.threshold = gc.get_threshold()
        gc.disable()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check)
        self.timer.start(interval_ms)

    def check(self) -> None:
        l0, l1, l2 = gc.get_count()
        if l0 > self.threshold[0]:
            gen = 0
            if l1 > self.threshold[1]:
                gen = 1
                if l2 > self.threshold[2]:
                    gen = 2
            gc.collect(gen)
