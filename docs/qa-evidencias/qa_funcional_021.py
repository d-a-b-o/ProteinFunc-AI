"""Comprobación adicional sobre Qt offscreen; no controla el escritorio del usuario."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from proteinfunc_app.core.history import History
from proteinfunc_app.ui.main_window import MainWindow
from test_results_history import make_result

out=Path(sys.argv[1]).resolve()
temp=Path(tempfile.mkdtemp(prefix='qa021-functional-'))
app=QApplication([])
w=MainWindow(ROOT/'model',History(temp/'historial.sqlite3'),settings=QSettings(str(temp/'prefs.ini'),QSettings.IniFormat))
w.show()
try:
    tick=time.perf_counter()
    while w.model is None and time.perf_counter()-tick<120:
        app.processEvents(); time.sleep(.02)
    if w.model is None: raise RuntimeError('No cargó modelo en 120 segundos')
    # Carga la fixture sintética existente; no se modifica ninguna prueba.
    w.load_result(make_result()); app.processEvents()
    w.specific_check.setChecked(False)
    w.search.setText('GO:1'); app.processEvents()
    count=w.proxy.rowCount()
    path=w.result.export(out/'exportacion-con-busqueda.json',w.current_view())
    exported=json.loads(path.read_text(encoding='utf-8'))
    terms=[p['go_term'] for r in exported['results'] for p in r['predictions']]
    result={'scope':'Fuente 0.2.1, Qt offscreen, fixture sintética. No ejecutable ni escritorio.',
        'search':'GO:1','visible_rows':count,'exported_prediction_terms':terms,
        'search_pass':count==1,'export_matches_visible':count==1 and terms==['GO:1'],
        'status':'APROBADO' if count==1 and terms==['GO:1'] else 'FALLIDO',
        'expected':'La exportación de resultados visibles solo contiene GO:1 con búsqueda GO:1 activa.',
        'actual':'La búsqueda se aplica al proxy Qt; el exportador recibe current_view() sin búsqueda.',
        'settings_and_history':str(temp)}
    (out/'busqueda-exportacion-qt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
finally:
    w.shutdown(); w.close(); app.processEvents()
