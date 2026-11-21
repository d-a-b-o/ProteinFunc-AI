import json
import shutil

import pytest
from conftest import MODEL_DIR

from proteinfunc_app.core.integrity import verify_bundle


def test_real_bundle_passes_and_matches_checksums():
    report = verify_bundle(MODEL_DIR)
    assert report.ok, [(c.label, c.detail) for c in report.errors]
    assert report.has_checksum_file
    assert all(f.matches for f in report.files)
    assert len(report.fingerprint) == 64


@pytest.fixture
def bundle_copy(tmp_path):
    target = tmp_path / "modelo con espacios"
    shutil.copytree(MODEL_DIR, target)
    return target


def test_tampered_file_is_detected(bundle_copy):
    with open(bundle_copy / "weights.pt", "ab") as handle:
        handle.write(b"\0")
    report = verify_bundle(bundle_copy)
    assert not report.ok
    assert any("SHA256SUMS" in c.label for c in report.errors)


def test_missing_file_is_detected(bundle_copy):
    (bundle_copy / "backbone" / "vocab.txt").unlink()
    report = verify_bundle(bundle_copy)
    assert not report.ok
    assert "vocab.txt" in report.errors[0].detail


def test_inconsistent_manifest_is_detected(bundle_copy):
    manifest = json.loads((bundle_copy / "manifest.json").read_text(encoding="utf-8"))
    manifest["classes"].append(manifest["classes"][0])
    (bundle_copy / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (bundle_copy / "SHA256SUMS").unlink()  # Solo se prueba la coherencia del manifiesto.
    report = verify_bundle(bundle_copy)
    assert any("duplicados" in c.label for c in report.errors)


def test_mixed_versions_are_rejected_when_loading(bundle_copy):
    """Vocabulario de una versión + pesos de otra: el manifiesto abre, pero no se carga."""
    from proteinfunc_app.services import PackageError, load_predictor

    manifest = json.loads((bundle_copy / "manifest.json").read_text(encoding="utf-8"))
    removed = manifest["classes"].pop()
    manifest["label_metadata"].pop(removed)
    for meta in manifest["label_metadata"].values():
        meta["ancestors"] = [a for a in meta["ancestors"] if a != removed]
    (bundle_copy / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (bundle_copy / "SHA256SUMS").unlink()
    with pytest.raises(PackageError, match="versiones mezcladas"):
        load_predictor(bundle_copy)
