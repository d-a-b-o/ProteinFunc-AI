"""Validación de entrada (RF-01, RF-02).

``protein_go.parse_input`` se detiene en el primer error. Aquí se revisan *todos* los
registros para que la interfaz indique cuál requiere corrección. Se aplican exactamente
las mismas reglas que el runtime (alfabeto, normalización, IDs ``sp|``/``tr|``), de modo
que un registro aceptado aquí es aceptado también por ``ProteinGOPredictor``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWYXBZOUJ"  # Igual que protein_go.AMINO_ACIDS.
_ALLOWED = set(AMINO_ACIDS)

OK, WARNING, ERROR = "ok", "warning", "error"


def protein_id(header: str) -> str:
    """Misma normalización que protein_go.protein_id."""
    first = header.split()[0]
    fields = first.split("|")
    return fields[1] if len(fields) >= 3 and fields[0] in {"sp", "tr"} else first


def clean_sequence(raw: str) -> str:
    """Misma normalización que protein_go.normalize_sequence, sin lanzar excepciones."""
    sequence = re.sub(r"\s+", "", raw).upper()
    if sequence.endswith("*"):
        sequence = sequence[:-1]
    return sequence


@dataclass
class RecordCheck:
    index: int                 # Posición 1..N en la entrada.
    line: int                  # Línea de la cabecera (1-based); 1 para secuencia cruda.
    record_id: str
    header: str
    sequence: str              # Secuencia normalizada (completa, nunca truncada).
    status: str = OK
    messages: list[str] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def accepted(self) -> bool:
        return self.status != ERROR


@dataclass
class ValidationReport:
    records: list[RecordCheck]
    global_errors: list[str]
    max_length: int | None

    @property
    def accepted(self) -> list[RecordCheck]:
        return [r for r in self.records if r.accepted] if not self.global_errors else []

    @property
    def rejected(self) -> list[RecordCheck]:
        return [r for r in self.records if not r.accepted]

    @property
    def warnings(self) -> list[RecordCheck]:
        return [r for r in self.records if r.status == WARNING]

    @property
    def is_clean(self) -> bool:
        return not self.global_errors and not self.rejected

    def summary(self) -> str:
        if self.global_errors:
            return self.global_errors[0]
        total, ok = len(self.records), len(self.accepted)
        text = f"{total} registro{'s' if total != 1 else ''} · {ok} válido{'s' if ok != 1 else ''}"
        if self.rejected:
            text += f" · {len(self.rejected)} con error"
        if self.warnings:
            text += f" · {len(self.warnings)} con aviso"
        return text

    def as_records(self) -> list[tuple[str, str]]:
        """Pares (id, secuencia) listos para ``predict_records``."""
        return [(r.record_id, r.sequence) for r in self.accepted]


def _check_sequence(check: RecordCheck, max_length: int | None) -> None:
    if not check.sequence:
        check.status = ERROR
        check.messages.append("La secuencia está vacía.")
        return
    invalid = sorted(set(check.sequence) - _ALLOWED)
    if invalid:
        positions = [i + 1 for i, aa in enumerate(check.sequence) if aa not in _ALLOWED]
        shown = ", ".join(str(p) for p in positions[:5]) + ("…" if len(positions) > 5 else "")
        symbols = " ".join(repr(c) for c in invalid)
        check.status = ERROR
        check.messages.append(f"Símbolos no admitidos {symbols} en las posiciones {shown}.")
        return
    if max_length and check.length > max_length:
        check.status = WARNING
        check.messages.append(
            f"Secuencia de {check.length} residuos: el modelo usará solo los primeros {max_length}.")


def validate_text(text: str, max_length: int | None = None) -> ValidationReport:
    """Valida una secuencia cruda o un texto FASTA con uno o varios registros."""
    if not text or not text.strip():
        return ValidationReport([], ["La entrada está vacía: carga un FASTA o pega una secuencia."], max_length)

    lines = text.splitlines()
    if not text.lstrip().startswith(">"):
        check = RecordCheck(1, 1, "query_1", "query_1", clean_sequence(text))
        _check_sequence(check, max_length)
        return ValidationReport([check], [], max_length)

    records: list[RecordCheck] = []
    current: RecordCheck | None = None
    chunks: list[str] = []

    def close():
        if current is not None:
            current.sequence = clean_sequence("".join(chunks))
            if current.status != ERROR:
                _check_sequence(current, max_length)

    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            close()
            header = line[1:].strip()
            current = RecordCheck(len(records) + 1, number, protein_id(header) if header else "",
                                  header, "")
            if not header:
                current.status = ERROR
                current.messages.append("Cabecera FASTA vacía: falta el identificador después de '>'.")
            records.append(current)
            chunks = []
        else:
            chunks.append(line)
    close()

    seen: dict[str, RecordCheck] = {}
    for check in records:
        if not check.record_id:
            continue
        if check.record_id in seen:
            first = seen[check.record_id]
            check.status = ERROR
            check.messages.insert(0, f"Identificador duplicado: ya aparece en el registro {first.index} "
                                     f"(línea {first.line}).")
        else:
            seen[check.record_id] = check

    return ValidationReport(records, [], max_length)


def read_input_file(path: str | Path) -> str:
    """Lee un FASTA/TXT. Acepta UTF-8 (con o sin BOM) y, como respaldo, Latin-1."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")
