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
    w = MainWindow(MODEL_DIR, History(tmp_path / "h.sqlite3"))
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
    assert w.table_model.rowCount() == len(w.result.rows(ViewFilter(0.45)))
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
    w = MainWindow(broken, History(tmp_path / "h2.sqlite3"))
    qtbot.addWidget(w)
    qtbot.waitUntil(lambda: w.model_chip.property("state") == "error", timeout=60000)
    w.paste_box.setPlainText("MKTAYIAKQR")
    w._revalidate()
    assert not w.run_button.isEnabled()
    assert "SHA256SUMS" in w.notice.label.text()
    w.shutdown()
