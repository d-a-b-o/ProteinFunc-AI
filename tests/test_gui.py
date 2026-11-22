"""Pruebas de la interfaz con Qt sin pantalla (QT_QPA_PLATFORM=offscreen) y el modelo real."""
import json

import pytest
from conftest import EXAMPLES, MODEL_DIR

pytest.importorskip("pytestqt")

from proteinfunc_app.core.history import CANCELLED, COMPLETED, History  # noqa: E402
from proteinfunc_app.core.results import ViewFilter  # noqa: E402
from proteinfunc_app.ui import theme  # noqa: E402
from proteinfunc_app.ui.main_window import MainWindow  # noqa: E402


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    # Los diálogos modales se sustituyen para no bloquear las pruebas.
    from proteinfunc_app.ui import main_window as mw

    monkeypatch.setattr(mw.ValidationDialog, "exec", lambda self: mw.ValidationDialog.Accepted)
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda *a, **k: None)
    qtbot_app = qtbot  # noqa: F841
    from PySide6.QtWidgets import QApplication

    QApplication.instance().setStyleSheet(theme.STYLESHEET)
    from PySide6.QtCore import QSettings

    w = MainWindow(MODEL_DIR, History(tmp_path / "h.sqlite3"),
                   settings=QSettings(str(tmp_path / "prefs.ini"), QSettings.IniFormat))
    qtbot.addWidget(w)
    w.show()
    qtbot.waitUntil(lambda: w.model is not None, timeout=60000)
    yield w
    w.shutdown()


def analyze(qtbot, w):
    w.start_analysis()
    qtbot.waitUntil(lambda: not w.running, timeout=60000)


def test_analyze_fasta_and_filter(qtbot, window):
    w = window
    w.load_file(EXAMPLES / "muestra.fasta")
    assert w.run_button.isEnabled()
    analyze(qtbot, w)
    assert w.result is not None and len(w.result.proteins) == 3
    # Por defecto solo términos específicos: menos filas que la jerarquía completa.
    assert w.specific_check.isChecked()
    specific = w.table_model.rowCount()
    assert specific == len(w.result.rows(ViewFilter(0.45, specific_only=True)))
    w.specific_check.setChecked(False)
    assert w.table_model.rowCount() == len(w.result.rows(ViewFilter(0.45))) > specific
    assert "ejemplo_kaggle" in w.empty_notice.label.text()  # Aviso de truncamiento.

    before = w.table_model.rowCount()
    w.aspect_buttons["BP"].setChecked(False)
    assert all(w.table_model.row_at(i).aspect != "BP" for i in range(w.table_model.rowCount()))
    w.slider.setValue(90)
    assert w.table_model.rowCount() < before
    assert w.none_notice.isVisible()  # Alguna proteína sin funciones ≥ 0,90.

    w.search.setText("binding")
    assert all("binding" in w.table_model.row_at(w.proxy.mapToSource(w.proxy.index(i, 0)).row()).name
               for i in range(w.proxy.rowCount()))

    runs = w.history.list()
    assert runs[0].status == COMPLETED and runs[0].model_fingerprint == w.report.fingerprint


def test_model_loaded_once(qtbot, window):
    w = window
    w.paste_box.setPlainText("MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAG")
    w._revalidate()
    analyze(qtbot, w)
    analyze(qtbot, w)
    assert w.worker.load_count == 1
    assert w.result.proteins[0]["id"] == "query_1"


def test_gui_matches_predictor(qtbot, window, predictor):
    w = window
    w.load_file(EXAMPLES / "muestra.fasta")
    analyze(qtbot, w)
    expected = predictor.predict((EXAMPLES / "muestra.fasta").read_text(encoding="utf-8"))
    got = w.result.to_contract(ViewFilter(predictor.manifest["threshold"]))
    for a, b in zip(got["results"], expected["results"]):
        assert a["id"] == b["id"] and a["status"] == b["status"]
        assert [p["go_term"] for p in a["predictions"]] == [p["go_term"] for p in b["predictions"]]
        assert [p["score"] for p in a["predictions"]] == pytest.approx([p["score"] for p in b["predictions"]])


def test_invalid_records_are_excluded(qtbot, window):
    w = window
    w.load_file(EXAMPLES / "con_errores.fasta")
    assert "4 con error" in w.validation_label.text()
    analyze(qtbot, w)
    assert w.result.protein_ids() == ["valida_1"]
    assert len(w.result.rejected) == 4


def test_cancel_discards_partial_results(qtbot, window):
    w = window
    w.paste_box.setPlainText("".join(f">p{i}\n{'MKTAYIAKQRQISFVKSHFSRQ' * 20}\n" for i in range(64)))
    w._revalidate()
    w.start_analysis()
    w.cancel_analysis()
    qtbot.waitUntil(lambda: not w.running, timeout=60000)
    assert w.result is None and w.table_model.rowCount() == 0
    assert w.history.list()[0].status == CANCELLED


def test_export_from_gui(qtbot, window, tmp_path):
    w = window
    w.load_file(EXAMPLES / "muestra.fasta")
    analyze(qtbot, w)
    path = w.result.export(tmp_path / "r.json", w.current_view())
    data = json.loads(path.read_text(encoding="utf-8"))
    assert [r["id"] for r in data["results"]] == ["P01308", "ubiquitina", "ejemplo_kaggle"]
    assert data["metadata"]["filter"]["threshold"] == w.slider.value() / 100


def test_history_reopen(qtbot, window):
    w = window
    w.load_file(EXAMPLES / "muestra.fasta")
    analyze(qtbot, w)
    run = w.history.list()[0]
    w.result = None
    w.load_result(w.history.load(run.id))
    assert len(w.result.proteins) == 3 and w.table_model.rowCount() > 0


def test_broken_bundle_disables_analysis(qtbot, tmp_path):
    import shutil

    broken = tmp_path / "modelo roto"
    shutil.copytree(MODEL_DIR, broken)
    (broken / "weights.pt").write_bytes(b"corrupto")
    from PySide6.QtCore import QSettings

    w = MainWindow(broken, History(tmp_path / "h2.sqlite3"),
                   settings=QSettings(str(tmp_path / "p2.ini"), QSettings.IniFormat))
    qtbot.addWidget(w)
    qtbot.waitUntil(lambda: w.model_chip.property("state") == "error", timeout=60000)
    w.paste_box.setPlainText("MKTAYIAKQR")
    w._revalidate()
    assert not w.run_button.isEnabled()
    assert "SHA256SUMS" in w.notice.label.text()
    w.shutdown()


def test_summary_panel_and_atypical_warning(qtbot, window):
    w = window
    w.paste_box.setPlainText(">poliG\n" + "G" * 60 + "\n>insulina\n"
                             "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAG\n")
    w._revalidate()
    assert "1 con aviso" in w.validation_label.text()
    analyze(qtbot, w)
    assert "atípicas" in w.empty_notice.label.text() and "poliG" in w.empty_notice.label.text()
    assert "2 proteína(s)" in w.detail.text()
    w.protein_combo.setCurrentIndex(w.protein_combo.findData("insulina"))
    assert "insulina" in w.detail.text() and "Función molecular" in w.detail.text()
    w.table.selectRow(0)
    assert w.detail_title.text() == "Detalle"


def test_performance_is_recorded(qtbot, window):
    w = window
    w.load_file(EXAMPLES / "muestra.fasta")
    analyze(qtbot, w)
    perf = w.history.list()[0].performance
    assert perf["proteins"] == 3 and perf["seconds"] > 0 and perf["device"] == "cpu"
    assert perf["peak_memory_mb"] and perf["chunk_size"] == w.worker.chunk_size


def test_preferences_apply_batch_and_threads(qtbot, window):
    w = window
    w.worker.configure(2, 1)
    w.load_file(EXAMPLES / "muestra.fasta")
    analyze(qtbot, w)
    perf = w.result.performance
    assert perf["chunk_size"] == 2 and perf["threads"] == 1


def test_settings_persist(qtbot, tmp_path):
    from PySide6.QtCore import QSettings

    ini = str(tmp_path / "prefs.ini")
    w = MainWindow(MODEL_DIR, History(tmp_path / "h.sqlite3"), settings=QSettings(ini, QSettings.IniFormat))
    qtbot.addWidget(w)
    w.aspect_buttons["CC"].setChecked(False)
    w.specific_check.setChecked(False)
    w.last_dir = tmp_path
    w._save_settings()
    w.shutdown()
    w2 = MainWindow(MODEL_DIR, History(tmp_path / "h.sqlite3"), settings=QSettings(ini, QSettings.IniFormat))
    qtbot.addWidget(w2)
    assert not w2.aspect_buttons["CC"].isChecked() and w2.aspect_buttons["MF"].isChecked()
    assert not w2.specific_check.isChecked() and w2.last_dir == tmp_path
    w2.shutdown()


def test_about_and_preferences_dialogs(qtbot, window):
    from proteinfunc_app.services import available_devices
    from proteinfunc_app.ui.dialogs import AboutDialog, PreferencesDialog

    about = AboutDialog(window.report, window)
    qtbot.addWidget(about)
    prefs = PreferencesDialog(available_devices(), "cpu", 8, None, window)
    qtbot.addWidget(prefs)
    assert prefs.device == "cpu" and prefs.chunk_size == 8 and prefs.threads is None
