"""Auditoría reproducible: solo escribe en docs/qa-evidencias/EVIDENCIAS.
No instala paquetes ni cambia código, modelos o historial del usuario.
"""
import ast
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
DIST = ROOT.parent / 'ProteinFuncAI'
sys.path.insert(0, str(ROOT))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from proteinfunc_app.core.integrity import verify_bundle
from proteinfunc_app.core.validation import validate_text, read_input_file

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def main():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', PYTHONUTF8='1')
    versions = {}
    for name in ['pytest','pytest-qt','numpy','torch','transformers','safetensors','PySide6','psutil']:
        try: versions[name] = md.version(name)
        except md.PackageNotFoundError: versions[name] = None
    tests = {}
    for p in sorted((ROOT/'tests').glob('test_*.py')):
        tests[p.name] = [{'name': n.name, 'line': n.lineno} for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
    save('entorno.json', {'date':dt.datetime.now().astimezone().isoformat(), 'os': platform.platform(),
        'python':sys.version, 'executable':sys.executable, 'machine':platform.machine(),
        'processor':platform.processor(), 'dependencies':versions, 'test_inventory':tests,
        'commit':'c38323717be241cfa75d7684d0ff4ab7343270cd', 'branch':'main'})
    reports = {}
    for label, directory in [('repositorio',ROOT/'model'),('distribucion',DIST/'_internal/model')]:
        r = verify_bundle(directory)
        reports[label] = dict(ok=r.ok, fingerprint=r.fingerprint,
            files=[dataclasses.asdict(f) | {'matches':f.matches} for f in r.files],
            checks=[dataclasses.asdict(c) for c in r.checks])
    reports['comparison'] = [{'path':p.relative_to(ROOT/'model').as_posix(),
        'repository_sha256':digest(p), 'distribution_sha256':digest(DIST/'_internal/model'/p.relative_to(ROOT/'model'))}
        for p in sorted((ROOT/'model').rglob('*')) if p.is_file()]
    save('integridad_modelos.json', reports)
    save('hashes_distribucion.json', {p.name: {'bytes':p.stat().st_size, 'sha256':digest(p)} for p in DIST.glob('*.exe') if not p.name.startswith('unins')})
    validation = {}
    for p in sorted((ROOT/'examples').rglob('*')):
        if p.suffix not in ('.fasta','.txt'): continue
        r = validate_text(read_input_file(p),512)
        validation[str(p.relative_to(ROOT))] = {'summary':r.summary(), 'global_errors':r.global_errors,
            'records':[{'id':x.record_id,'status':x.status,'length':len(x.sequence),'accepted':x.accepted,'messages':x.messages} for x in r.records]}
    r=validate_text('  \n',512)
    validation['empty_input']={'global_errors':r.global_errors,'accepted':len(r.accepted)}
    save('validacion_ejemplos.json',validation)
    # La selección evita imports de dependencias ausentes; no se cambia ninguna prueba.
    cmd=[sys.executable,'-m','pytest','tests/test_validation.py','tests/test_results_history.py',
         'tests/test_integrity.py','-v','-k','not validation_agrees_with_runtime_parser and not mixed_versions_are_rejected_when_loading',
         '-p','no:cacheprovider','--basetemp',tempfile.mkdtemp(prefix='proteinfunc-qa-pytest-'),
         '--junitxml',str(OUT/'pytest-subconjunto.xml')]
    start=dt.datetime.now().astimezone().isoformat(); tick=time.perf_counter()
    proc=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/'pytest-subconjunto.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    save('pytest-ejecucion.json',{'command':cmd,'start':start,'end':dt.datetime.now().astimezone().isoformat(),
         'seconds':time.perf_counter()-tick,'exit_code':proc.returncode})
    # El comprobador empaquetado no abre SQLite ni la GUI.
    cmd=[str(DIST/'proteinfunc-check.exe'),str(ROOT/'examples/muestra.fasta')]
    start=dt.datetime.now().astimezone().isoformat(); tick=time.perf_counter()
    try:
        proc=subprocess.run(cmd,cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
        (OUT/'ejecutable-check.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        save('ejecutable-check.json',{'command':cmd,'start':start,'seconds':time.perf_counter()-tick,
            'exit_code':proc.returncode,'network':'HF_HUB_OFFLINE=1; TRANSFORMERS_OFFLINE=1. Red del sistema no desactivada.'})
    except Exception as exc:
        save('ejecutable-check.json',{'command':cmd,'start':start,'seconds':time.perf_counter()-tick,'error':str(exc)})
    print('Evidencias guardadas en',OUT)

if __name__ == '__main__': main()
