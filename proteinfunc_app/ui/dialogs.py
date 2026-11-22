"""Diálogos: validación de entrada, paquete del modelo, historial y exportación."""
from __future__ import annotations

import html
import importlib.metadata as md
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDateEdit, QSpinBox,
                               QPlainTextEdit, QFormLayout,
                               QDialog, QDialogButtonBox, QFileDialog, QGridLayout, QHBoxLayout,
                               QHeaderView, QLabel, QMessageBox, QPushButton, QRadioButton,
                               QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from ..core.history import COMPLETED, STATUS_LABELS, History, RunSummary
from ..core.integrity import IntegrityReport
from ..core.results import ViewFilter
from .. import APP_NAME, __version__
from ..core.perf import cpu_count
from ..core.validation import ERROR, WARNING, ValidationReport
from ..paths import resource_root
from . import theme
from .widgets import Banner, Card, hbox, muted, section_label


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setAlternatingRowColors(True)
    table.setWordWrap(True)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _item(text, color: str | None = None, tooltip: str | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    if color:
        item.setForeground(QColor(color))
    if tooltip:
        item.setToolTip(tooltip)
    return item


# --------------------------------------------------------------------------- validación
class ValidationDialog(QDialog):
    """Lista todos los registros con su estado (RF-02). Permite analizar solo los válidos."""

    def __init__(self, report: ValidationReport, source_name: str, parent=None, allow_run=True):
        super().__init__(parent)
        self.setWindowTitle("Validación de la entrada")
        self.resize(820, 480)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(f"<b>{html.escape(source_name)}</b> — {html.escape(report.summary())}")
        title.setObjectName("Title")
        layout.addWidget(title)

        banner = Banner()
        if report.global_errors:
            banner.set("error", "<br>".join(html.escape(e) for e in report.global_errors))
        elif report.rejected:
            banner.set("error", f"{len(report.rejected)} registro(s) no se analizarán. Corrige el archivo y "
                                 "vuelve a cargarlo, o continúa solo con los registros válidos.")
        elif report.warnings:
            banner.set("warning", "Hay avisos, pero todos los registros pueden analizarse.")
        else:
            banner.set("info", "Todos los registros son válidos.")
        layout.addWidget(banner)

        table = _table(["#", "Línea", "Identificador", "Longitud", "Estado", "Detalle"])
        table.setRowCount(len(report.records))
        labels = {ERROR: ("Error", theme.ERROR), WARNING: ("Aviso", theme.WARN), "ok": ("Válido", theme.TEAL_DARK)}
        for i, r in enumerate(report.records):
            text, color = labels[r.status]
            table.setItem(i, 0, _item(r.index))
            table.setItem(i, 1, _item(r.line))
            table.setItem(i, 2, _item(r.record_id or "(vacío)", tooltip=r.header))
            table.setItem(i, 3, _item(r.length))
            table.setItem(i, 4, _item(text, color))
            table.setItem(i, 5, _item(" ".join(r.messages) or "—"))
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        table.resizeRowsToContents()
        layout.addWidget(table, 1)

        buttons = QDialogButtonBox()
        n_ok = len(report.accepted)
        self.run_button = None
        if allow_run and n_ok and not report.is_clean:
            self.run_button = buttons.addButton(f"Analizar {n_ok} válido{'s' if n_ok != 1 else ''}",
                                                QDialogButtonBox.AcceptRole)
            self.run_button.setObjectName("Primary")
            buttons.addButton("Volver y corregir", QDialogButtonBox.RejectRole)
        else:
            buttons.addButton("Cerrar", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# --------------------------------------------------------------------- paquete del modelo
def _installed(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


class PackageDialog(QDialog):
    """Manifiesto, verificaciones, huellas SHA-256 y métricas del paquete (RF-06, RNF-06)."""

    def __init__(self, report: IntegrityReport, load_info: dict | None = None, parent=None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Paquete del modelo")
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        m = report.manifest or {}
        spec = m.get("model_spec", {})

        state = "info" if report.ok else "error"
        text = ("Paquete verificado: los archivos y el manifiesto son coherentes." if report.ok else
                "El paquete no supera la verificación. El análisis está deshabilitado.")
        if report.ok and not report.has_checksum_file:
            state, text = "warning", text + " No hay SHA256SUMS: las huellas se muestran pero no se comparan."
        banner = Banner(state, text)
        layout.addWidget(banner)

        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        # --- Resumen
        summary = QWidget()
        grid = QGridLayout(summary)
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        aspects = {}
        for term in m.get("classes", []):
            a = m.get("label_metadata", {}).get(term, {}).get("aspect", "?")
            aspects[a] = aspects.get(a, 0) + 1
        rows = [
            ("Carpeta", str(report.bundle_dir)),
            ("Huella del paquete (SHA-256)", report.fingerprint),
            ("Modelo", f"{spec.get('kind', '?')} · {spec.get('hf_model', '—')}"
                       + (" · backbone congelado" if spec.get("frozen_backbone") else "")),
            ("Vocabulario GO", f"{len(m.get('classes', []))} términos · "
                               + " · ".join(f"{k} {v}" for k, v in sorted(aspects.items()))),
            ("Umbral operativo", f"{m.get('threshold')} (elegido en validación)"),
            ("Longitud máxima", f"{m.get('max_length')} residuos · política: {m.get('long_sequence_policy', '—')}"),
            ("Mejor época", str(m.get("best_epoch", "—"))),
        ]
        if load_info:
            rows.append(("Carga", f"{load_info.get('seconds', 0):.1f} s en {load_info.get('device', 'cpu').upper()}"))
        ds = m.get("data_summary", {})
        if ds:
            parts = ds.get("partitions", {})
            rows.append(("Datos de entrenamiento",
                         f"{ds.get('selected_annotated_proteins', '?')} proteínas · "
                         + " / ".join(f"{k} {v.get('proteins')}" for k, v in parts.items())
                         + f" · agrupación: {ds.get('grouping', '—')}"))
            rows.append(("Alcance de métricas", ds.get("metrics_scope", "—")))
        for i, (k, v) in enumerate(rows):
            key = QLabel(k)
            key.setObjectName("Muted")
            val = QLabel(v)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(key, i, 0, Qt.AlignTop)
            grid.addWidget(val, i, 1)
        grid.setRowStretch(len(rows), 1)
        tabs.addTab(summary, "Resumen")

        # --- Verificaciones
        checks = _table(["Verificación", "Resultado", "Detalle"])
        checks.setRowCount(len(report.checks))
        for i, c in enumerate(report.checks):
            checks.setItem(i, 0, _item(c.label))
            checks.setItem(i, 1, _item("✓ Correcto" if c.ok else "✗ Falla",
                                       theme.TEAL_DARK if c.ok else theme.ERROR))
            checks.setItem(i, 2, _item(c.detail))
        checks.resizeColumnsToContents()
        tabs.addTab(checks, "Verificaciones")

        # --- Huellas
        files_tab = QWidget()
        fl = QVBoxLayout(files_tab)
        files = _table(["Archivo", "Tamaño", "SHA-256 calculado", "Esperado"])
        files.setRowCount(len(report.files))
        for i, f in enumerate(report.files):
            files.setItem(i, 0, _item(f.name))
            files.setItem(i, 1, _item(f"{f.size / 1024:,.0f} KB".replace(",", " ")))
            files.setItem(i, 2, _item(f.sha256))
            if f.matches is None:
                files.setItem(i, 3, _item("sin registro", theme.MUTED))
            else:
                files.setItem(i, 3, _item("✓ coincide" if f.matches else "✗ difiere",
                                          theme.TEAL_DARK if f.matches else theme.ERROR,
                                          tooltip=f.expected))
        files.resizeColumnsToContents()
        fl.addWidget(files)
        copy = QPushButton("Copiar huellas")
        copy.clicked.connect(self._copy_hashes)
        fl.addWidget(hbox(muted("Huellas calculadas al iniciar la aplicación."), None, copy))
        tabs.addTab(files_tab, "Huellas SHA-256")

        # --- Métricas de validación
        metrics = m.get("validation_metrics", {})
        if metrics:
            mt = _table(["Métrica", "Global", "MF", "BP", "CC"])
            names = [("micro_precision", "Precisión (micro)"), ("micro_recall", "Exhaustividad (micro)"),
                     ("micro_f1", "F1 (micro)")]
            mt.setRowCount(len(names) + 3)
            for i, (key, label) in enumerate(names):
                mt.setItem(i, 0, _item(label))
                mt.setItem(i, 1, _item(f"{metrics.get(key, float('nan')):.3f}"))
                for j, a in enumerate(("MF", "BP", "CC")):
                    value = metrics.get(f"{a}_{key}")
                    mt.setItem(i, 2 + j, _item("—" if value is None else f"{value:.3f}"))
            extra = [("macro_f1", "F1 (macro)"), ("micro_average_precision", "Precisión promedio (micro)"),
                     ("protein_f1", "F1 por proteína")]
            for k, (key, label) in enumerate(extra, start=len(names)):
                mt.setItem(k, 0, _item(label))
                mt.setItem(k, 1, _item(f"{metrics.get(key, float('nan')):.3f}"))
            mt.resizeColumnsToContents()
            box = QWidget()
            bl = QVBoxLayout(box)
            bl.addWidget(mt)
            bl.addWidget(muted("Métricas sobre la partición de validación y el vocabulario seleccionado; "
                               "no equivalen al puntaje oficial de CAFA."))
            tabs.addTab(box, "Métricas")

        # --- Versiones
        versions = m.get("package_versions", {})
        if versions:
            vt = _table(["Paquete", "Entrenamiento", "Instalado"])
            vt.setRowCount(len(versions))
            for i, (name, trained) in enumerate(sorted(versions.items())):
                inst = _installed(name)
                same = inst is not None and inst.split("+")[0] == str(trained).split("+")[0]
                vt.setItem(i, 0, _item(name))
                vt.setItem(i, 1, _item(trained))
                vt.setItem(i, 2, _item(inst or "no instalado (no requerido para inferir)" if name in
                                       ("pandas", "scikit-learn") else inst or "no instalado",
                                       None if same else theme.WARN))
            vt.resizeColumnsToContents()
            tabs.addTab(vt, "Versiones")

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)

    def _copy_hashes(self):
        text = "\n".join(f"{f.sha256}  {f.name}" for f in self.report.files)
        text += f"\n# huella del paquete: {self.report.fingerprint}\n"
        QGuiApplication.clipboard().setText(text)


# ------------------------------------------------------------------------------ historial
class HistoryDialog(QDialog):
    """Ejecuciones por fecha y versión del modelo (RF-11)."""

    def __init__(self, history: History, parent=None):
        super().__init__(parent)
        self.history = history
        self.selected_run_id: int | None = None
        self.setWindowTitle("Historial de ejecuciones")
        self.resize(980, 520)
        layout = QVBoxLayout(self)

        self.date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_to = QDateEdit(QDate.currentDate())
        for d in (self.date_from, self.date_to):
            d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy")
        self.version = QComboBox()
        self.status = QComboBox()
        self.status.addItem("Todos los estados", None)
        for key, label in STATUS_LABELS.items():
            self.status.addItem(label, key)
        self.all_dates = QCheckBox("Todas las fechas")
        self.all_dates.setChecked(True)
        filters = hbox(section_label("Desde"), self.date_from, section_label("Hasta"), self.date_to,
                       self.all_dates, section_label("Versión del modelo"), self.version,
                       self.status, None)
        layout.addWidget(filters)

        self.table = _table(["Fecha", "Origen", "Proteínas", "Estado", "Duración", "Proteínas/s",
                             "Memoria máx.", "Dispositivo", "Modelo", "Umbral", "App", "Mensaje"])
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(self._open)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self.table, 1)

        self.open_button = QPushButton("Abrir resultados")
        self.open_button.setObjectName("Primary")
        self.open_button.clicked.connect(self._open)
        self.delete_button = QPushButton("Eliminar")
        self.delete_button.clicked.connect(self._delete)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.reject)
        layout.addWidget(hbox(muted(f"Base de datos local: {history.db_path}"), None,
                              self.delete_button, self.open_button, close))

        self._runs: list[RunSummary] = []
        self._fill_versions()
        for w in (self.date_from, self.date_to):
            w.dateChanged.connect(self.refresh)
        self.all_dates.toggled.connect(self.refresh)
        self.version.currentIndexChanged.connect(self.refresh)
        self.status.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def _fill_versions(self):
        self.version.blockSignals(True)
        self.version.clear()
        self.version.addItem("Todas las versiones", None)
        for fp, kind in self.history.fingerprints():
            self.version.addItem(f"{kind} · {fp[:12]}", fp)
        self.version.blockSignals(False)

    def refresh(self):
        dated = not self.all_dates.isChecked()
        self.date_from.setEnabled(dated)
        self.date_to.setEnabled(dated)
        self._runs = self.history.list(
            date_from=self.date_from.date().toString("yyyy-MM-dd") if dated else None,
            date_to=self.date_to.date().toString("yyyy-MM-dd") if dated else None,
            fingerprint=self.version.currentData(), status=self.status.currentData())
        colors = {"completado": theme.TEAL_DARK, "cancelado": theme.WARN, "fallido": theme.ERROR}
        self.table.setRowCount(len(self._runs))
        for i, r in enumerate(self._runs):
            when = r.started_at.replace("T", " ")
            self.table.setItem(i, 0, _item(when))
            self.table.setItem(i, 1, _item(r.source_name))
            self.table.setItem(i, 2, _item(r.proteins if not r.rejected else f"{r.proteins} (+{r.rejected} rech.)"))
            self.table.setItem(i, 3, _item(r.status_label, colors.get(r.status)))
            perf = r.performance or {}
            self.table.setItem(i, 4, _item("—" if r.duration_s is None else f"{r.duration_s:.1f} s"))
            pps = perf.get("proteins_per_second")
            mem = perf.get("peak_memory_mb")
            self.table.setItem(i, 5, _item("—" if pps is None else theme.num(pps, 1)))
            self.table.setItem(i, 6, _item("—" if mem is None else f"{mem:.0f} MB",
                                           tooltip="Memoria residente máxima del proceso"))
            device = perf.get("device")
            self.table.setItem(i, 7, _item("—" if not device else
                                           f"{'GPU' if str(device).startswith('cuda') else 'CPU'}"
                                           + (f" · {perf['threads']} hilos" if perf.get("threads") else "")
                                           + (f" · lote {perf['chunk_size']}" if perf.get("chunk_size") else "")))
            self.table.setItem(i, 8, _item(f"{r.model_kind} · {r.model_fingerprint[:12]}",
                                           tooltip=r.model_fingerprint))
            self.table.setItem(i, 9, _item(r.model_threshold))
            self.table.setItem(i, 10, _item(r.app_version))
            self.table.setItem(i, 11, _item(r.message or ""))
        self.table.resizeColumnsToContents()
        self._update_buttons()

    def _current(self) -> RunSummary | None:
        rows = self.table.selectionModel().selectedRows()
        return self._runs[rows[0].row()] if rows else None

    def _update_buttons(self):
        run = self._current()
        self.open_button.setEnabled(bool(run and run.status == COMPLETED and run.has_results))
        self.delete_button.setEnabled(run is not None)

    def _open(self, *_):
        run = self._current()
        if run and run.status == COMPLETED and run.has_results:
            self.selected_run_id = run.id
            self.accept()

    def _delete(self):
        run = self._current()
        if run and QMessageBox.question(self, "Eliminar ejecución",
                                        f"¿Eliminar la ejecución del {run.started_at.replace('T', ' ')}?"
                                        ) == QMessageBox.Yes:
            self.history.delete(run.id)
            self._fill_versions()
            self.refresh()


# ----------------------------------------------------------------------------- exportación
class ExportDialog(QDialog):
    """CSV / TSV / JSON con los filtros actuales y metadatos de ejecución (RF-09)."""

    FORMATS = {"csv": "CSV (Excel, separado por comas)", "tsv": "TSV (separado por tabulaciones)",
               "json": "JSON (contrato completo: entrada, estados y truncamiento)"}

    def __init__(self, view: ViewFilter, n_rows: int, n_empty: int, default_dir: Path, source_stem: str,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar resultados")
        self.view = view
        self.default_dir = default_dir
        self.source_stem = source_stem
        self.path: Path | None = None
        self.fmt = "csv"
        layout = QVBoxLayout(self)

        card = Card()
        card.body.addWidget(section_label("Formato"))
        self.group = QButtonGroup(self)
        for key, label in self.FORMATS.items():
            rb = QRadioButton(label)
            rb.setProperty("fmt", key)
            rb.setChecked(key == "csv")
            self.group.addButton(rb)
            card.body.addWidget(rb)
        layout.addWidget(card)

        self.propagated = QCheckBox("Incluir términos propagados (ancestros GO)")
        self.propagated.setChecked(view.include_propagated)
        layout.addWidget(self.propagated)

        aspects = ", ".join(view.aspects) or "ninguno"
        protein = view.protein_id or "todas las proteínas"
        if view.specific_only:
            protein += ", solo términos específicos"
        layout.addWidget(muted(
            f"Se exportan los resultados visibles: umbral ≥ {theme.num(view.threshold, 2)}, aspectos {aspects}, "
            f"{protein}. {n_rows} fila(s); {n_empty} proteína(s) sin funciones sobre el umbral se "
            "incluyen indicando ese estado. El archivo registra versión de la app, huella del modelo y "
            "configuración."))

        buttons = QDialogButtonBox()
        save = buttons.addButton("Elegir ubicación y guardar…", QDialogButtonBox.AcceptRole)
        save.setObjectName("Accent")
        buttons.addButton("Cancelar", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._choose)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose(self):
        self.fmt = self.group.checkedButton().property("fmt")
        self.view.include_propagated = self.propagated.isChecked()
        suggested = self.default_dir / f"{self.source_stem}.predicciones.{self.fmt}"
        filters = {"csv": "CSV (*.csv)", "tsv": "TSV (*.tsv)", "json": "JSON (*.json)"}
        path, _ = QFileDialog.getSaveFileName(self, "Guardar resultados", str(suggested), filters[self.fmt])
        if not path:
            return
        path = Path(path)
        if path.suffix.lower() != f".{self.fmt}":
            path = path.with_name(path.name + f".{self.fmt}")
        self.path = path
        self.accept()


# --------------------------------------------------------------------------- preferencias
class PreferencesDialog(QDialog):
    """Dispositivo, tamaño de lote e hilos (límites configurables del documento, RNF-05)."""

    def __init__(self, devices: list[tuple[str, str]], device: str, chunk_size: int, threads: int | None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias")
        self.setMinimumSize(580, 460)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self.device_combo = QComboBox()
        for key, label in devices:
            self.device_combo.addItem(label, key)
        index = self.device_combo.findData(device)
        self.device_combo.setCurrentIndex(max(0, index))
        form.addRow("Dispositivo", self.device_combo)
        if len(devices) == 1:
            form.addRow("", muted("No se detectó una GPU compatible (CUDA). La CPU es suficiente para este modelo."))

        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(1, 64)
        self.chunk_spin.setValue(int(chunk_size))
        self.chunk_spin.setSuffix(" proteínas")
        form.addRow("Tamaño de lote", self.chunk_spin)
        form.addRow("", muted("Proteínas procesadas juntas. Lotes menores usan menos memoria y permiten "
                              "cancelar antes; lotes mayores pueden ser algo más rápidos."))

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(0, cpu_count())
        self.threads_spin.setValue(int(threads or 0))
        self.threads_spin.setSpecialValueText("Automático")
        form.addRow("Hilos de CPU", self.threads_spin)
        form.addRow("", muted(f"Este equipo tiene {cpu_count()} núcleos lógicos. Reduce el número si "
                              "quieres seguir usando el equipo con fluidez durante el análisis."))
        layout.addLayout(form)
        layout.addWidget(muted("La longitud máxima (residuos) y el umbral los fija el modelo entrenado; "
                               "cambiarlos rompería la consistencia con el notebook."))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def device(self) -> str:
        return self.device_combo.currentData()

    @property
    def chunk_size(self) -> int:
        return self.chunk_spin.value()

    @property
    def threads(self) -> int | None:
        return self.threads_spin.value() or None


# ------------------------------------------------------------------------------ acerca de
COMPONENTS = [
    ("PySide6 (Qt for Python)", "PySide6", "LGPL-3.0"),
    ("PyTorch", "torch", "BSD-3-Clause"),
    ("Transformers (Hugging Face)", "transformers", "Apache-2.0"),
    ("safetensors", "safetensors", "Apache-2.0"),
    ("NumPy", "numpy", "BSD-3-Clause"),
    ("ESM-2 esm2_t6_8M_UR50D (Meta AI)", None, "MIT"),
    ("Gene Ontology (nombres y relaciones de términos)", None, "CC BY 4.0"),
    ("Python", None, "PSF-2.0"),
]


class AboutDialog(QDialog):
    """Versión, cómo interpretar los resultados y licencias de terceros (RNF-10)."""

    def __init__(self, report=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de {APP_NAME}")
        self.resize(760, 560)
        layout = QVBoxLayout(self)
        title = QLabel(f"<b style='font-size:14pt'>{APP_NAME}</b> &nbsp; versión {__version__}")
        layout.addWidget(title)
        layout.addWidget(muted("Predicción local de funciones Gene Ontology (MF, BP, CC) a partir de secuencias de "
                               "proteínas. Proyecto del curso de Bioinformática, USIL."))
        if report is not None:
            layout.addWidget(muted(f"Huella del modelo (SHA-256): {report.fingerprint}"))

        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        guide = QLabel(
            "<p><b>MF</b> Función molecular · <b>BP</b> Proceso biológico · <b>CC</b> Componente celular. "
            "Una proteína puede tener varias funciones en cada aspecto.</p>"
            "<p><b>Puntuación</b>: salida sigmoid del modelo por término, ajustada por la jerarquía GO. "
            "<b>No es una probabilidad calibrada</b>: 0,80 no significa 80 % de certeza.</p>"
            "<p><b>Directo / Propagado</b>: un término propagado hereda el puntaje de un término más "
            "específico (relaciones <i>is_a</i> y <i>part_of</i>). «Solo términos específicos» oculta esos "
            "términos generales cuando ya se muestra uno más concreto.</p>"
            "<p><b>Umbral</b>: por defecto el elegido en validación. «Ninguna función superó el umbral» no "
            "implica que la proteína carezca de función.</p>"
            "<p><b>Límites</b>: solo se predicen los términos del vocabulario entrenado; las secuencias "
            "largas se truncan; el modelo asigna funciones incluso a secuencias sin sentido biológico "
            "(la app avisa de las de baja complejidad). Las predicciones son hipótesis computacionales "
            "y no sustituyen la validación experimental.</p>")
        guide.setWordWrap(True)
        guide.setTextFormat(Qt.RichText)
        guide.setAlignment(Qt.AlignTop)
        guide_box = QWidget()
        gl = QVBoxLayout(guide_box)
        gl.addWidget(guide)
        gl.addStretch(1)
        tabs.addTab(guide_box, "Cómo interpretar")

        comp = _table(["Componente", "Licencia", "Versión instalada"])
        comp.setRowCount(len(COMPONENTS))
        for i, (name, dist, license_) in enumerate(COMPONENTS):
            comp.setItem(i, 0, _item(name))
            comp.setItem(i, 1, _item(license_))
            comp.setItem(i, 2, _item((_installed(dist) or "—") if dist else "—"))
        comp.resizeColumnsToContents()
        comp_box = QWidget()
        cl = QVBoxLayout(comp_box)
        cl.addWidget(comp)
        cl.addWidget(muted("PySide6 se distribuye bajo LGPL-3.0 como librerías dinámicas reemplazables, junto "
                           "a la aplicación. Revisa las reglas de la competencia CAFA 6 (Kaggle) antes de "
                           "redistribuir artefactos derivados de sus datos."))
        tabs.addTab(comp_box, "Componentes y licencias")

        full = resource_root() / "THIRD_PARTY_LICENSES.txt"
        if full.is_file():
            text = QPlainTextEdit()
            text.setReadOnly(True)
            text.setPlainText(full.read_text(encoding="utf-8", errors="replace"))
            tabs.addTab(text, "Textos completos")

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.button(QDialogButtonBox.Close).setText("Cerrar")
        close.rejected.connect(self.reject)
        layout.addWidget(close)
