"""Servicio de inferencia fuera del hilo gráfico (RF-06, RF-10, RNF-02).

``InferenceWorker`` es un ``QThread`` con cola de trabajos. Carga el modelo una sola vez y atiende
una solicitud a la vez. El análisis se divide en bloques para informar progreso y
permitir cancelar entre bloques; una ejecución cancelada no entrega resultados parciales.
"""
from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path

# RNF-02: la inferencia nunca consulta Hugging Face ni otra red. Debe definirse antes de
# importar transformers.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from PySide6.QtCore import QThread, Signal  # noqa: E402

from .core.integrity import IntegrityReport, verify_bundle  # noqa: E402
from .core.results import SCORE_FLOOR  # noqa: E402

CHUNK_SIZE = 8  # Proteínas por bloque entre comprobaciones de cancelación.


class PackageError(RuntimeError):
    """El paquete de modelo no supera la verificación."""


@dataclass
class LoadedModel:
    predictor: object
    report: IntegrityReport
    load_seconds: float
    device: str


def load_predictor(bundle_dir: Path, device: str = "cpu") -> LoadedModel:
    """Verifica y carga el paquete. Lanza PackageError con un mensaje comprensible."""
    start = time.perf_counter()
    report = verify_bundle(bundle_dir)
    if not report.ok:
        details = "\n".join(f"• {c.label}: {c.detail}" for c in report.errors)
        raise PackageError(f"El paquete de modelo no es válido:\n{details}")

    try:
        import transformers

        transformers.utils.logging.set_verbosity_error()
        transformers.utils.logging.disable_progress_bar()
    except Exception:  # pragma: no cover - solo afecta a los mensajes de consola
        pass

    from .inference.protein_go import ProteinGOPredictor

    try:
        predictor = ProteinGOPredictor(bundle_dir, device=device)
    except RuntimeError as exc:
        # load_state_dict(strict=True) falla si las dimensiones de los pesos no
        # corresponden al vocabulario o al backbone del manifiesto.
        report.add("Dimensiones de pesos ↔ vocabulario", False, str(exc).splitlines()[0])
        raise PackageError("Los pesos no corresponden al vocabulario o al backbone del "
                           f"manifiesto (versiones mezcladas).\n{exc}") from exc
    except (OSError, ValueError) as exc:
        report.add("Carga del modelo", False, str(exc).splitlines()[0])
        raise PackageError(f"No se pudo cargar el modelo: {exc}") from exc

    n_classes = len(predictor.classes)
    head = getattr(predictor.model, "head", None)
    out_features = getattr(head[-1], "out_features", None) if head is not None else None
    report.add("Dimensiones de pesos ↔ vocabulario",
               out_features in (None, n_classes),
               f"salida del clasificador = {out_features or n_classes}, vocabulario = {n_classes}")
    return LoadedModel(predictor, report, time.perf_counter() - start, device)


def run_prediction(predictor, records, cancel: threading.Event | None = None,
                   progress=None, chunk_size: int = CHUNK_SIZE):
    """Ejecuta ``predict_records`` por bloques. Devuelve None si se canceló."""
    results = []
    total = len(records)
    for start in range(0, total, chunk_size):
        if cancel is not None and cancel.is_set():
            return None
        results.extend(predictor.predict_records(records[start:start + chunk_size],
                                                 threshold=SCORE_FLOOR))
        if progress is not None:
            progress(min(start + chunk_size, total), total)
    if cancel is not None and cancel.is_set():
        return None
    return results


class InferenceWorker(QThread):
    """Hilo de inferencia con cola de trabajos propia.

    Todo el trabajo (carga y predicción) ocurre dentro de ``run`` en un único hilo, y la
    interfaz se comunica con él mediante una ``queue.Queue``. Se evita invocar slots en el
    hilo mediante señales encoladas: con PySide6 6.12 + Python 3.13 eso provocó un fallo
    fatal del intérprete (_PyThreadState_Attach) al ejecutar PyTorch.
    Las señales se emiten desde este hilo y llegan encoladas al hilo gráfico.
    """

    loading = Signal()
    loaded = Signal(object)            # LoadedModel
    load_failed = Signal(str, object)  # mensaje, IntegrityReport | None
    progress = Signal(int, int)        # hechas, total
    finished = Signal(object, float)   # lista de resultados, segundos
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, bundle_dir: Path, device: str = "cpu", parent=None):
        super().__init__(parent)
        self.setObjectName("InferenceThread")
        self.bundle_dir = Path(bundle_dir)
        self.device = device
        self.model: LoadedModel | None = None
        self.load_count = 0
        self._cancel = threading.Event()
        self._jobs: queue.Queue = queue.Queue()

    # --- API para el hilo gráfico (no bloqueante)
    def request_load(self) -> None:
        self._jobs.put(("load", None))

    def request_predict(self, records) -> None:
        self._cancel.clear()
        self._jobs.put(("predict", list(records)))

    def request_cancel(self) -> None:
        self._cancel.set()

    def stop(self, timeout_ms: int = 30000) -> None:
        self._cancel.set()
        self._jobs.put(("stop", None))
        self.wait(timeout_ms)

    # --- hilo de trabajo
    def run(self) -> None:  # noqa: D401 - QThread API
        while True:
            kind, payload = self._jobs.get()
            if kind == "stop":
                return
            if kind == "load":
                self._load()
            elif kind == "predict":
                self._predict(payload)

    def _load(self) -> None:
        if self.model is not None:
            self.loaded.emit(self.model)
            return
        self.loading.emit()
        try:
            self.model = load_predictor(self.bundle_dir, self.device)
            self.load_count += 1
        except PackageError as exc:
            self.load_failed.emit(str(exc), verify_bundle(self.bundle_dir))
            return
        except Exception as exc:  # noqa: BLE001 - mostrar cualquier fallo al usuario
            self.load_failed.emit(f"Error inesperado al cargar el modelo: {exc}", None)
            return
        self.loaded.emit(self.model)

    def _predict(self, records) -> None:
        if self.model is None:
            self.failed.emit("El modelo todavía no está cargado.")
            return
        start = time.perf_counter()
        try:
            results = run_prediction(self.model.predictor, records, self._cancel,
                                     lambda done, total: self.progress.emit(done, total))
        except MemoryError:
            self.failed.emit("Memoria insuficiente. Prueba con menos proteínas por archivo.")
            return
        except ValueError as exc:
            self.failed.emit(f"Entrada rechazada por el modelo: {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            if "out of memory" in message.lower():
                message = "Memoria insuficiente. Prueba con menos proteínas por archivo."
            self.failed.emit(f"Error durante la inferencia: {message}")
            return
        if results is None:
            self.cancelled.emit()
        else:
            self.finished.emit(results, time.perf_counter() - start)
