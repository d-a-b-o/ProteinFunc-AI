"""Evidencias antes/después; usar prepare una sola vez por carpeta nueva."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
TF=ROOT.parent
OUT=Path(sys.argv[2]).resolve()
PY=TF/'.qa-venv-021/Scripts/python.exe'

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def run(name,tests):
    import time
    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',
             QT_QPA_PLATFORM='offscreen',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    cmd=[str(PY),'-m','pytest',*tests,'-v','-p','no:cacheprovider',
         '--basetemp',tempfile.mkdtemp(prefix='qa-export-fix-'),'--junitxml',str(OUT/(name+'.xml'))]
    start=dt.datetime.now().astimezone().isoformat(); tick=time.perf_counter()
    p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=900)
    (OUT/(name+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    save(name+'.json',{'command':cmd,'start':start,'seconds':time.perf_counter()-tick,'exit_code':p.returncode})
    print(name,p.returncode,p.stdout[-600:],flush=True)

def capture(stage):
    os.environ['QT_QPA_PLATFORM']='offscreen'
    sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from types import SimpleNamespace
    from unittest.mock import patch
    from proteinfunc_app.core.history import History
    from proteinfunc_app.ui import main_window as mw
    from test_export_search import synthetic_result,proxy_keys,exported_keys
    target=OUT/stage; target.mkdir()
    temp=Path(tempfile.mkdtemp(prefix='qa-export-capture-'))
    app=QApplication([])
    def idle(self,device): self.worker=SimpleNamespace(isRunning=lambda:False)
    results={}
    with patch.object(mw.MainWindow,'_start_worker',idle):
        w=mw.MainWindow(temp/'sin-modelo',History(temp/'historial.sqlite3'),
                       settings=QSettings(str(temp/'prefs.ini'),QSettings.IniFormat))
    try:
        w.show(); w.load_result(synthetic_result()); w.specific_check.setChecked(False)
        for label,query in [('sin-busqueda',''),('GO1','GO:1'),('sin-coincidencias','inexistente')]:
            w.search.setText(query); app.processEvents()
            visible=proxy_keys(w); formats={}
            for fmt in ('csv','tsv','json'):
                path=target/f'{label}.{fmt}'
                w.result.export(path,w.current_view())
                keys,_=exported_keys(path,fmt)
                formats[fmt]={'exported_keys':keys,'matches_visible':sorted(keys)==sorted(visible)}
            results[label]={'query':query,'visible_keys':visible,'formats':formats}
    finally:
        w.close(); app.processEvents()
    save(stage+'-comparacion.json',results)
    print(stage,results,flush=True)

if sys.argv[1]=='prepare':
    OUT.mkdir(parents=True,exist_ok=False)
    old={p.relative_to(QA).as_posix():sha(p) for p in QA.rglob('*') if p.is_file() and OUT not in p.parents}
    save('archivos-previos-sha256.json',old)
    archive=OUT/'HISTORICO'; archive.mkdir()
    for name in ['INFORME_QA.md','MATRIZ_PRUEBAS.md','TRAZABILIDAD.md','RESUMEN_ACADEMICO.md']:
        shutil.copy2(QA/name,archive/name)
    save('fuente-antes-sha256.json',{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'proteinfunc_app/core/results.py',ROOT/'proteinfunc_app/ui/main_window.py']})
    capture('antes')
    run('regresion-antes',['tests/test_export_search.py'])
elif sys.argv[1]=='related':
    capture('despues')
    run('pruebas-relacionadas',['tests/test_export_search.py','tests/test_results_history.py','tests/test_gui.py'])
elif sys.argv[1]=='full':
    run('suite-completa',['tests'])
