"""Resultados de una ejecución, filtrado y exportación (RF-08, RF-09).

El predictor se llama una sola vez con ``threshold=SCORE_FLOOR``; el deslizador de la
interfaz filtra en memoria sin volver a ejecutar el modelo. Las exportaciones aplican el
mismo filtro que la vista y registran umbral, aspectos y versión del modelo.
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .. import APP_NAME, __version__

SCORE_FLOOR = 0.05          # Puntaje mínimo que se conserva en memoria e historial.
ALL_ASPECTS = ("MF", "BP", "CC")
SCORE_NOTE = ("Los puntajes son salidas sigmoid con propagación por la jerarquía GO; "
              "no son probabilidades calibradas. Que ninguna función supere el umbral "
              "no implica que la proteína carezca de función.")

COLUMNS = ["protein_id", "go_term", "name", "aspect", "score", "direct_score", "origin",
           "length", "residues_used", "truncated"]


@dataclass(frozen=True)
class Row:
    protein_id: str
    go_term: str
    name: str
    aspect: str
    score: float
    direct_score: float
    origin: str
    length: int
    residues_used: int
    truncated: bool


@dataclass
class ViewFilter:
    threshold: float
    aspects: tuple[str, ...] = ALL_ASPECTS
    protein_id: str | None = None      # None = todas.
    include_propagated: bool = True
    specific_only: bool = False        # Ocultar ancestros de otro término visible.
    # Instantánea de la búsqueda Qt: None no limita; conjunto vacío no admite ninguna fila.
    visible_keys: frozenset[tuple[str, str]] | None = None

    def accepts(self, prediction: dict) -> bool:
        return (prediction["score"] >= self.threshold
                and prediction["aspect"] in self.aspects
                and (self.include_propagated or prediction.get("origin", "direct") == "direct"))

    def describe(self) -> dict:
        return {"threshold": round(self.threshold, 4), "aspects": list(self.aspects),
                "protein": self.protein_id or "todas",
                "include_propagated": self.include_propagated,
                "specific_only": self.specific_only}


@dataclass
class RunResult:
    source_name: str
    input_text: str
    proteins: list[dict]                       # Resultados de ProteinGOPredictor (umbral = SCORE_FLOOR).
    model_kind: str
    model_threshold: float
    max_length: int
    fingerprint: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    finished_at: str | None = None
    rejected: list[dict] = field(default_factory=list)  # Registros excluidos por validación.
    app_version: str = __version__
    # Ancestros GO de cada término del vocabulario (del manifiesto), para «solo específicos».
    ancestors: dict[str, list[str]] = field(default_factory=dict)
    # Rendimiento de la ejecución (RNF-05): segundos, memoria máxima, dispositivo, lote…
    performance: dict = field(default_factory=dict)

    # ----- consulta -----
    def protein_ids(self) -> list[str]:
        return [p["id"] for p in self.proteins]

    def protein(self, protein_id: str) -> dict | None:
        return next((p for p in self.proteins if p["id"] == protein_id), None)

    def validate_prediction_keys(self) -> None:
        """La selección por identidad requiere una sola predicción por proteína y término."""
        seen = set()
        for protein in self.proteins:
            for prediction in protein["predictions"]:
                key = (protein["id"], prediction["go_term"])
                if key in seen:
                    raise ValueError(f"Predicción duplicada para proteína y término GO: {key!r}.")
                seen.add(key)

    def visible_predictions(self, protein: dict, view: ViewFilter) -> list[dict]:
        """Predicciones de una proteína que pasan el filtro. Con ``specific_only`` se
        oculta todo término que sea ancestro de otro término visible de la misma proteína."""
        preds = [x for x in protein["predictions"] if view.accepts(x)]
        if view.specific_only and self.ancestors:
            covered = set()
            for x in preds:
                covered.update(self.ancestors.get(x["go_term"], ()))
            preds = [x for x in preds if x["go_term"] not in covered]
        # Después de resolver especificidad: buscar un ancestro oculto no debe recuperarlo.
        if view.visible_keys is not None:
            preds = [x for x in preds if (protein["id"], x["go_term"]) in view.visible_keys]
        return preds

    def rows(self, view: ViewFilter) -> list[Row]:
        out = []
        for p in self.proteins:
            if view.protein_id and p["id"] != view.protein_id:
                continue
            for pred in self.visible_predictions(p, view):
                out.append(Row(p["id"], pred["go_term"], pred["name"], pred["aspect"],
                           float(pred["score"]), float(pred.get("direct_score", pred["score"])),
                           pred.get("origin", "direct"), int(p["length"]),
                           int(p["residues_used"]), bool(p["truncated"])))
        return out

    def all_rows(self) -> list[Row]:
        return self.rows(ViewFilter(threshold=0.0))

    def proteins_without_terms(self, view: ViewFilter) -> list[str]:
        if view.visible_keys is not None:
            # Una búsqueda sin coincidencias no significa «sin funciones sobre el umbral».
            return []
        return [p["id"] for p in self.proteins
                if (not view.protein_id or p["id"] == view.protein_id)
                and not any(view.accepts(x) for x in p["predictions"])]

    def summary(self, view: ViewFilter, top: int = 3) -> list[dict]:
        """Resumen por proteína: funciones por aspecto y las principales de cada uno."""
        out = []
        for p in self.proteins:
            if view.protein_id and p["id"] != view.protein_id:
                continue
            preds = self.visible_predictions(p, view)
            by_aspect = {a: [x for x in preds if x["aspect"] == a] for a in ALL_ASPECTS}
            out.append({"id": p["id"], "length": p["length"], "truncated": p["truncated"],
                        "counts": {a: len(v) for a, v in by_aspect.items()},
                        "top": {a: sorted(v, key=lambda x: -x["score"])[:top] for a, v in by_aspect.items()}})
        return out

    def truncated_proteins(self) -> list[dict]:
        return [p for p in self.proteins if p["truncated"]]

    # ----- metadatos -----
    def metadata(self, view: ViewFilter) -> dict:
        return {
            "application": APP_NAME,
            "app_version": self.app_version,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "run_started_at": self.started_at,
            "run_finished_at": self.finished_at,
            "source": self.source_name,
            "model_kind": self.model_kind,
            "model_fingerprint_sha256": self.fingerprint,
            "model_threshold": self.model_threshold,
            "max_length": self.max_length,
            "filter": view.describe(),
            "proteins_analyzed": len(self.proteins),
            "records_rejected": len(self.rejected),
            "performance": self.performance,
            "note": SCORE_NOTE,
        }

    # ----- exportación -----
    def to_contract(self, view: ViewFilter) -> dict:
        """Misma estructura que ``ProteinGOPredictor.predict`` con el filtro aplicado,
        más una clave ``metadata`` con la configuración de la ejecución."""
        results = []
        for p in self.proteins:
            if view.protein_id and p["id"] != view.protein_id:
                continue
            preds = [dict(x) for x in self.visible_predictions(p, view)]
            if view.visible_keys is not None and not preds:
                continue
            item = {k: p[k] for k in ("id", "sequence", "length", "residues_used", "truncated")}
            item.update(threshold=float(view.threshold), predictions=preds,
                        status="ok" if preds else "no_terms_above_threshold")
            results.append(item)
        return {"schema_version": 1, "model": self.model_kind, "input": self.input_text,
                "results": results, "metadata": self.metadata(view)}

    def to_json(self, view: ViewFilter) -> str:
        return json.dumps(self.to_contract(view), ensure_ascii=False, indent=2)

    def to_delimited(self, view: ViewFilter, delimiter: str) -> str:
        buffer = io.StringIO()
        for key, value in self.metadata(view).items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            buffer.write(f"# {key}: {value}\n")
        writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
        writer.writerow(COLUMNS)
        for r in self.rows(view):
            writer.writerow([r.protein_id, r.go_term, r.name, r.aspect, f"{r.score:.6f}",
                             f"{r.direct_score:.6f}", r.origin, r.length, r.residues_used,
                             "true" if r.truncated else "false"])
        for pid in self.proteins_without_terms(view):
            p = self.protein(pid)
            writer.writerow([pid, "", "Ninguna función superó el umbral", "", "", "", "",
                             p["length"], p["residues_used"], "true" if p["truncated"] else "false"])
        return buffer.getvalue()

    def export(self, path: str | Path, view: ViewFilter, fmt: str | None = None) -> Path:
        path = Path(path)
        fmt = (fmt or path.suffix.lstrip(".")).lower()
        if fmt == "json":
            path.write_text(self.to_json(view), encoding="utf-8")
        elif fmt in {"csv", "tsv"}:
            text = self.to_delimited(view, "," if fmt == "csv" else "\t")
            # UTF-8 con BOM para que Excel en Windows muestre bien los acentos.
            path.write_text(text, encoding="utf-8-sig", newline="")
        else:
            raise ValueError(f"Formato no soportado: {fmt!r} (usa csv, tsv o json)")
        return path

    # ----- persistencia (historial) -----
    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: dict) -> "RunResult":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
