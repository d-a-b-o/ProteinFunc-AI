"""Historial local de ejecuciones en SQLite (RF-11). Sin servidor externo.

Cada ejecución se registra al iniciar con estado ``en_curso`` y se cierra como
``completado``, ``cancelado`` o ``fallido``. Solo las completadas guardan resultados, de
modo que una interrupción nunca se presenta como un análisis terminado (RF-10).
"""
from __future__ import annotations

import gzip
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .results import RunResult

RUNNING, COMPLETED, CANCELLED, FAILED = "en_curso", "completado", "cancelado", "fallido"
STATUS_LABELS = {RUNNING: "En curso", COMPLETED: "Completado", CANCELLED: "Cancelado", FAILED: "Fallido"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at       TEXT NOT NULL,
    finished_at      TEXT,
    status           TEXT NOT NULL,
    source_name      TEXT NOT NULL,
    proteins         INTEGER NOT NULL,
    rejected         INTEGER NOT NULL DEFAULT 0,
    model_kind       TEXT NOT NULL,
    model_fingerprint TEXT NOT NULL,
    model_threshold  REAL NOT NULL,
    app_version      TEXT NOT NULL,
    duration_s       REAL,
    message          TEXT,
    results_gz       BLOB
);
CREATE INDEX IF NOT EXISTS runs_started ON runs(started_at);
CREATE INDEX IF NOT EXISTS runs_fingerprint ON runs(model_fingerprint);
"""


@dataclass
class RunSummary:
    id: int
    started_at: str
    finished_at: str | None
    status: str
    source_name: str
    proteins: int
    rejected: int
    model_kind: str
    model_fingerprint: str
    model_threshold: float
    app_version: str
    duration_s: float | None
    message: str | None
    has_results: bool

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)


class History:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(_SCHEMA)
            # Una ejecución que quedó «en curso» se interrumpió (cierre o fallo de la app).
            con.execute("UPDATE runs SET status=?, message=COALESCE(message, ?) WHERE status=?",
                        (FAILED, "Interrumpida: la aplicación se cerró antes de terminar.", RUNNING))

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def start(self, source_name: str, proteins: int, rejected: int, model_kind: str,
              fingerprint: str, threshold: float, app_version: str) -> int:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO runs (started_at, status, source_name, proteins, rejected, model_kind,"
                " model_fingerprint, model_threshold, app_version) VALUES (?,?,?,?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), RUNNING, source_name, proteins, rejected,
                 model_kind, fingerprint, threshold, app_version))
            return int(cur.lastrowid)

    def finish(self, run_id: int, status: str, duration_s: float | None = None,
               result: RunResult | None = None, message: str | None = None) -> None:
        if status not in (COMPLETED, CANCELLED, FAILED):
            raise ValueError(f"Estado final no válido: {status}")
        blob = None
        if status == COMPLETED and result is not None:
            blob = gzip.compress(json.dumps(result.to_dict(), ensure_ascii=False).encode("utf-8"))
        with self._connect() as con:
            con.execute("UPDATE runs SET status=?, finished_at=?, duration_s=?, message=?, results_gz=?"
                        " WHERE id=?",
                        (status, datetime.now().isoformat(timespec="seconds"), duration_s, message, blob,
                         run_id))

    def list(self, date_from: str | None = None, date_to: str | None = None,
             fingerprint: str | None = None, status: str | None = None) -> list[RunSummary]:
        """Fechas en formato ISO ``AAAA-MM-DD`` (inclusive)."""
        query = ("SELECT id, started_at, finished_at, status, source_name, proteins, rejected, model_kind,"
                 " model_fingerprint, model_threshold, app_version, duration_s, message,"
                 " results_gz IS NOT NULL AS has_results FROM runs WHERE 1=1")
        params: list = []
        if date_from:
            query += " AND substr(started_at, 1, 10) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND substr(started_at, 1, 10) <= ?"
            params.append(date_to)
        if fingerprint:
            query += " AND model_fingerprint = ?"
            params.append(fingerprint)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY started_at DESC, id DESC"
        with self._connect() as con:
            return [RunSummary(**{**dict(r), "has_results": bool(r["has_results"])})
                    for r in con.execute(query, params)]

    def fingerprints(self) -> list[tuple[str, str]]:
        """Versiones del modelo usadas: (huella, tipo)."""
        with self._connect() as con:
            return [(r[0], r[1]) for r in con.execute(
                "SELECT model_fingerprint, model_kind FROM runs GROUP BY model_fingerprint"
                " ORDER BY MAX(started_at) DESC")]

    def load(self, run_id: int) -> RunResult | None:
        with self._connect() as con:
            row = con.execute("SELECT results_gz FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None or row[0] is None:
            return None
        return RunResult.from_dict(json.loads(gzip.decompress(row[0]).decode("utf-8")))

    def delete(self, run_id: int) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM runs WHERE id=?", (run_id,))
