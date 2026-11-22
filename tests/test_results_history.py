import csv
import json

from proteinfunc_app.core.history import CANCELLED, COMPLETED, FAILED, History
from proteinfunc_app.core.results import RunResult, ViewFilter

PROTEINS = [
    {"id": "proteína_á", "sequence": "MKT", "length": 3, "residues_used": 3, "truncated": False,
     "predictions": [
         {"go_term": "GO:1", "name": "unión", "aspect": "MF", "score": 0.9, "direct_score": 0.9, "origin": "direct"},
         {"go_term": "GO:2", "name": "proceso", "aspect": "BP", "score": 0.6, "direct_score": 0.2, "origin": "propagated"},
         {"go_term": "GO:3", "name": "membrana", "aspect": "CC", "score": 0.3, "direct_score": 0.3, "origin": "direct"}]},
    {"id": "P2", "sequence": "M" * 600, "length": 600, "residues_used": 512, "truncated": True,
     "predictions": [
         {"go_term": "GO:3", "name": "membrana", "aspect": "CC", "score": 0.2, "direct_score": 0.2, "origin": "direct"}]},
]


def make_result():
    return RunResult("prueba.fasta", ">proteína_á\nMKT\n>P2\n" + "M" * 600, [dict(p) for p in PROTEINS],
                     "esm2", 0.45, 512, "f" * 64, ancestors={"GO:1": [], "GO:2": ["GO:9"], "GO:3": []},
                     performance={"seconds": 1.0, "peak_memory_mb": 100.0})


def test_filters():
    r = make_result()
    assert [x.go_term for x in r.rows(ViewFilter(0.45))] == ["GO:1", "GO:2"]
    assert [x.go_term for x in r.rows(ViewFilter(0.45, aspects=("MF",)))] == ["GO:1"]
    assert [x.go_term for x in r.rows(ViewFilter(0.45, include_propagated=False))] == ["GO:1"]
    assert r.proteins_without_terms(ViewFilter(0.45)) == ["P2"]
    assert len(r.rows(ViewFilter(0.1, protein_id="P2"))) == 1


def test_json_export_roundtrip_with_accents(tmp_path):
    r = make_result()
    path = r.export(tmp_path / "salida.json", ViewFilter(0.45))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1 and data["input"] == r.input_text
    first, second = data["results"]
    assert first["id"] == "proteína_á" and first["status"] == "ok"
    assert [p["name"] for p in first["predictions"]] == ["unión", "proceso"]
    assert second["status"] == "no_terms_above_threshold" and second["truncated"] is True
    assert data["metadata"]["filter"]["threshold"] == 0.45
    assert data["metadata"]["model_fingerprint_sha256"] == "f" * 64


def test_csv_and_tsv_exports_match_view(tmp_path):
    r = make_result()
    view = ViewFilter(0.45)
    for fmt, delim in (("csv", ","), ("tsv", "\t")):
        path = r.export(tmp_path / f"salida.{fmt}", view)
        text = path.read_text(encoding="utf-8-sig")
        meta = [l for l in text.splitlines() if l.startswith("#")]
        assert any("model_fingerprint_sha256" in l for l in meta) and any("filter" in l for l in meta)
        rows = list(csv.DictReader([l for l in text.splitlines() if not l.startswith("#")], delimiter=delim))
        assert [(x["protein_id"], x["go_term"]) for x in rows] == [
            ("proteína_á", "GO:1"), ("proteína_á", "GO:2"), ("P2", "")]
        assert rows[1]["origin"] == "propagated" and float(rows[1]["score"]) == 0.6
        assert rows[2]["name"] == "Ninguna función superó el umbral"


def test_history_lifecycle(tmp_path):
    h = History(tmp_path / "h.sqlite3")
    run = h.start("prueba.fasta", 2, 1, "esm2", "f" * 64, 0.45, "0.1.0")
    h.finish(run, COMPLETED, 1.5, make_result())
    cancelled = h.start("b.fasta", 1, 0, "esm2", "e" * 64, 0.45, "0.1.0")
    h.finish(cancelled, CANCELLED, message="Cancelado")
    h.start("c.fasta", 1, 0, "esm2", "f" * 64, 0.45, "0.1.0")  # Queda «en curso».

    reopened = History(tmp_path / "h.sqlite3")  # Simula reiniciar la app.
    runs = reopened.list()
    assert [r.status for r in runs] == [FAILED, CANCELLED, COMPLETED]
    assert "Interrumpida" in runs[0].message
    assert [r.has_results for r in runs] == [False, False, True]
    assert len(reopened.list(fingerprint="f" * 64)) == 2
    assert reopened.list(date_from="2000-01-01", date_to="2000-12-31") == []
    loaded = reopened.load(run)
    assert loaded.proteins == make_result().proteins and loaded.fingerprint == "f" * 64
    assert reopened.load(cancelled) is None
    reopened.delete(run)
    assert len(reopened.list()) == 2


def test_specific_only_hides_visible_ancestors():
    proteins = [{"id": "p", "sequence": "MKT", "length": 3, "residues_used": 3, "truncated": False,
                 "predictions": [
                     {"go_term": "GO:A", "name": "general", "aspect": "MF", "score": 0.9, "direct_score": 0.5, "origin": "propagated"},
                     {"go_term": "GO:B", "name": "intermedio", "aspect": "MF", "score": 0.9, "direct_score": 0.6, "origin": "propagated"},
                     {"go_term": "GO:C", "name": "específico", "aspect": "MF", "score": 0.9, "direct_score": 0.9, "origin": "direct"},
                     {"go_term": "GO:D", "name": "otro", "aspect": "MF", "score": 0.5, "direct_score": 0.5, "origin": "direct"}]}]
    r = RunResult("x", "", proteins, "esm2", 0.45, 512, "f" * 64,
                  ancestors={"GO:A": [], "GO:B": ["GO:A"], "GO:C": ["GO:B", "GO:A"], "GO:D": ["GO:A"]})
    assert [x.go_term for x in r.rows(ViewFilter(0.45, specific_only=True))] == ["GO:C", "GO:D"]
    # Si el término específico queda bajo el umbral, su ancestro vuelve a mostrarse.
    assert [x.go_term for x in r.rows(ViewFilter(0.95, specific_only=True))] == []
    summary = r.summary(ViewFilter(0.45, specific_only=True))[0]
    assert summary["counts"] == {"MF": 2, "BP": 0, "CC": 0}
    assert [t["go_term"] for t in summary["top"]["MF"]] == ["GO:C", "GO:D"]


def test_history_migrates_v01_database(tmp_path):
    import sqlite3

    db = tmp_path / "viejo.sqlite3"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,"
                " finished_at TEXT, status TEXT NOT NULL, source_name TEXT NOT NULL, proteins INTEGER NOT NULL,"
                " rejected INTEGER NOT NULL DEFAULT 0, model_kind TEXT NOT NULL, model_fingerprint TEXT NOT NULL,"
                " model_threshold REAL NOT NULL, app_version TEXT NOT NULL, duration_s REAL, message TEXT,"
                " results_gz BLOB)")
    con.execute("INSERT INTO runs (started_at, status, source_name, proteins, model_kind, model_fingerprint,"
                " model_threshold, app_version) VALUES ('2026-11-21T10:00:00','cancelado','a.fasta',1,'esm2','f',0.45,'0.1.0')")
    con.commit()
    con.close()
    h = History(db)
    assert h.list()[0].performance is None
    run = h.start("b.fasta", 1, 0, "esm2", "f", 0.45, "0.2.0")
    h.finish(run, COMPLETED, 1.0, make_result())
    assert h.list()[0].performance == {"seconds": 1.0, "peak_memory_mb": 100.0}
    # Resultados de 0.1.x (sin «ancestors» ni «performance») siguen abriéndose.
    old = make_result().to_dict()
    old.pop("ancestors"), old.pop("performance")
    assert RunResult.from_dict(old).ancestors == {}
