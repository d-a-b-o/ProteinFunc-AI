"""Regresión QA-021-EXPORT-BUSQUEDA con Qt offscreen y resultados sintéticos."""
import copy
import csv
import json
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt

from proteinfunc_app.core.history import COMPLETED, History
from proteinfunc_app.core.results import COLUMNS, RunResult, ViewFilter
from proteinfunc_app.ui import main_window as mw


def synthetic_result():
    def pred(term, name, aspect, score, origin="direct"):
        return dict(go_term=term, name=name, aspect=aspect, score=score,
                    direct_score=score if origin == "direct" else 0.1, origin=origin)

    def protein(pid, predictions):
        return dict(id=pid, sequence="MKT", length=3, residues_used=3,
                    truncated=False, predictions=predictions)

    return RunResult("sintetico.fasta", ">P1\nMKT\n>P2\nMKT\n>P3\nMKT\n", [
        protein("P1", [pred("GO:1", "unión especial", "MF", .9),
                       pred("GO:2", "proceso de unión", "BP", .6, "propagated"),
                       pred("GO:3", "membrana", "CC", .3),
                       pred("GO:4", "función raíz", "MF", .8, "propagated")]),
        protein("P2", [pred("GO:1", "unión especial", "MF", .7),
                       pred("GO:5", "membrana compartida", "CC", .55)]),
        protein("P3", []),
    ], "esm2", .45, 512, "f" * 64,
        ancestors={"GO:1": ["GO:4"], "GO:2": [], "GO:3": [], "GO:4": [], "GO:5": []})


@pytest.fixture
def export_window(qtbot, tmp_path, monkeypatch):
    # No carga ni simula predicciones del modelo: este ensayo trata solo resultados ya obtenidos.
    def idle_worker(self, device):
        self.worker = SimpleNamespace(isRunning=lambda: False)

    monkeypatch.setattr(mw.MainWindow, "_start_worker", idle_worker)
    w = mw.MainWindow(tmp_path / "sin-modelo", History(tmp_path / "historial.sqlite3"),
                      settings=QSettings(str(tmp_path / "preferencias.ini"), QSettings.IniFormat))
    qtbot.addWidget(w)
    w.show()
    w.load_result(synthetic_result())
    w.specific_check.setChecked(False)
    yield w
    w.shutdown()


def proxy_keys(w):
    # Lee identidades del modelo fuente después de mapear el proxy, no conserva índices visuales.
    return [(r.protein_id, r.go_term) for i in range(w.proxy.rowCount())
            for r in [w.table_model.row_at(w.proxy.mapToSource(w.proxy.index(i, 0)).row())]]


def exported_keys(path, fmt):
    if fmt == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == {"schema_version", "model", "input", "results", "metadata"}
        assert data["schema_version"] == 1
        return [(p["id"], pred["go_term"]) for p in data["results"] for pred in p["predictions"]], data
    text = path.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader([line for line in text.splitlines() if not line.startswith("#")],
                               delimiter="," if fmt == "csv" else "\t"))
    assert text.splitlines() and path.read_bytes().startswith(b"\xef\xbb\xbf")
    header = next(line for line in text.splitlines() if not line.startswith("#"))
    assert header.split("," if fmt == "csv" else "\t") == COLUMNS
    return [(r["protein_id"], r["go_term"]) for r in rows if r["go_term"]], rows


def export_through_dialog(w, tmp_path, monkeypatch, fmt):
    path = tmp_path / f"resultado.{fmt}"
    captured = {}

    def accept_dialog(dialog):
        captured["view"] = dialog.view
        for button in dialog.group.buttons():
            button.setChecked(button.property("fmt") == fmt)
        dialog._choose()
        return dialog.result()

    monkeypatch.setattr(mw.ExportDialog, "exec", accept_dialog)
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **kw: (str(path), ""))
    w.export_results()
    assert path.exists()
    return path, captured["view"]


SCENARIOS = [
    ("", ("MF", "BP", "CC"), 45, False, 5),
    ("GO:1", ("MF", "BP", "CC"), 45, False, 2),
    ("  UnIÓn  ", ("MF", "BP", "CC"), 45, False, 3),
    ("unión", ("MF",), 45, False, 2),
    ("unión", ("BP",), 45, False, 1),
    ("membrana", ("CC",), 10, False, 2),
    ("GO:1", ("MF", "BP", "CC"), 80, False, 1),
    ("inexistente", ("MF", "BP", "CC"), 45, False, 0),
    # Buscar un ancestro oculto no debe hacer que vuelva a aparecer.
    ("raíz", ("MF", "BP", "CC"), 45, True, 0),
    # Qt también busca en origen, aspecto y proteína; se conserva ese comportamiento.
    ("Propagado", ("MF", "BP", "CC"), 45, False, 2),
    ("P2", ("MF", "BP", "CC"), 45, False, 2),
]


@pytest.mark.parametrize("fmt", ["csv", "tsv", "json"])
@pytest.mark.parametrize("query,aspects,threshold,specific,count", SCENARIOS)
def test_export_matches_visible_rows(export_window, tmp_path, monkeypatch, fmt,
                                     query, aspects, threshold, specific, count):
    w = export_window
    w.specific_check.setChecked(specific)
    for aspect, button in w.aspect_buttons.items():
        button.setChecked(aspect in aspects)
    w.slider.setValue(threshold)
    w.search.setText(query)
    w.proxy.sort(0, Qt.AscendingOrder)
    visible = proxy_keys(w)
    assert len(visible) == count
    path, _ = export_through_dialog(w, tmp_path, monkeypatch, fmt)
    keys, data = exported_keys(path, fmt)
    assert sorted(keys) == sorted(visible)
    assert len(keys) == len(set(keys))
    if query.strip():
        if fmt == "json":
            assert all(p["predictions"] for p in data["results"])
        else:
            assert all(row["go_term"] for row in data)
    elif fmt == "json":
        assert data["results"][-1]["id"] == "P3" and not data["results"][-1]["predictions"]
    else:
        assert data[-1]["protein_id"] == "P3" and data[-1]["go_term"] == ""


@pytest.mark.parametrize("fmt", ["csv", "tsv", "json"])
def test_search_reset_and_sorting_keep_identity(export_window, tmp_path, monkeypatch, fmt):
    w = export_window
    w.search.setText("GO:1")
    w.protein_combo.setCurrentIndex(w.protein_combo.findData("P2"))
    selected = w.current_view()
    assert selected.visible_keys == frozenset({("P2", "GO:1")})
    # La selección es una instantánea de identidades, independiente del orden visual.
    w.proxy.sort(5, Qt.AscendingOrder)
    assert w.current_view().visible_keys == selected.visible_keys
    assert [(r.protein_id, r.go_term) for r in w.result.rows(selected)] == [("P2", "GO:1")]
    w.search.setText("inexistente")
    assert w.current_view().visible_keys == frozenset()
    w.search.clear()
    assert w.current_view().visible_keys is None
    path, _ = export_through_dialog(w, tmp_path, monkeypatch, fmt)
    keys, _ = exported_keys(path, fmt)
    assert sorted(keys) == sorted(proxy_keys(w)) == [("P2", "GO:1"), ("P2", "GO:5")]
    w.protein_combo.setCurrentIndex(0)
    assert len(proxy_keys(w)) == 5


@pytest.mark.parametrize("selection,expected", [(None, 5), (frozenset(), 0)])
def test_absent_and_empty_selection_are_distinct(selection, expected):
    r = synthetic_result()
    view = ViewFilter(.45, visible_keys=selection)
    assert len(r.rows(view)) == expected
    if selection is not None:
        assert r.to_contract(view)["results"] == []
        assert r.proteins_without_terms(view) == []


def test_prediction_identity_is_unique_across_proteins_and_history(tmp_path):
    r = synthetic_result()
    r.validate_prediction_keys()
    keys = [(p["id"], x["go_term"]) for p in r.proteins for x in p["predictions"]]
    assert len(keys) == len(set(keys)) == 6
    assert ("P1", "GO:1") in keys and ("P2", "GO:1") in keys
    h = History(tmp_path / "historial.sqlite3")
    rid = h.start("sintetico", 3, 0, "esm2", r.fingerprint, .45, r.app_version)
    h.finish(rid, COMPLETED, result=r)
    loaded = History(h.db_path).load(rid)
    loaded.validate_prediction_keys()
    assert loaded.to_dict() == r.to_dict()
    assert "visible_keys" not in loaded.to_dict()
    assert len(loaded.rows(ViewFilter(.45, visible_keys=frozenset({("P2", "GO:1")})))) == 1


def test_ambiguous_prediction_keys_are_rejected(export_window, monkeypatch):
    w = export_window
    w.result.proteins[0]["predictions"].append(copy.deepcopy(w.result.proteins[0]["predictions"][0]))
    w.search.setText("GO:1")
    with pytest.raises(ValueError, match="duplicad"):
        w.current_view()
    warnings = []
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *args: warnings.append(args[-1]))
    monkeypatch.setattr(mw.ExportDialog, "exec", lambda self: pytest.fail("No debe abrir un diálogo con claves ambiguas"))
    w.export_results()
    assert len(warnings) == 1 and "duplicad" in warnings[0]


def test_propagated_export_option_still_limits_visible_selection(export_window):
    w = export_window
    w.search.setText("unión")
    view = w.current_view()
    view.include_propagated = False
    assert [(r.protein_id, r.go_term) for r in w.result.rows(view)] == [("P1", "GO:1"), ("P2", "GO:1")]
