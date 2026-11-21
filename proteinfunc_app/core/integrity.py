"""Verificación del paquete de modelo antes de analizar (RF-06, RNF-06).

Comprueba que estén los archivos obligatorios, que el manifiesto sea coherente y calcula
SHA-256 de cada archivo. Si existe ``model/SHA256SUMS`` se comparan las huellas
calculadas con las esperadas; cualquier diferencia bloquea el análisis.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

CHECKSUM_FILE = "SHA256SUMS"
ASPECTS = ("MF", "BP", "CC")
TRANSFORMER_KINDS = {"esm2", "protbert"}
BACKBONE_FILES = ("config.json", "model.safetensors", "tokenizer_config.json", "vocab.txt")


def required_files(manifest: dict | None) -> list[str]:
    files = ["manifest.json", "weights.pt"]
    kind = (manifest or {}).get("model_spec", {}).get("kind")
    if kind in TRANSFORMER_KINDS:
        files += [f"backbone/{name}" for name in BACKBONE_FILES]
    return files


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checksums(path: Path) -> dict[str, str]:
    """Formato de ``sha256sum``: ``<hash>  <ruta relativa>`` por línea."""
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, name = line.split(maxsplit=1)
        result[name.lstrip("*").strip()] = digest.lower()
    return result


def write_checksums(bundle_dir: Path) -> Path:
    bundle_dir = Path(bundle_dir)
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    lines = [f"{sha256_file(bundle_dir / name)}  {name}" for name in required_files(manifest)]
    target = bundle_dir / CHECKSUM_FILE
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return target


@dataclass
class FileDigest:
    name: str
    size: int
    sha256: str
    expected: str | None = None

    @property
    def matches(self) -> bool | None:
        return None if self.expected is None else self.expected == self.sha256


@dataclass
class Check:
    label: str
    ok: bool
    detail: str = ""


@dataclass
class IntegrityReport:
    bundle_dir: Path
    manifest: dict | None = None
    files: list[FileDigest] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    has_checksum_file: bool = False

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def errors(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]

    @property
    def fingerprint(self) -> str:
        """Huella del paquete completo: SHA-256 de la lista ordenada «ruta:sha256»."""
        payload = "\n".join(f"{f.name}:{f.sha256}" for f in sorted(self.files, key=lambda f: f.name))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def short_fingerprint(self) -> str:
        return self.fingerprint[:12]

    def add(self, label: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(label, ok, detail))


def _check_manifest(report: IntegrityReport, manifest: dict) -> None:
    report.add("Versión de esquema del manifiesto", manifest.get("schema_version") == 1,
               f"schema_version = {manifest.get('schema_version')!r} (se admite 1)")

    classes = manifest.get("classes") or []
    metadata = manifest.get("label_metadata") or {}
    unique = len(set(classes)) == len(classes) and len(classes) > 0
    report.add("Vocabulario GO ordenado y sin duplicados", unique, f"{len(classes)} términos")

    missing = [c for c in classes if c not in metadata]
    report.add("Metadatos para cada término del vocabulario", not missing,
               f"faltan {len(missing)}: {', '.join(missing[:3])}" if missing else "nombre, aspecto y ancestros")

    bad_aspect = [c for c in classes if metadata.get(c, {}).get("aspect") not in ASPECTS]
    report.add("Aspecto MF/BP/CC válido en cada término", not bad_aspect,
               f"{len(bad_aspect)} términos con aspecto desconocido" if bad_aspect else "")

    class_set = set(classes)
    orphan = [a for c in classes for a in metadata.get(c, {}).get("ancestors", []) if a not in class_set]
    report.add("Ancestros GO dentro del vocabulario", not orphan,
               f"{len(orphan)} referencias externas" if orphan else "reglas is_a / part_of coherentes")

    threshold = manifest.get("threshold")
    report.add("Umbral operativo en [0, 1]", isinstance(threshold, (int, float)) and 0 <= threshold <= 1,
               f"umbral = {threshold!r}")
    max_length = manifest.get("max_length")
    report.add("Longitud máxima positiva", isinstance(max_length, int) and max_length > 0,
               f"max_length = {max_length!r}")
    kind = manifest.get("model_spec", {}).get("kind")
    report.add("Tipo de modelo reconocido", kind in TRANSFORMER_KINDS | {"cnn", "bilstm"}, f"kind = {kind!r}")


def verify_bundle(bundle_dir: str | Path) -> IntegrityReport:
    """Verificación rápida (sin PyTorch). Las dimensiones de los pesos se comprueban al
    cargar el modelo con ``load_state_dict(strict=True)`` (ver services.check_dimensions)."""
    bundle_dir = Path(bundle_dir)
    report = IntegrityReport(bundle_dir)

    manifest_path = bundle_dir / "manifest.json"
    if not bundle_dir.is_dir():
        report.add("Carpeta del modelo", False, f"No existe: {bundle_dir}")
        return report
    if not manifest_path.is_file():
        report.add("Archivo manifest.json", False, f"No se encontró en {bundle_dir}")
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report.manifest = manifest
    except (OSError, ValueError) as exc:
        report.add("Archivo manifest.json legible", False, str(exc))
        return report

    names = required_files(manifest)
    missing = [n for n in names if not (bundle_dir / n).is_file()]
    report.add("Archivos obligatorios presentes", not missing,
               "Faltan: " + ", ".join(missing) if missing else f"{len(names)} archivos")

    checksum_path = bundle_dir / CHECKSUM_FILE
    expected = {}
    if checksum_path.is_file():
        report.has_checksum_file = True
        try:
            expected = read_checksums(checksum_path)
        except ValueError as exc:
            report.add("Archivo SHA256SUMS legible", False, str(exc))

    for name in names:
        path = bundle_dir / name
        if path.is_file():
            report.files.append(FileDigest(name, path.stat().st_size, sha256_file(path), expected.get(name)))

    if report.has_checksum_file:
        mismatched = [f.name for f in report.files if f.matches is False]
        unlisted = [f.name for f in report.files if f.expected is None]
        report.add("Huellas SHA-256 coinciden con SHA256SUMS", not mismatched and not unlisted,
                   ("Difieren: " + ", ".join(mismatched)) if mismatched else
                   ("Sin huella registrada: " + ", ".join(unlisted)) if unlisted else
                   f"{len(report.files)} archivos verificados")

    _check_manifest(report, manifest)
    return report
