import os
import subprocess
import sys

from conftest import EXAMPLES, ROOT


def test_check_runs_from_other_directory_with_spaces(tmp_path):
    workdir = tmp_path / "carpeta con espacios"
    workdir.mkdir()
    env = dict(os.environ, PYTHONPATH=str(ROOT), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               PYTHONUTF8="1")
    proc = subprocess.run([sys.executable, "-m", "proteinfunc_app", "--check", str(EXAMPLES / "muestra.fasta")],
                          cwd=workdir, env=env, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '"ok": true' in proc.stdout and "P01308" in proc.stdout
