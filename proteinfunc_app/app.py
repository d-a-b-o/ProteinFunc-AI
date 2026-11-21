"""Punto de entrada de ProteinFunc AI Desktop.

Uso:
    python -m proteinfunc_app                 # interfaz gráfica
    python -m proteinfunc_app --check [FASTA] # verificación sin interfaz (paquete + predicción)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import APP_NAME, __version__
from .paths import examples_dir, model_dir


def _history_path() -> Path:
    from PySide6.QtCore import QStandardPaths

    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return Path(base or Path.home() / ".proteinfunc_ai") / "historial.sqlite3"


def run_check(bundle: Path, fasta: Path | None) -> int:
    """Verificación por consola: integridad, carga y una predicción. Útil para probar
    una instalación nueva con la red deshabilitada."""
    from .core.validation import read_input_file, validate_text
    from .services import PackageError, load_predictor, run_prediction

    print(f"{APP_NAME} {__version__}")
    print(f"Paquete: {bundle}")
    try:
        loaded = load_predictor(bundle)
    except PackageError as exc:
        print(f"ERROR: {exc}")
        return 2
    for check in loaded.report.checks:
        print(f"  [{'OK' if check.ok else 'FALLA'}] {check.label}: {check.detail}")
    print(f"Huella del paquete (SHA-256): {loaded.report.fingerprint}")
    print(f"Modelo cargado en {loaded.load_seconds:.1f} s ({loaded.device})")

    fasta = fasta or examples_dir() / "muestra.fasta"
    report = validate_text(read_input_file(fasta), loaded.predictor.manifest["max_length"])
    print(f"Entrada {fasta.name}: {report.summary()}")
    results = run_prediction(loaded.predictor, report.as_records())
    threshold = loaded.predictor.manifest["threshold"]
    for r in results:
        above = [p for p in r["predictions"] if p["score"] >= threshold]
        top = ", ".join(f"{p['go_term']} {p['aspect']} {p['score']:.3f}" for p in above[:3])
        print(f"  {r['id']}: {len(above)} funciones ≥ {threshold}" + (f" — {top}" if top else ""))
    print(json.dumps({"ok": True, "proteins": len(results)}))
    return 0


def _ensure_std_streams() -> None:
    """En el .exe de Windows sin consola, sys.stdout/stderr son None; cualquier escritura
    (avisos de librerías, barras de progreso) fallaría. Se redirigen a un registro."""
    for stream in (sys.stdout, sys.stderr):
        # Consolas de Windows con cp1252: evitar errores con «≥», «✓», etc.
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (OSError, ValueError):
                pass
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_dir = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "state") / "ProteinFuncAI"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        stream = open(log_dir / "proteinfunc.log", "a", encoding="utf-8", buffering=1)
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


def main(argv: list[str] | None = None) -> int:
    _ensure_std_streams()
    parser = argparse.ArgumentParser(prog="proteinfunc_app", description=APP_NAME)
    parser.add_argument("--model", type=Path, help="Carpeta del paquete de modelo (por defecto model/)")
    parser.add_argument("--check", nargs="?", const="", metavar="FASTA",
                        help="Verificar paquete y predecir un FASTA sin abrir la interfaz")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    args = parser.parse_args(argv)
    bundle = args.model.expanduser().resolve() if args.model else model_dir()

    if args.check is not None:
        return run_check(bundle, Path(args.check) if args.check else None)

    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication

    from .core.history import History
    from .ui import theme
    from .ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("ProteinFuncAI")
    app.setOrganizationName("USIL-Bioinformatica")
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    font = QFont(theme.FONT_FAMILY, 10)
    app.setFont(font)
    app.setStyle(theme.AppStyle())
    app.setStyleSheet(theme.STYLESHEET)
    icon = Path(__file__).with_name("icon.png")
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))

    window = MainWindow(bundle, History(_history_path()))
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
