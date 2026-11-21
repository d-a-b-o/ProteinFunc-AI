"""Ventana principal, basada en la maqueta «ProteinFunc AI Desktop» (diapositiva 18)."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSortFilterProxyModel, Qt, QTimer
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton, QSlider, QSplitter,
                               QStackedWidget, QTableView, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..core.history import CANCELLED, COMPLETED, FAILED, History
from ..core.integrity import IntegrityReport, verify_bundle
from ..core.results import ALL_ASPECTS, SCORE_FLOOR, SCORE_NOTE, RunResult, ViewFilter
from ..core.validation import ValidationReport, read_input_file, validate_text
from ..services import InferenceWorker, LoadedModel
from . import theme
from .dialogs import ExportDialog, HistoryDialog, PackageDialog, ValidationDialog
from .widgets import (COL_ASPECT, COL_NAME, COL_SCORE, AspectBadgeDelegate, Banner, Card,
                      ResultsTableModel, ScoreBarDelegate, hbox, muted, section_label)


class MainWindow(QMainWindow):
    def __init__(self, bundle_dir: Path, history: History, device: str = "cpu"):
        super().__init__()
        self.bundle_dir = Path(bundle_dir)
        self.history = history
        self.model: LoadedModel | None = None
        self.report: IntegrityReport | None = None
        self.result: RunResult | None = None
        self.file_path: Path | None = None
        self.file_text: str | None = None
        self.validation: ValidationReport | None = None
        self.running = False
        self.run_id: int | None = None
        self._pending_input: tuple[str, str, ValidationReport] | None = None
        self.last_dir = Path.home()
        self.max_length = self._peek_max_length()

        self.setWindowTitle(APP_NAME)
        self.resize(1320, 820)
        self.setMinimumSize(1040, 640)
        self.setAcceptDrops(True)
        self._build_ui()
        self._build_actions()
        self._start_worker(device)
        self._refresh_state()

    # ------------------------------------------------------------------ construcción
    def _peek_max_length(self) -> int | None:
        try:
            return int(json.loads((self.bundle_dir / "manifest.json").read_text(encoding="utf-8"))["max_length"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _build_ui(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 12)
        body.setSpacing(14)
        body.addWidget(self._build_sidebar())
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_results())
        splitter.addWidget(self._build_detail())
        splitter.setStretchFactor(0, 1)
        splitter.setSizes([900, 260])
        body.addWidget(splitter, 1)
        outer.addLayout(body, 1)
        self.setCentralWidget(root)

        self.status_label = QLabel()
        self.model_status = QLabel()
        self.device_status = QLabel()
        self.offline_status = QLabel("Inferencia local · sin conexión")
        self.statusBar().addWidget(self.status_label, 1)
        for w in (self.model_status, self.device_status, self.offline_status):
            self.statusBar().addPermanentWidget(w)

    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("HeaderBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 12, 16, 12)
        title = QLabel(APP_NAME)
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Predicción de funciones GO con ESM-2 · inferencia local")
        subtitle.setObjectName("HeaderSubtitle")
        texts = QVBoxLayout()
        texts.setSpacing(0)
        texts.addWidget(title)
        texts.addWidget(subtitle)
        layout.addLayout(texts)
        layout.addStretch(1)
        self.model_chip = QLabel("Cargando modelo…")
        self.model_chip.setObjectName("ModelChip")
        layout.addWidget(self.model_chip)
        self.history_button = QPushButton("Historial")
        self.package_button = QPushButton("Paquete del modelo")
        for b in (self.history_button, self.package_button):
            b.setObjectName("HeaderButton")
            b.setCursor(Qt.PointingHandCursor)
            layout.addWidget(b)
        self.history_button.setToolTip("Ejecuciones anteriores (Ctrl+H)")
        self.package_button.setToolTip("Manifiesto, verificaciones y huellas SHA-256")
        self.history_button.clicked.connect(self.show_history)
        self.package_button.clicked.connect(self.show_package)
        return bar

    def _build_sidebar(self) -> QWidget:
        card = Card(spacing=8)
        card.setFixedWidth(280)
        b = card.body

        self.load_button = QPushButton("Cargar FASTA")
        self.load_button.setObjectName("Primary")
        self.load_button.setToolTip("Abrir un archivo FASTA o TXT (Ctrl+O). También puedes arrastrarlo aquí.")
        self.load_button.clicked.connect(self.open_file)
        b.addWidget(self.load_button)

        self.file_field = QLineEdit()
        self.file_field.setObjectName("FileField")
        self.file_field.setReadOnly(True)
        self.file_field.setPlaceholderText("Ningún archivo cargado")
        self.file_field.setAccessibleName("Archivo cargado")
        self.clear_file_button = QPushButton("✕")
        self.clear_file_button.setFixedWidth(34)
        self.clear_file_button.setToolTip("Quitar archivo")
        self.clear_file_button.setAccessibleName("Quitar archivo")
        self.clear_file_button.clicked.connect(self.clear_file)
        b.addWidget(hbox(self.file_field, self.clear_file_button, spacing=4))

        b.addWidget(section_label("o pega una secuencia / FASTA"))
        self.paste_box = QPlainTextEdit()
        self.paste_box.setPlaceholderText(">mi_proteina\nMKTAYIAKQRQISFVKSHFSRQ…")
        self.paste_box.setFixedHeight(96)
        self.paste_box.setTabChangesFocus(True)
        self.paste_box.setAccessibleName("Secuencia o FASTA pegado")
        self.paste_box.textChanged.connect(self._on_paste_changed)
        b.addWidget(self.paste_box)

        self.validation_label = muted("")
        self.validation_link = QPushButton("Ver validación")
        self.validation_link.setObjectName("Link")
        self.validation_link.setCursor(Qt.PointingHandCursor)
        self.validation_link.clicked.connect(self.show_validation)
        b.addWidget(self.validation_label)
        b.addWidget(hbox(self.validation_link, None))

        self.run_button = QPushButton("Analizar")
        self.run_button.setObjectName("Accent")
        self.run_button.setToolTip("Predecir funciones GO (Ctrl+Enter)")
        self.run_button.clicked.connect(self.start_analysis)
        b.addWidget(self.run_button)

        b.addSpacing(6)
        b.addWidget(section_label("Progreso"))
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setAccessibleName("Progreso del análisis")
        b.addWidget(self.progress)
        self.progress_label = muted("En espera")
        b.addWidget(self.progress_label)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setToolTip("Detener el análisis (Esc). No se muestran resultados parciales.")
        self.cancel_button.clicked.connect(self.cancel_analysis)
        b.addWidget(self.cancel_button)

        b.addSpacing(6)
        b.addWidget(section_label("Filtros"))
        self.aspect_buttons = {}
        row = QHBoxLayout()
        row.setSpacing(6)
        for aspect in ALL_ASPECTS:
            btn = QPushButton(aspect)
            btn.setObjectName("AspectToggle")
            btn.setProperty("aspect", aspect)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setToolTip(f"{theme.ASPECT_NAMES[aspect]} — mostrar u ocultar")
            btn.setAccessibleName(f"Filtro {theme.ASPECT_NAMES[aspect]}")
            btn.toggled.connect(self._refresh_table)
            self.aspect_buttons[aspect] = btn
            row.addWidget(btn)
        b.addLayout(row)

        b.addSpacing(4)
        self.threshold_title = section_label("Umbral")
        b.addWidget(self.threshold_title)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(SCORE_FLOOR * 100), 100)
        self.slider.setValue(45)
        self.slider.setPageStep(5)
        self.slider.setAccessibleName("Umbral de puntuación")
        self.slider.valueChanged.connect(self._on_threshold_changed)
        b.addWidget(self.slider)
        self.threshold_value = QLabel()
        self.threshold_value.setAccessibleName("Valor del umbral")
        self.reset_threshold = QPushButton("Restablecer")
        self.reset_threshold.setObjectName("Link")
        self.reset_threshold.setCursor(Qt.PointingHandCursor)
        self.reset_threshold.clicked.connect(self._reset_threshold)
        b.addWidget(hbox(self.threshold_value, None, self.reset_threshold))
        b.addStretch(1)
        return card

    def _build_results(self) -> QWidget:
        card = Card(margins=(14, 14, 14, 12))
        b = card.body

        self.protein_combo = QComboBox()
        self.protein_combo.setMinimumWidth(240)
        self.protein_combo.setAccessibleName("Proteína")
        self.protein_combo.currentIndexChanged.connect(self._refresh_table)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar término GO o nombre…  (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.search.setAccessibleName("Buscar en resultados")
        self.count_label = muted("", wrap=False)
        b.addWidget(hbox(self.protein_combo, self.search, self.count_label, spacing=10))

        self.notice = Banner()
        self.notice.setVisible(False)
        b.addWidget(self.notice)
        self.empty_notice = Banner()
        self.empty_notice.setVisible(False)
        b.addWidget(self.empty_notice)
        self.none_notice = Banner()
        self.none_notice.setVisible(False)
        b.addWidget(self.none_notice)

        self.stack = QStackedWidget()
        placeholder = QLabel("Carga un archivo FASTA o pega una secuencia y pulsa <b>Analizar</b>.<br>"
                             "<span style='color:%s'>Una proteína puede tener varias funciones en MF, BP y CC."
                             "</span>" % theme.MUTED)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        self.stack.addWidget(placeholder)

        self.table_model = ResultsTableModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.table_model)
        self.proxy.setSortRole(Qt.UserRole)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.search.textChanged.connect(self._on_search)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(COL_SCORE, Qt.DescendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideRight)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setItemDelegateForColumn(COL_ASPECT, AspectBadgeDelegate(self.table))
        self.table.setItemDelegateForColumn(COL_SCORE, ScoreBarDelegate(self.table))
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        for col, width in ((0, 118), (1, 104), (3, 74), (4, 92), (5, 150)):
            self.table.setColumnWidth(col, width)
        self.table.setAccessibleName("Tabla de funciones GO predichas")
        self.table.selectionModel().currentRowChanged.connect(self._on_row_selected)
        self.stack.addWidget(self.table)
        b.addWidget(self.stack, 1)

        self.export_button = QPushButton("Exportar CSV / TSV / JSON")
        self.export_button.setObjectName("Accent")
        self.export_button.setToolTip("Guardar los resultados visibles (Ctrl+E)")
        self.export_button.clicked.connect(self.export_results)
        note = muted("Las puntuaciones no son probabilidades calibradas.", wrap=False)
        note.setToolTip(SCORE_NOTE)
        b.addWidget(hbox(note, None, self.export_button))
        return card

    def _build_detail(self) -> QWidget:
        card = Card(spacing=6)
        card.setMinimumWidth(230)
        title = QLabel("Detalle")
        title.setObjectName("Title")
        card.body.addWidget(title)
        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setTextFormat(Qt.RichText)
        self.detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        card.body.addWidget(self.detail, 1)
        self.copy_seq = QPushButton("Copiar secuencia")
        self.copy_seq.clicked.connect(self._copy_sequence)
        card.body.addWidget(self.copy_seq)
        self._show_detail(None)
        return card

    def _build_actions(self):
        def action(text, shortcut, slot):
            act = QAction(text, self)
            act.setShortcuts(shortcut if isinstance(shortcut, list) else [shortcut])
            act.setShortcutContext(Qt.WindowShortcut)
            act.triggered.connect(slot)
            self.addAction(act)
            return act

        action("Abrir", QKeySequence.Open, self.open_file)
        action("Analizar", [QKeySequence("Ctrl+Return"), QKeySequence("Ctrl+Enter")], self.start_analysis)
        action("Cancelar", QKeySequence(Qt.Key_Escape), self.cancel_analysis)
        action("Exportar", QKeySequence("Ctrl+E"), self.export_results)
        action("Historial", QKeySequence("Ctrl+H"), self.show_history)
        action("Buscar", QKeySequence.Find, lambda: (self.search.setFocus(), self.search.selectAll()))

    # ---------------------------------------------------------------------- worker
    def _start_worker(self, device: str):
        self.worker = InferenceWorker(self.bundle_dir, device, self)
        self.worker.loading.connect(self._on_loading)
        self.worker.loaded.connect(self._on_model_loaded)
        self.worker.load_failed.connect(self._on_model_failed)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()
        self.worker.request_load()

    def _on_loading(self):
        self._set_status("Verificando y cargando el modelo…")

    def shutdown(self):
        if self.worker.isRunning():
            self.worker.stop()

    def closeEvent(self, event):  # noqa: N802
        if self.running and QMessageBox.question(
                self, "Análisis en curso", "Hay un análisis en curso. ¿Cancelarlo y salir?") != QMessageBox.Yes:
            event.ignore()
            return
        self.shutdown()
        super().closeEvent(event)

    def _on_model_loaded(self, model: LoadedModel):
        self.model = model
        self.report = model.report
        m = model.predictor.manifest
        self.max_length = int(m["max_length"])
        self.slider.setValue(round(float(m["threshold"]) * 100))
        kind = m["model_spec"]["kind"].upper()
        self.model_chip.setText(f"{kind} · {len(m['classes'])} términos · listo")
        self.model_chip.setProperty("state", "ok")
        self._repolish(self.model_chip)
        self.model_status.setText(f"Modelo {m['model_spec']['kind']} · {self.report.short_fingerprint}")
        self.device_status.setText(model.device.upper())
        self._set_status(f"Modelo listo en {model.load_seconds:.1f} s.")
        if self.validation is not None:
            self._revalidate()
        self._refresh_state()

    def _on_model_failed(self, message: str, report: IntegrityReport | None):
        self.report = report
        self.model_chip.setText("Modelo no disponible")
        self.model_chip.setProperty("state", "error")
        self._repolish(self.model_chip)
        self.model_status.setText("Sin modelo")
        self._set_status("No se pudo cargar el modelo.")
        self.notice.set("error", "<b>No se puede analizar.</b> " + html.escape(message).replace("\n", "<br>")
                        + "<br>Abre <i>Paquete del modelo</i> para ver los detalles.")
        self._refresh_state()

    # ------------------------------------------------------------------- entrada
    def open_file(self):
        if self.running:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Cargar FASTA", str(self.last_dir),
                                              "FASTA o texto (*.fasta *.fa *.faa *.fas *.txt);;Todos (*)")
        if path:
            self.load_file(Path(path))

    def load_file(self, path: Path):
        try:
            text = read_input_file(path)
        except OSError as exc:
            QMessageBox.warning(self, "No se pudo leer el archivo", str(exc))
            return
        self.last_dir = path.parent
        self.file_path, self.file_text = path, text
        self.file_field.setText(path.name)
        self.file_field.setToolTip(str(path))
        self.paste_box.blockSignals(True)
        self.paste_box.clear()
        self.paste_box.blockSignals(False)
        self._revalidate()
        if self.validation and not self.validation.is_clean:
            self.show_validation(allow_run=False)

    def clear_file(self):
        self.file_path = self.file_text = None
        self.file_field.clear()
        self.file_field.setToolTip("")
        self._revalidate()

    def _on_paste_changed(self):
        if self.file_path is not None:
            self.file_path = self.file_text = None
            self.file_field.clear()
        if not hasattr(self, "_paste_timer"):
            self._paste_timer = QTimer(self)
            self._paste_timer.setSingleShot(True)
            self._paste_timer.setInterval(300)
            self._paste_timer.timeout.connect(self._revalidate)
        self._paste_timer.start()

    def _current_input(self) -> tuple[str, str]:
        if self.file_text is not None:
            return self.file_text, self.file_path.name
        return self.paste_box.toPlainText(), "Secuencia pegada"

    def _revalidate(self):
        text, _ = self._current_input()
        self.validation = validate_text(text, self.max_length) if text.strip() else None
        if self.validation is None:
            self.validation_label.setText("")
        else:
            self.validation_label.setText(self.validation.summary())
        self.validation_link.setVisible(self.validation is not None)
        self._refresh_state()

    def show_validation(self, allow_run=False):
        if self.validation is None:
            return False
        dialog = ValidationDialog(self.validation, self._current_input()[1], self, allow_run=allow_run)
        return dialog.exec() == ValidationDialog.Accepted

    def dragEnterEvent(self, event: QDragEnterEvent):  # noqa: N802
        if event.mimeData().hasUrls() and not self.running:
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):  # noqa: N802
        urls = [u for u in event.mimeData().urls() if u.isLocalFile()]
        if urls:
            self.load_file(Path(urls[0].toLocalFile()))

    # ------------------------------------------------------------------- análisis
    def start_analysis(self):
        if self.running or self.model is None:
            return
        self._revalidate()
        report = self.validation
        if report is None:
            self.notice.set("warning", "Carga un archivo FASTA o pega una secuencia antes de analizar.")
            return
        if report.global_errors or not report.accepted:
            self.show_validation(allow_run=False)
            return
        if report.rejected and not self.show_validation(allow_run=True):
            return
        text, source = self._current_input()
        records = report.as_records()
        self._pending_input = (text, source, report)
        self.run_id = self.history.start(source, len(records), len(report.rejected),
                                         self.model.predictor.manifest["model_spec"]["kind"],
                                         self.report.fingerprint, float(self.model.predictor.manifest["threshold"]),
                                         __version__)
        self.running = True
        self._started_at = datetime.now().isoformat(timespec="seconds")
        self.progress.setRange(0, len(records))
        self.progress.setValue(0)
        self.progress_label.setText(f"0 de {len(records)} proteínas")
        self.notice.set("info", "")
        self._set_status("Analizando…")
        self._refresh_state()
        self.worker.request_predict(records)

    def cancel_analysis(self):
        if self.running:
            self.worker.request_cancel()
            self.cancel_button.setEnabled(False)
            self.progress_label.setText("Cancelando al terminar el bloque actual…")

    def _on_progress(self, done: int, total: int):
        self.progress.setValue(done)
        self.progress_label.setText(f"{done} de {total} proteínas")

    def _on_finished(self, results: list, seconds: float):
        text, source, report = self._pending_input
        m = self.model.predictor.manifest
        self.result = RunResult(
            source_name=source, input_text=text, proteins=results, model_kind=m["model_spec"]["kind"],
            model_threshold=float(m["threshold"]), max_length=int(m["max_length"]),
            fingerprint=self.report.fingerprint, started_at=self._started_at,
            finished_at=datetime.now().isoformat(timespec="seconds"),
            rejected=[{"index": r.index, "id": r.record_id, "messages": r.messages} for r in report.rejected])
        try:
            self.history.finish(self.run_id, COMPLETED, seconds, self.result)
        except Exception as exc:  # noqa: BLE001 - el historial es opcional
            self._set_status(f"Resultados listos (no se guardó en el historial: {exc})")
        self.running = False
        self.progress_label.setText(f"Completado: {len(results)} proteínas en {seconds:.1f} s")
        self._set_status("Análisis completado.")
        self._show_result()

    def _on_cancelled(self):
        self.history.finish(self.run_id, CANCELLED, message="Cancelado por el usuario.")
        self.running = False
        self.result = None
        self.progress.setValue(0)
        self.progress_label.setText("Cancelado")
        self.notice.set("warning", "Análisis cancelado. No se muestran resultados parciales.")
        self._set_status("Análisis cancelado.")
        self._show_result()

    def _on_failed(self, message: str):
        if self.run_id is not None:
            self.history.finish(self.run_id, FAILED, message=message)
        self.running = False
        self.progress.setValue(0)
        self.progress_label.setText("Falló")
        self.notice.set("error", html.escape(message))
        self._set_status("El análisis falló.")
        self._refresh_state()
        QMessageBox.critical(self, "Error en el análisis", message)

    # ----------------------------------------------------------------- resultados
    def load_result(self, result: RunResult):
        self.result = result
        self.notice.set("info", f"Resultados del historial: {html.escape(result.source_name)} "
                                f"({result.started_at.replace('T', ' ')}).")
        self.slider.setValue(round(result.model_threshold * 100))
        self._show_result()

    def _show_result(self):
        self.protein_combo.blockSignals(True)
        self.protein_combo.clear()
        if self.result:
            ids = self.result.protein_ids()
            self.protein_combo.addItem(f"Todas las proteínas ({len(ids)})", None)
            for p in self.result.proteins:
                flag = " ⚠" if p["truncated"] else ""
                self.protein_combo.addItem(f"{p['id']} · {p['length']} aa{flag}", p["id"])
        self.protein_combo.blockSignals(False)
        self._refresh_table()
        self._refresh_state()

    def current_view(self) -> ViewFilter:
        aspects = tuple(a for a, btn in self.aspect_buttons.items() if btn.isChecked())
        return ViewFilter(threshold=self.slider.value() / 100, aspects=aspects,
                          protein_id=self.protein_combo.currentData())

    def _refresh_table(self, *_):
        if not self.result:
            self.table_model.set_rows([])
            self.stack.setCurrentIndex(0)
            self.count_label.setText("")
            self.empty_notice.setVisible(False)
            self.none_notice.setVisible(False)
            self._show_detail(None)
            return
        view = self.current_view()
        self.table_model.set_rows(self.result.rows(view))
        self.stack.setCurrentIndex(1)
        self._update_count()

        notes = []
        truncated = [p for p in self.result.truncated_proteins()
                     if not view.protein_id or p["id"] == view.protein_id]
        if truncated:
            items = ", ".join(f"{html.escape(p['id'])} ({p['residues_used']} de {p['length']})"
                              for p in truncated[:6])
            more = f" y {len(truncated) - 6} más" if len(truncated) > 6 else ""
            notes.append(f"<b>Secuencias truncadas:</b> se usaron solo los primeros residuos — {items}{more}.")
        if self.result.rejected:
            notes.append(f"<b>{len(self.result.rejected)} registro(s) excluidos</b> por la validación.")
        self.empty_notice.set("warning", "<br>".join(notes))

        empty = self.result.proteins_without_terms(view)
        if empty:
            names = ", ".join(html.escape(x) for x in empty[:8]) + (f" y {len(empty) - 8} más" if len(empty) > 8 else "")
            self.none_notice.set("info", f"<b>Ninguna función superó el umbral</b> para: {names}. "
                                         "No implica que la proteína carezca de función.")
        else:
            self.none_notice.set("info", "")
        self._show_detail(None)

    def _update_count(self):
        shown, total = self.proxy.rowCount(), self.table_model.rowCount()
        n_prot = len({self.table_model.row_at(i).protein_id for i in range(total)})
        text = f"{total} funciones · {n_prot} proteína{'s' if n_prot != 1 else ''}"
        if shown != total:
            text = f"{shown} de {text}"
        self.count_label.setText(text)

    def _on_search(self, text: str):
        self.proxy.setFilterFixedString(text.strip())
        self._update_count()

    def _on_threshold_changed(self, value: int):
        default = round(float(self.model.predictor.manifest["threshold"]) * 100) if self.model else None
        label = f"<b>{theme.num(value / 100, 2)}</b>"
        if default is not None:
            label += (f" <span style='color:{theme.MUTED}'>· del modelo</span>" if value == default else
                      f" <span style='color:{theme.WARN}'>· modelo: {theme.num(default / 100, 2)}</span>")
        self.threshold_value.setText(label)
        self.reset_threshold.setVisible(default is not None and value != default)
        self._refresh_table()

    def _reset_threshold(self):
        if self.model:
            self.slider.setValue(round(float(self.model.predictor.manifest["threshold"]) * 100))

    def _on_row_selected(self, current, _previous):
        row = self.table_model.row_at(self.proxy.mapToSource(current).row()) if current.isValid() else None
        self._show_detail(row)

    def _show_detail(self, row):
        self._detail_row = row
        self.copy_seq.setEnabled(row is not None)
        if row is None:
            self.detail.setText(f"<span style='color:{theme.MUTED}'>Selecciona una fila para ver el término GO, "
                                "su origen y los ancestros en el vocabulario.</span>")
            return
        meta = {}
        if self.model is not None:
            meta = self.model.predictor.metadata
        protein = self.result.protein(row.protein_id) if self.result else None
        scores = {p["go_term"]: p["score"] for p in (protein or {}).get("predictions", [])}
        color = theme.ASPECT_COLORS.get(row.aspect, theme.MUTED)
        parts = [
            f"<p style='margin:0'><b style='font-size:11pt'>{html.escape(row.name)}</b></p>",
            f"<p style='margin:2px 0 8px 0'><code>{row.go_term}</code> · "
            f"<span style='color:{color};font-weight:600'>{row.aspect}</span> "
            f"{theme.ASPECT_NAMES.get(row.aspect, '')}</p>",
            f"<p style='margin:0'>Puntuación: <b>{theme.num(row.score)}</b></p>",
            f"<p style='margin:0'>Puntaje directo del modelo: {theme.num(row.direct_score)}</p>",
            f"<p style='margin:0 0 8px 0'>Origen: <b>{theme.ORIGIN_LABELS.get(row.origin, row.origin)}</b>"
            + (" — heredado de un término más específico (regla is_a / part_of)" if row.origin == "propagated" else "")
            + "</p>",
        ]
        ancestors = meta.get(row.go_term, {}).get("ancestors", [])
        if ancestors:
            items = "".join(
                f"<li><code>{a}</code> {html.escape(meta.get(a, {}).get('name', ''))}"
                + (f" — {theme.num(scores[a])}" if a in scores else "") + "</li>" for a in ancestors[:12])
            parts.append(f"<p style='margin:0'><b>Ancestros en el vocabulario</b></p><ul style='margin-top:2px'>{items}</ul>")
        if protein:
            trunc = (f"<br><span style='color:{theme.WARN}'>Truncada: se usaron {protein['residues_used']} de "
                     f"{protein['length']} residuos.</span>") if protein["truncated"] else ""
            parts.append(f"<p style='margin:8px 0 0 0'><b>Proteína</b> <code>{html.escape(row.protein_id)}</code><br>"
                         f"Longitud: {protein['length']} aa{trunc}</p>")
        self.detail.setText("".join(parts))

    def _copy_sequence(self):
        from PySide6.QtGui import QGuiApplication

        if self._detail_row and self.result:
            p = self.result.protein(self._detail_row.protein_id)
            if p:
                QGuiApplication.clipboard().setText(f">{p['id']}\n{p['sequence']}\n")
                self._set_status(f"Secuencia de {p['id']} copiada.")

    # ------------------------------------------------------------------- diálogos
    def export_results(self):
        if not self.result or self.running:
            return
        view = self.current_view()
        rows = len(self.result.rows(view))
        empty = len(self.result.proteins_without_terms(view))
        stem = Path(self.result.source_name).stem if self.result.source_name != "Secuencia pegada" else "secuencia"
        dialog = ExportDialog(view, rows, empty, self.last_dir, stem, self)
        if dialog.exec() != ExportDialog.Accepted or dialog.path is None:
            return
        try:
            path = self.result.export(dialog.path, dialog.view, dialog.fmt)
        except OSError as exc:
            QMessageBox.warning(self, "No se pudo exportar", str(exc))
            return
        self.last_dir = path.parent
        self._set_status(f"Exportado: {path}")

    def show_history(self):
        dialog = HistoryDialog(self.history, self)
        if dialog.exec() == HistoryDialog.Accepted and dialog.selected_run_id is not None:
            result = self.history.load(dialog.selected_run_id)
            if result is None:
                QMessageBox.information(self, "Historial", "Esta ejecución no tiene resultados guardados.")
                return
            if self.report and result.fingerprint != self.report.fingerprint:
                QMessageBox.information(
                    self, "Versión distinta del modelo",
                    "Estos resultados se generaron con otra versión del paquete de modelo "
                    f"({result.fingerprint[:12]}). Se muestran tal como se guardaron.")
            self.load_result(result)

    def show_package(self):
        report = self.report or verify_bundle(self.bundle_dir)
        info = {"seconds": self.model.load_seconds, "device": self.model.device} if self.model else None
        PackageDialog(report, info, self).exec()

    # ---------------------------------------------------------------------- estado
    def _refresh_state(self):
        ready = self.model is not None
        has_input = self.validation is not None and bool(self.validation.accepted)
        self.run_button.setEnabled(ready and not self.running and has_input)
        self.cancel_button.setEnabled(self.running)
        self.load_button.setEnabled(not self.running)
        self.paste_box.setReadOnly(self.running)
        self.clear_file_button.setEnabled(not self.running and self.file_path is not None)
        self.export_button.setEnabled(self.result is not None and not self.running)
        if not ready and self.model_chip.property("state") != "error":
            self.run_button.setToolTip("Esperando a que cargue el modelo…")
        else:
            self.run_button.setToolTip("Predecir funciones GO (Ctrl+Enter)")
        if self.running:
            self.progress_label.setVisible(True)

    def _set_status(self, text: str):
        self.status_label.setText(text)

    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
