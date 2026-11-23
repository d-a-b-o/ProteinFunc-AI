"""Conserva salidas pequeñas, verifica filtros y mide el CLI con entrada inválida."""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import psutil

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_results_history import make_result
from proteinfunc_app.core.results import ViewFilter

r=make_result()
checks=[]
for aspect in ('MF','BP','CC'):
    rows=r.rows(ViewFilter(0.1,aspects=(aspect,)))
    checks.append({'aspect':aspect,'terms':[x.go_term for x in rows],
                   'pass':bool(rows) and all(x.aspect==aspect for x in rows)})
counts=[len(r.rows(ViewFilter(t))) for t in (0.1,0.45,0.95)]
checks.append({'thresholds':[0.1,0.45,0.95],'counts':counts,'pass':counts==[4,2,0]})
for fmt in ('csv','tsv','json'):
    r.export(OUT/f'exportacion_sintetica.{fmt}',ViewFilter(0.45))
(OUT/'filtros_adicionales.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')

# Sacar las copias desechables del modelo del directorio de evidencias.
# Solo mueve el árbol nuevo creado por esta auditoría; no elimina archivos.
created=OUT/'pytest-temporales'
if created.exists():
    assert created.resolve().parent==OUT.resolve() and created.name=='pytest-temporales'
    dest=Path(tempfile.mkdtemp(prefix='proteinfunc-qa-temporales-'))/'pytest-temporales'
    assert dest.parent.is_dir() and not dest.exists()
    shutil.move(str(created),str(dest))
    (OUT/'temporales.json').write_text(json.dumps({'moved_from':str(created),'moved_to':str(dest),
        'reason':'Copias temporales del modelo y SQLite de pruebas; fuera del paquete de evidencias.'},indent=2),encoding='utf-8')

env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1',HF_HUB_OFFLINE='1',
         TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
cmd=[str(ROOT.parent/'ProteinFuncAI/proteinfunc-check.exe'),str(ROOT/'examples/con_errores.fasta')]
start=dt.datetime.now().astimezone().isoformat(); tick=time.perf_counter(); peak=0; samples=0
with (OUT/'ejecutable-errores.log').open('wb') as out:
    proc=subprocess.Popen(cmd,cwd=OUT,env=env,stdout=out,stderr=subprocess.STDOUT)
    monitor=psutil.Process(proc.pid)
    while proc.poll() is None:
        try:
            info=monitor.memory_info(); peak=max(peak,info.rss,getattr(info,'peak_wset',0)); samples+=1
        except psutil.Error: pass
        if time.perf_counter()-tick>300:
            raise TimeoutError('Comprobador excedió 300 segundos')
        time.sleep(0.05)
duration=time.perf_counter()-tick
(OUT/'rendimiento-cli.json').write_text(json.dumps({'command':cmd,'start':start,'seconds':duration,
    'exit_code':proc.returncode,'peak_working_set_bytes':peak,'samples':samples,
    'scope':'Proceso CLI: inicio, integridad, carga, validación e inferencia. No es tiempo de inferencia aislado.',
    'network':'Variables offline; red física no desconectada.'},indent=2),encoding='utf-8')
assert all(c['pass'] for c in checks)
print('Filtros adicionales aprobados; comprobador terminado:',proc.returncode)
