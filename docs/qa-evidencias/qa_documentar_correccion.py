"""Consolida evidencias de QA-021-EXPORT-BUSQUEDA; no sobrescribe registros anteriores."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]; TF=ROOT.parent
OUT=Path(sys.argv[1]).resolve()
REL='EVIDENCIAS/'+OUT.name+'/'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def load(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,data):
    with (OUT/name).open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
def link(name,label=None): return f'[{label or name}]({REL}{name})'
def stats(name):
    tree=ET.parse(OUT/(name+'.xml')); cases=list(tree.iter('testcase'))
    return {'tests':len(cases),'passed':sum(not any(x.find(t) is not None for t in ('failure','error','skipped')) for x in cases),
        'failed':sum(x.find('failure') is not None for x in cases),
        'errors':sum(x.find('error') is not None for x in cases),
        'skipped':sum(x.find('skipped') is not None for x in cases),
        'junit_seconds':float(next(tree.iter('testsuite')).attrib['time'])}
def append(name,text):
    original=(OUT/'HISTORICO'/name).read_bytes()
    assert (QA/name).read_bytes()==original,'El documento cambió durante la auditoría'
    with (QA/name).open('a',encoding='utf-8') as f: f.write('\n\n---\n\n'+text.strip()+'\n')
    assert (QA/name).read_bytes().startswith(original)

before=stats('regresion-antes'); related=stats('pruebas-relacionadas'); full=stats('suite-completa')
assert related['passed']==related['tests']==61 and full['passed']==full['tests']==84
save('resumen-pruebas.json',{'before':before,'related':related,'full':full,'new_regression_cases':41,'base_cases':43})
after=load('despues-comparacion.json')
assert all(v['matches_visible'] for c in after.values() for v in c['formats'].values())
git=['git','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT)]
patch=subprocess.check_output(git+['diff','--','proteinfunc_app/core/results.py','proteinfunc_app/ui/main_window.py'],encoding='utf-8')
(OUT/'correccion-produccion.patch').write_text(patch,encoding='utf-8')
shutil.copy2(ROOT/'tests/test_export_search.py',OUT/'test_export_search.py')
env=subprocess.check_output([str(TF/'.qa-venv-021/Scripts/python.exe'),'-m','pip','freeze'],encoding='utf-8')
(OUT/'dependencias.txt').write_text(env,encoding='utf-8')

previous=load('archivos-previos-sha256.json')
historical_docs={'INFORME_QA.md','MATRIZ_PRUEBAS.md','TRAZABILIDAD.md','RESUMEN_ACADEMICO.md'}
changed=[name for name,value in previous.items() if name not in historical_docs and sha(QA/name)!=value]
assert not changed
version_folder=QA/'EVIDENCIAS/release-0.2.1-20261122'
distributions={}
for version in ('0.2.0','0.2.1'):
    baseline=json.loads((version_folder/f'distribucion-{version}-sha256.json').read_text(encoding='utf-8'))
    directory=TF/f'ProteinFuncAI {version}'
    current={p.relative_to(directory).as_posix():sha(p) for p in directory.rglob('*') if p.is_file()}
    distributions[version]={'added':sorted(set(current)-set(baseline)),
        'missing':sorted(set(baseline)-set(current)),
        'modified':[n for n,v in baseline.items() if n in current and current[n]!=v['sha256']]}
    assert not any(distributions[version].values())
models=json.loads((version_folder/'integridad-modelos.json').read_text(encoding='utf-8'))
model_changed=[n for n,v in models['fuente']['all_files'].items() if sha(ROOT/'model'/n)!=v['sha256']]
assert not model_changed
changed_source=subprocess.check_output(git+['diff','--name-only'],encoding='utf-8').splitlines()
assert set(changed_source)=={'proteinfunc_app/core/results.py','proteinfunc_app/ui/main_window.py'}
diff_check=subprocess.run(git+['diff','--check'],capture_output=True,text=True)
assert diff_check.returncode==0
save('conservacion.json',{'date':dt.datetime.now().astimezone().isoformat(),
    'base_commit':subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip(),
    'tracked_files_modified':changed_source,'production_patch_sha256':sha(OUT/'correccion-produccion.patch'),
    'new_test_sha256':sha(ROOT/'tests/test_export_search.py'),'historical_evidence_modified':changed,
    'source_model_modified':model_changed,'distributions':distributions,'git_diff_check_exit_code':diff_check.returncode,
    'status':subprocess.check_output(git+['status','--short'],text=True),
    'application_version_file_changed':False,'installation':'No se instalaron dependencias en esta corrección.'})

report=f'''# Corrección QA-021-EXPORT-BUSQUEDA

Fecha: {dt.datetime.now().astimezone().isoformat()}. **Estado: APROBADO en fuente local**, tras ejecutar las pruebas relacionadas y la suite completa. Base Git: c38323717be241cfa75d7684d0ff4ab7343270cd, con los cambios sin commit identificados en el patch de evidencia. La versión sigue siendo 0.2.1. Los ejecutables distribuidos 0.2.0 y 0.2.1 no se modificaron y **no incorporan esta corrección**.

## Causa raíz

La tabla usa ViewFilter para umbral, aspecto, proteína y especificidad; posteriormente QSortFilterProxyModel aplica la búsqueda a las columnas visibles, sin distinguir mayúsculas. current_view() omitía esa segunda selección, y export_results() pasaba únicamente el filtro base a RunResult.export(). Por tanto, CSV, TSV y JSON incluían predicciones ocultas por la búsqueda. La evaluación previa reprodujo una fila GO:1 visible y dos términos exportados; sus evidencias permanecen intactas en `EVIDENCIAS/release-0.2.1-20261122/`.

## Solución implementada y archivos

| Archivo | Cambio |
|---|---|
| proteinfunc_app/core/results.py | Campo opcional visible_keys en ViewFilter; intersección común en visible_predictions(); tratamiento de selección vacía; validación de identidad única; omisión de registros sin coincidencias cuando hay selección activa |
| proteinfunc_app/ui/main_window.py | current_view() captura identidades desde el proxy; reconstrucción de tabla y resumen usan include_search=False; aviso de exportación si hay identidades ambiguas |
| tests/test_export_search.py | 41 casos nuevos de regresión con datos sintéticos y archivos/preferencias/SQLite temporales |
| docs/qa-evidencias/ | Este resumen, anexos de QA, scripts de reproducción y evidencias nuevas; documentos anteriores conservados como prefijos exactos y copias |

El proxy conserva su lógica de coincidencias sobre todas las columnas, incluidas etiquetas traducidas, espacios recortados y comparación sin distinción de mayúsculas. No se duplica la lógica de búsqueda en los exportadores. Las claves seleccionadas se aplican después de los filtros de especificidad para evitar que buscar un ancestro oculto vuelva a mostrarlo.

La distinción es explícita mediante `is not None`: `None` conserva el comportamiento anterior sin búsqueda; `frozenset()` representa búsqueda sin coincidencias y exporta cero predicciones. En ese segundo caso JSON conserva el contrato pero tiene results vacío; CSV/TSV conservan metadatos, BOM y cabecera, sin filas de datos. Con búsqueda activa se omiten las proteínas que no tengan predicciones visibles, evitando clasificarlas erróneamente como “sin funciones sobre el umbral”. Sin búsqueda se mantienen esos registros de estado, como antes.

Cada selección conserva pares `(protein_id, go_term)`, no índices visuales. Se permite el mismo GO en proteínas diferentes. validate_prediction_keys() comprueba el resultado completo al capturar una selección activa y rechaza pares duplicados con ValueError; export_results() informa el error sin abrir el diálogo ni escribir archivos. Ordenar el proxy no cambia las identidades seleccionadas. La normalización y rechazo de IDs duplicados ya existen en el validador; el vocabulario GO sin duplicados se verifica en integridad. La nueva guarda también protege resultados históricos malformados cuando se intenta exportarlos con búsqueda activa.

La selección solo pertenece a ViewFilter, no a RunResult ni a SQLite. No se altera el formato exportado (columnas, contrato JSON, estados, codificación ni claves de metadatos) ni la estructura del historial. El resumen de proteínas conserva sus filtros previos; la instantánea del proxy se utiliza para exportar. El orden de las filas exportadas conserva el orden anterior del resultado; la comparación de pruebas verifica pertenencia e identidad frente a la tabla, no reproducción de su orden de clasificación.

## Pruebas añadidas

Los 41 casos en tests/test_export_search.py se descomponen en:

- 33 casos: once escenarios × CSV/TSV/JSON, recorriendo export_results(), un ExportDialog real y su lógica de guardar; únicamente el modal y el selector de ruta se sustituyen por acciones deterministas.
- 3 casos: restablecer búsqueda y cambiar orden de clasificación, con selector de proteína y términos GO compartidos entre proteínas.
- 2 casos: distinción entre selección ausente y vacía.
- 1 caso: identidad única y reapertura de SQLite temporal, sin persistir visible_keys.
- 1 caso: rechazo de claves duplicadas y aviso sin exportación.
- 1 caso: opción de excluir términos propagados aplicada sobre la selección visible.

Se cubren búsqueda por identificador y nombre con acentos/mayúsculas/espacios, combinaciones MF/BP/CC y umbral, ausencia de búsqueda, ausencia de coincidencias, búsqueda de ancestro oculto con “solo específicos”, búsqueda por otras columnas, filtros por proteína y restablecimiento de búsqueda. Los controles verifican cantidades esperadas antes de exportar para evitar aprobaciones vacías. Se comparan pares de identidad y se comprueba ausencia de duplicados y conservación de los formatos.

## Ejecuciones reales

Entorno existente `TF/.qa-venv-021`: Python 3.12.10, pytest 9.2.0, pytest-qt 4.5.0, PySide6/Qt 6.12.0; sin instalaciones adicionales. Se usaron QT_QPA_PLATFORM=offscreen, variables offline y bytecode deshabilitado. {link('dependencias.txt','Versiones exactas')}.

| Ejecución | Casos | Aprobados | Fallidos | Omitidos | Duración pytest | Evidencia |
|---|---:|---:|---:|---:|---:|---|
| Regresiones antes de corregir | 41 | 3 | 38 | 0 | 2.12 s | {link('regresion-antes.log')} |
| Relacionadas, después | 61 | 61 | 0 | 0 | 13.90 s | {link('pruebas-relacionadas.log')} |
| Suite completa, después | 84 | 84 | 0 | 0 | 18.70 s | {link('suite-completa.log')} |

La ejecución anterior de regresiones contiene tanto discrepancias funcionales como errores por las nuevas APIs aún ausentes; no representa 38 defectos independientes. Las capturas de exportación antes/después confirman por separado la discrepancia funcional. La suite final comprende las 43 pruebas originales, sin modificarlas, más 41 nuevas. No se suman las ejecuciones repetidas como casos únicos. Los procesos relacionados y completo finalizaron con código 0; los XML registran cero errores y cero skips. Las pequeñas diferencias de redondeo respecto al atributo time de JUnit no se interpretan como resultados diferentes. Comandos, horas y duraciones de proceso en los JSON homónimos.

Orden ejecutado:

```powershell
# Desde la raíz del repositorio, con el Python del venv QA:
..\\.qa-venv-021\\Scripts\\python.exe -m pytest tests/test_export_search.py tests/test_results_history.py tests/test_gui.py -v
..\\.qa-venv-021\\Scripts\\python.exe -m pytest tests -v
```

En las ejecuciones registradas se añadieron `-p no:cacheprovider`, `--basetemp` nuevo y `--junitxml` para conservar evidencias y evitar escribir cachés en el repositorio. {link('pruebas-relacionadas.json','Comando relacionado exacto')}; {link('suite-completa.json','Comando completo exacto')}; {link('suite-completa.xml','JUnit completo')}.

## Evidencia antes y después

Se capturó la misma fixture sintética en ambos estados: tres proteínas, términos GO compartidos entre P1/P2 y una proteína sin predicciones. Cada escenario se guardó en los tres formatos, sin sobrescribir archivos.

| Búsqueda | Predicciones visibles | Exportación antes, cada formato | Exportación después, cada formato |
|---|---:|---:|---:|
| Sin búsqueda | 5 | 5; se conserva registro de proteína sin términos | 5; mismo comportamiento |
| GO:1 | 2, una por proteína P1/P2 | 5, incorrecto | 2, exactamente las visibles |
| inexistente | 0 | 5, incorrecto | 0; sin registros de proteína añadidos |

{link('antes-comparacion.json','Comparación antes')}; {link('despues-comparacion.json','Comparación después')}. Archivos concretos: {link('antes/GO1.json','JSON antes')}, {link('despues/GO1.json','JSON después')}, {link('despues/GO1.csv','CSV después')}, {link('despues/GO1.tsv','TSV después')}. Las carpetas antes/ y despues/ contienen nueve salidas cada una, incluidas las búsquedas vacías y sin coincidencias. Los términos y secuencias son sintéticos; no constituyen predicciones experimentales.

El nuevo registro no reemplaza la evidencia histórica del caso original de una sola predicción visible; esta fixture amplía la comprobación a dos proteínas con el mismo GO para probar la identidad compuesta.

## Conservación y límites

{link('conservacion.json','Verificación de conservación')} confirma que los dos únicos archivos rastreados modificados son los dos componentes de producción indicados, que el modelo fuente y todos los archivos de las distribuciones 0.2.0/0.2.1 mantienen sus hashes, y que las evidencias anteriores no cambiaron. `git diff --check` aprobó. {link('correccion-produccion.patch','Patch de producción')} y {link('test_export_search.py','Copia exacta de las nuevas pruebas')} permiten identificar el código evaluado sin crear commits.

Los cuatro documentos QA previos se conservaron completos y recibieron únicamente anexos. Sus copias anteriores están en HISTORICO/. No se modificaron inferencia, pesos, versión, pruebas originales, resultados experimentales, ejecutables ni historial real. No se hicieron commits, pushes, compilaciones o releases.

La validación es automatizada sobre código fuente y Qt offscreen; no acredita revisión visual del escritorio. Los binarios distribuidos conservan la implementación anterior, por lo que el defecto no se declara resuelto en ellos. Permanecen pendientes, fuera de esta corrección, la comprobación visual de un futuro binario que incorpore el cambio y la operación con Internet físicamente desconectado. Los metadatos y el campo input de JSON conservan el contrato anterior: la búsqueda limita predicciones exportadas, no elimina el texto FASTA original ni añade un nuevo campo de búsqueda al esquema.

Reproducción de evidencias: [qa_correccion_exportacion.py](qa_correccion_exportacion.py), etapas prepare (solo antes de aplicar el patch y en carpeta nueva), related y full. Las rutas existentes no deben reutilizarse para sobrescribir esta auditoría. [qa_documentar_correccion.py](qa_documentar_correccion.py) añade los documentos solo si siguen coincidiendo con sus copias iniciales.
'''
with (QA/'CORRECCION_EXPORTACION.md').open('x',encoding='utf-8') as f: f.write(report.strip()+'\n')

append('INFORME_QA.md',f'''# Corrección posterior: QA-021-EXPORT-BUSQUEDA

**APROBADO en fuente local 0.2.1 con cambios sin commit sobre c38323717be241cfa75d7684d0ff4ab7343270cd.** El defecto histórico no se elimina del informe: queda resuelto por la selección de identidades visibles del proxy en ViewFilter. Se diferencia None de selección vacía y se rechazan claves ambiguas antes de exportar con búsqueda activa. CSV, TSV y JSON usan la misma intersección. Los formatos y la persistencia se conservan.

Pruebas relacionadas: **61 aprobadas en 13.90 s**. Suite completa: **84 aprobadas en 18.70 s**, cero fallidas, cero errores y cero omitidas: las 43 originales más 41 regresiones nuevas. No se modificaron pruebas existentes. El ensayo de exportación valida el flujo export_results()/ExportDialog, con entradas sintéticas y rutas temporales. Antes: GO:1 deja dos filas visibles y se exportan cinco; después: se exportan esas dos. Sin coincidencias: después se exportan cero predicciones en los tres formatos.

Detalle de causa, solución, archivos, comandos, cobertura y limitaciones: [CORRECCION_EXPORTACION.md](CORRECCION_EXPORTACION.md). {link('suite-completa.xml','JUnit')}; {link('antes-comparacion.json','Antes')}; {link('despues-comparacion.json','Después')}; {link('conservacion.json','Integridad y conservación')}.

La corrección no está en los ejecutables distribuidos, que no fueron modificados ni recompilados. La validación visual de un futuro binario corregido y la desconexión física de Internet permanecen pendientes. No se reevaluó exactitud biológica.
''')
matrix='''# Regresión de la corrección QA-021-EXPORT-BUSQUEDA

Los estados históricos anteriores se mantienen. Este anexo acredita la fuente local corregida, no los ejecutables distribuidos. Suite final: 84 APROBADO, 0 FALLIDO, 0 BLOQUEADO y 0 NO EJECUTADO entre los casos automatizados recolectados; las comprobaciones manuales pendientes conservan su estado anterior.

| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
'''
rows=[('FIX-01','RF-09','Sin búsqueda','Mismas predicciones y estados anteriores','5 predicciones; se conserva proteína sin términos','despues/sin-busqueda.json'),
('FIX-02','RF-08/RF-09','Buscar GO:1','Solo pares visibles','2 visibles y 2 exportados, P1/GO:1 y P2/GO:1','despues/GO1.json'),
('FIX-03','RF-08/RF-09','Nombre, mayúsculas y espacios','Mismas coincidencias que Qt','Regresiones CSV/TSV/JSON aprobadas','pruebas-relacionadas.xml'),
('FIX-04','RF-08/RF-09','Búsqueda + MF/BP/CC y umbral','Intersección de filtros','Tres aspectos y umbrales comprobados','pruebas-relacionadas.xml'),
('FIX-05','RF-09','Sin coincidencias','Cero predicciones, sin volver a todas','JSON results vacío; CSV/TSV solo metadatos y cabecera','despues/sin-coincidencias.json'),
('FIX-06','RF-08/RF-09','Limpiar búsqueda y ordenar','Recuperar datos sin cambiar identidades','None frente a conjunto vacío y orden comprobados','pruebas-relacionadas.xml'),
('FIX-07','RF-09','Identidad compuesta','GO compartido entre proteínas no colisiona','Mismo GO en P1/P2 independiente; pares duplicados rechazados','pruebas-relacionadas.xml'),
('FIX-08','RF-11','Historial y reapertura','Selección temporal sin migraciones','SQLite temporal reabierta; selección no persistida','suite-completa.xml'),
('FIX-09','RF-08/RF-09','Solo específicos y propagados','Mantener filtros anteriores','Ancestro oculto no reaparece; opción de propagados limita selección','suite-completa.xml')]
for cid,req,scenario,expect,got,evidence in rows:
    matrix+=f'| {cid} | {req} | {scenario} | {expect} | {got} | APROBADO | {link(evidence)} |\n'
matrix+=f'\nTodas las regresiones identificadas individualmente en {link("suite-completa.xml")}. El fallo reproducido antes de la implementación se conserva en {link("regresion-antes.log")}; no se cuenta como fallo de la suite final.\n'
append('MATRIZ_PRUEBAS.md',matrix)
append('TRAZABILIDAD.md',f'''# Trazabilidad de la corrección de exportación

| Requisito | Implementación corregida | Regresión | Resultado / evidencia |
|---|---|---|---|
| RF-08/RF-09 | main_window.current_view(): identidades desde el proxy; ViewFilter.visible_keys | test_export_matches_visible_rows y test_search_reset_and_sorting_keep_identity | APROBADO; {link('suite-completa.xml')} |
| RF-09 | RunResult.visible_predictions(), to_contract(), proteins_without_terms() | test_absent_and_empty_selection_are_distinct; once escenarios en tres formatos | APROBADO; {link('despues-comparacion.json')} |
| Identidad única | RunResult.validate_prediction_keys(); guarda en export_results() | test_ambiguous_prediction_keys_are_rejected; identidad P1/GO:1 frente a P2/GO:1 | APROBADO; {link('pruebas-relacionadas.xml')} |
| RF-11 | RunResult/SQLite sin selección persistida ni cambios de esquema | test_prediction_identity_is_unique_across_proteins_and_history más pruebas anteriores | APROBADO; {link('suite-completa.xml')} |
| Conservación de filtros | Reconstrucción y resumen con include_search=False; intersección después de especificidad | Búsqueda de ancestro oculto y test_propagated_export_option_still_limits_visible_selection | APROBADO; {link('suite-completa.xml')} |

Código evaluado: cambios sin commit sobre HEAD c38323717be241cfa75d7684d0ff4ab7343270cd, identificado mediante {link('correccion-produccion.patch')} y sus hashes en {link('conservacion.json')}. Las 43 pruebas previas permanecen y pasan junto con 41 nuevas. Los ejecutables 0.2.0/0.2.1 siguen sin esta corrección. [Resumen de corrección](CORRECCION_EXPORTACION.md).
''')
append('RESUMEN_ACADEMICO.md',f'''# Validación posterior de la corrección de exportación

El defecto QA-021-EXPORT-BUSQUEDA se corrigió en el código fuente local de ProteinFunc AI Desktop 0.2.1, conservando la versión y sin recompilar los ejecutables. La causa era la omisión de la selección del proxy de búsqueda al exportar. Se incorporó una selección temporal por identidad de proteína y término GO, compartida por CSV, TSV y JSON. Se distinguió selección ausente de selección vacía y se comprobó la unicidad de las identidades al capturar la búsqueda.

Con datos sintéticos y Qt sin pantalla, las exportaciones posteriores coincidieron con las predicciones visibles. En el caso GO:1, dos predicciones visibles de proteínas diferentes pasaron de cinco predicciones exportadas antes de corregir a dos después. Una búsqueda sin coincidencias produjo cero predicciones en los tres formatos. La suite completa aprobó 84 pruebas en 18.70 segundos según pytest, con cero fallos y cero omisiones; incluye las 43 anteriores y 41 regresiones nuevas. Antes se habían ejecutado y aprobado las 61 pruebas relacionadas.

La validación acredita la corrección en fuente y conserva las evidencias del defecto original. Los ejecutables distribuidos permanecieron intactos y no incorporan el cambio. Continúan pendientes la revisión visual de un binario que integre la corrección y la comprobación con conectividad física desactivada. No se modificaron modelos ni resultados experimentales ni se reevaluó la exactitud biológica. [Registro técnico y evidencias](CORRECCION_EXPORTACION.md).
''')

broken=[]
for p in QA.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if not target.startswith(('https:','http:','#')) and not (p.parent/target).exists(): broken.append((p.name,target))
assert not broken
save('documentacion-verificada.json',{'historical_prefixes_preserved':True,'broken_links':broken,
    'updated_documents':sorted(historical_docs),'correction_summary':'CORRECCION_EXPORTACION.md'})
save('INDICE_SHA256_CORRECCION.json',{p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='INDICE_SHA256_CORRECCION.json'})
print(json.dumps({'related':related,'full':full,'new_regressions':41,'historical_evidence_unchanged':not changed,'models_and_distributions_unchanged':True}))
