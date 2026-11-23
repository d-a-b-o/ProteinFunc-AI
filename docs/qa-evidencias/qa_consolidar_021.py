"""Añade la evaluación 0.2.1 sin reemplazar resultados ni evidencias anteriores."""
import datetime as dt
import gzip
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
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def link(name,label=None): return f'[{label or name}]({REL}{name})'
def append(name,text):
    archive=(OUT/'HISTORICO'/name).read_bytes()
    assert (QA/name).read_bytes()==archive, 'El documento cambió desde la copia; revisar antes de anexar.'
    with (QA/name).open('a',encoding='utf-8') as f: f.write('\n\n---\n\n'+text.strip()+'\n')

tree=ET.parse(OUT/'pytest-completo-021.xml')
cases=list(tree.iter('testcase'))
stats={'tests':len(cases),'passed':sum(x.find('failure') is None and x.find('error') is None and x.find('skipped') is None for x in cases),
    'failed':sum(x.find('failure') is not None for x in cases),'errors':sum(x.find('error') is not None for x in cases),
    'skipped':sum(x.find('skipped') is not None for x in cases)}
suite=next(tree.iter('testsuite'))
stats['junit_seconds']=float(suite.attrib['time'])
save('resumen-pytest-021.json',stats)
models=load('integridad-modelos.json')
fingerprint=models['0.2.1']['fingerprint']
versions={v:load(f'distribucion-{v}-sha256.json') for v in ('0.2.0','0.2.1')}
bug=load('busqueda-exportacion-qt.json')
old_env=json.loads((QA/'EVIDENCIAS/entorno.json').read_text(encoding='utf-8'))
old_passed={x.attrib['name'] for x in ET.parse(QA/'EVIDENCIAS/pytest-subconjunto.xml').iter('testcase')}
pending=[(f,t) for f,tests in old_env['test_inventory'].items() for t in tests if t['name'] not in old_passed]
now_passed={x.attrib['name'] for x in cases if x.find('failure') is None and x.find('error') is None and x.find('skipped') is None}
assert len(pending)==21 and all(t['name'] in now_passed for _,t in pending)

# Conserva íntegro el log bruto fuera del paquete ligero; guarda copia comprimida.
raw=OUT/'instalacion-dependencias.log'
raw_hash=sha(raw); raw_size=raw.stat().st_size
compressed=OUT/'instalacion-dependencias.log.gz'
with raw.open('rb') as src,gzip.open(compressed,'xb') as dst: shutil.copyfileobj(src,dst)
dest=TF/'.qa-venv-021/QA_REGISTROS/instalacion-dependencias-release021.log'
assert dest.resolve().is_relative_to((TF/'.qa-venv-021').resolve()) and not dest.exists()
dest.parent.mkdir(exist_ok=True)
shutil.move(str(raw),str(dest))
save('registro-instalacion.json',{'authorization':'Usuario autorizó venv y dependencias; red adicional autorizada tras WinError 10013.',
    'venv':str(TF/'.qa-venv-021'),'include_system_site_packages':False,'raw_log':str(dest),
    'raw_bytes':raw_size,'raw_sha256':raw_hash,'compressed_log':compressed.name,
    'commands':['python -m venv .qa-venv-021',
        '.qa-venv-021/Scripts/python.exe -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu',
        '.qa-venv-021/Scripts/python.exe -m pip install -r ProteinFunc-AI/requirements.txt pytest pytest-qt'],
    'notes':'Primer intento torch bloqueado por sockets; reintento autorizado exitoso. No se instaló PyInstaller ni se actualizó pip/global. Log de segunda instalación preservado bruto y comprimido.'})

now=dt.datetime.now().astimezone().isoformat()
checks={}
for v,before in versions.items():
    root=TF/f'ProteinFuncAI {v}'
    actual={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
    checks[v]={'files':len(before),'added':sorted(set(actual)-set(before)),
        'missing':sorted(set(before)-set(actual)),
        'modified':[n for n in before if n in actual and before[n]['sha256']!=actual[n]]}
previous=load('evidencias_previas_sha256.json')
checks['historical_evidence_modified']=[n for n,h in previous.items() if sha(QA/'EVIDENCIAS'/n)!=h]
checks['source_model_modified']=[n for n,v in models['fuente']['all_files'].items() if sha(ROOT/'model'/n)!=v['sha256']]
git=['git','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT)]
checks['commit']=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
checks['tracked_diff']=subprocess.check_output(git+['diff','--stat'],text=True)
checks['git_status']=subprocess.check_output(git+['status','--short'],text=True)
checks['date']=now
save('conservacion-y-cierre.json',checks)
assert not checks['historical_evidence_modified'] and not checks['source_model_modified'] and not checks['tracked_diff']
assert all(not checks[v][k] for v in versions for k in ('added','missing','modified'))

report=f'''# Ampliación QA: release final candidato 0.2.1

Fecha de cierre: {now}. La sección anterior se conserva como **auditoría histórica**, con fuente 0.2.1 y distribución 0.2.0. Este anexo incorpora el ejecutable 0.2.1; no atribuye al binario las pruebas ejecutadas sobre el código fuente. Copias exactas de los cuatro documentos anteriores: `{REL}HISTORICO/`.

## Resultado consolidado

| Ámbito | Auditoría previa | Evaluación actual 0.2.1 |
|---|---|---|
| Fuente / commit | 0.2.1 / c38323717be241cfa75d7684d0ff4ab7343270cd | Mismo commit, sin diferencias en archivos rastreados |
| Pytest | 22 aprobadas; 21 pendientes | **43 aprobadas, 0 fallidas, 0 errores, 0 skipped**; ninguna de las 21 sigue bloqueada |
| Qt automatizado | 13 pruebas pendientes | 13 aprobadas con Qt offscreen; no escritorio real |
| Binario local evaluado | 0.2.0 | **0.2.1**, confirmado por GUI --version y por el comprobador |
| CLI muestra / errores | Ambas aprobadas | Ambas repetidas y aprobadas; cuatro procesos CLI en total |
| Control adicional búsqueda/exportación | Sospecha estática | **FALLIDO**, reproducido en fuente 0.2.1 mediante Qt offscreen y fixture sintética |
| Interfaz del ejecutable | No ejecutada | Sigue pendiente validación visual/manual |
| Sin Internet físico | Pendiente | Sigue pendiente; solo configuración lógica offline |

La suite existente pasa, pero **no se declara aceptación completa del release**: existe un defecto funcional adicional en la exportación con búsqueda activa. No se corrigió código ni se alteraron pruebas para obtener estos resultados.

## Distribuciones y trazabilidad SHA-256

Se localizaron `TF/ProteinFuncAI 0.2.0/` y `TF/ProteinFuncAI 0.2.1/`. Ambas incluyen ProteinFuncAI.exe, proteinfunc-check.exe y _internal. La carpeta 0.2.1 también contiene archivos de desinstalador; no se dispone del ZIP original ni de un manifiesto firmado de publicación para acreditar su procedencia portable. Se verificó la distribución local ejecutable y autocontenida. No se instalaron/desinstalaron aplicaciones.

| Artefacto | SHA-256 0.2.0 | SHA-256 0.2.1 |
|---|---|---|
| ProteinFuncAI.exe | `{versions['0.2.0']['ProteinFuncAI.exe']['sha256']}` | `{versions['0.2.1']['ProteinFuncAI.exe']['sha256']}` |
| proteinfunc-check.exe | `{versions['0.2.0']['proteinfunc-check.exe']['sha256']}` | `{versions['0.2.1']['proteinfunc-check.exe']['sha256']}` |

Versiones observadas: {link('gui-version.stdout.log','GUI --version')} y {link('cli-muestra.stdout.log','CLI 0.2.1')}. `--version` termina antes de construir QApplication/History; no es una prueba de inicio visual ni de carga del modelo en la GUI. El binario se ejecutó con stdout/stderr capturados y rutas de datos temporales para esta consulta.

Se calculó SHA-256 de **todos los archivos** de las dos distribuciones: {link('distribucion-0.2.0-sha256.json')} y {link('distribucion-0.2.1-sha256.json')}. Estas huellas identifican los archivos locales y permiten detectar cambios; **no sustituyen una comparación con checksums oficiales del editor**, que no se suministraron.

Los siete archivos del modelo, incluido SHA256SUMS, coinciden entre fuente, 0.2.0 y 0.2.1. Huella estructurada del paquete: `{fingerprint}`. Los seis archivos listados en SHA256SUMS coinciden con los valores esperados, y el CLI 0.2.1 verificó 768 salidas/768 etiquetas al cargar pesos. {link('integridad-modelos.json','Evidencia de modelos')}. Los hashes de los dos ejecutables 0.2.0 también coinciden con los registrados en la auditoría previa, pese al cambio de nombre de su carpeta realizado antes de esta continuación.

La comprobación final no detectó archivos añadidos, eliminados o modificados en ninguna distribución, ni cambios en modelos o evidencias previas. No hubo commits ni pushes. {link('conservacion-y-cierre.json','Registro de conservación')}. El código empaquetado no contiene una atestación de commit comprobada: la versión declarada y la igualdad de modelos no prueban por sí solas identidad de todo el código con HEAD.

## Entorno autorizado y suite completa

El usuario autorizó crear `TF/.qa-venv-021`, con Python 3.12.10 e `include-system-site-packages=false`. Se instalaron los requisitos fijados sin actualizar el entorno global: numpy 2.1.3, torch 2.11.0+cpu, transformers 5.20.2, safetensors 0.8.0 y PySide6 6.12.0. Las herramientas de prueba resolvieron a pytest 9.2.0 y pytest-qt 4.5.0; Qt runtime/compilado 6.12.0 y pluggy 1.7.0. No se instaló PyInstaller, porque no se reconstruyeron binarios. `pip check` finalizó sin requisitos rotos. {link('pip-freeze.stdout.log','Versiones completas')}; {link('pip-check.stdout.log','Consistencia de dependencias')}; {link('registro-instalacion.json','Autorización y comandos de instalación')}. El log detallado se conserva comprimido y el bruto permanece en el venv, sin eliminarse.

El primer intento de descarga de torch falló por WinError 10013 del entorno aislado. Se autorizó el acceso de red adicional y la instalación concluyó correctamente. Esto es una incidencia de preparación del entorno, no un fallo de producto.

```powershell
.\\.qa-venv-021\\Scripts\\python.exe -m pytest tests -v -p no:cacheprovider --basetemp <temporal-nueva> --junitxml <salida-nueva.xml>
```

Se ejecutó desde la raíz del repositorio, con QT_QPA_PLATFORM=offscreen, variables HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE=1 y bytecode deshabilitado. El comando y las rutas reales están en {link('pytest-completo-021.json')}. Resultado: **43 passed in 28.36s**, proceso completo **30.6897 s**, código 0. {link('pytest-completo-021.stdout.log','Log completo')}; {link('pytest-completo-021.xml','JUnit')}. Una ejecución preliminar de cuatro pruebas de validación también aprobó (0.11 s; ocho deseleccionadas), pero esas cuatro están incluidas en las 43 y **no se suman como casos únicos adicionales**.

Las 21 pendientes eran: una prueba de acuerdo validador/parser, una de versiones de modelo mezcladas, cinco de inferencia, trece de Qt y una de CLI. Todas aprobaron. Esto incorpora la comparación con reference_prediction.json de Kaggle con tolerancia absoluta 1e-5, consistencia de propagación GO, equivalencia por bloques, truncamiento, cancelación sin parciales y reapertura del historial. Las bases SQLite, preferencias y copias de modelos utilizadas son temporales y nuevas; el historial del usuario no se abrió.

## Repetición del comprobador 0.2.1

| Entrada | Salida real | Duración total medida | Evidencia |
|---|---|---|---|
| examples/muestra.fasta | 3 proteínas: P01308=36, ubiquitina=13, ejemplo_kaggle=45 términos a 0.45; ok=true | {load('cli-muestra.json')['seconds']:.4f} s | {link('cli-muestra.stdout.log')} |
| examples/con_errores.fasta | 5 registros, 1 válido, 4 errores; solo valida_1 procesada; ok=true | {load('cli-errores.json')['seconds']:.4f} s | {link('cli-errores.stdout.log')} |
| examples/pruebas/07_adn_en_vez_de_proteina.fasta | 3 registros, 1 válido, 2 errores; solo proteina_valida procesada; ok=true | {load('cli-adn-arn.json')['seconds']:.4f} s | {link('cli-adn-arn.stdout.log')} |
| examples/pruebas/03_casos_limite.fasta | 6 válidos, 2 avisos; seis proteínas procesadas; ok=true | {load('cli-limites.json')['seconds']:.4f} s | {link('cli-limites.stdout.log')} |

Los cuatro procesos terminaron con código 0. Los conteos del par muestra/errores coinciden con los registrados para 0.2.0. El CLI muestra solo una síntesis y los primeros términos redondeados: no demuestra igualdad numérica de todas las predicciones entre binarios. Los tiempos incluyen arranque, integridad, carga, validación e inferencia; no son tiempos aislados de inferencia ni permiten comparar velocidad entre versiones con condiciones de caché diferentes. Las cargas impresas para muestra, errores, ADN/ARN y límites fueron respectivamente 5.5, 5.0, 4.9 y 5.0 s. No se midió memoria máxima ni proteínas/s en esta ampliación.

Los logs CLI contienen algunos caracteres sustituidos por la codificación de consola Windows del binario; los identificadores, cifras y códigos de salida son legibles. Los mensajes completos y con acentos se conservan desde el validador fuente en JSON. No se reemplazaron estos logs por resultados de nuevas ejecuciones. El aviso PyTorch sobre redirecciones no soportadas en Windows no impidió finalizar.

## ADN/ARN y baja complejidad

El validador fuente 0.2.1 rechaza `adn_codificante` y `arn_mensajero` con estado error y el mensaje que comienza: “Parece una secuencia de ADN/ARN ... no de proteína”. El binario 0.2.1 confirma dos rechazos y solo infiere la proteína válida; no muestra los mensajes detallados en su CLI. El criterio inspeccionado es heurístico: longitud mínima 20, al menos 90% de A/C/G/T/U/N y tres nucleótidos distintos. No constituye una identificación universal de ADN/ARN.

Se comprobaron mensajes de causa: poliglicina de 50 residuos → “G ocupa el 100%”; ACDE repetido → “4 aminoácidos distintos”, diversidad 2.0 bits; residuos ambiguos → porcentaje y advertencia de poca fiabilidad. La secuencia corta ACGTACGT se acepta como control del límite de la heurística. Los avisos no excluyen proteínas: el CLI también predice para secuencias sintéticas de baja complejidad, por lo que esos puntajes no deben interpretarse como evidencia biológica. Las pruebas de Qt verifican además el aviso de secuencia atípica y el panel de resumen. {link('mensajes-validacion-fuente-021.json','Mensajes y estados exactos')}; tests/test_validation.py y test_gui.py::test_summary_panel_and_atypical_warning en el JUnit.

## Defecto adicional QA-021-EXPORT-BUSQUEDA

**Estado: FALLIDO. Severidad propuesta: media**, por discrepancia entre resultados visibles y archivo exportado. Alcance reproducido: código fuente 0.2.1, Qt offscreen, fixture sintética existente; no se ha confirmado la manifestación en el ejecutable mediante interacción visual.

Pasos reproducidos: construir MainWindow con History y QSettings temporales; cargar make_result() de tests/test_results_history.py; desactivar “solo específicos”; buscar GO:1; obtener el filtro con current_view() y exportar por el mismo mecanismo que usa export_results(). Resultado visible: **1 fila**. Resultado JSON: predicciones **GO:1 y GO:2**. Esperado según “Guardar los resultados visibles”: solo GO:1. La búsqueda sí funciona; es su aplicación a la exportación la que falla.

Evidencia: {link('busqueda-exportacion-qt.json')}, {link('exportacion-con-busqueda.json')}; reproducción: [qa_funcional_021.py](qa_funcional_021.py). El script finaliza normalmente para conservar el diagnóstico; la conclusión funcional está en su campo status=FALLIDO. El código observado es main_window.py:600 (current_view), :656 (proxy de búsqueda), :781 (export_results), y core/results.py:43 (ViewFilter sin campo de búsqueda). La suite existente no cubre esta combinación; por ello el fallo adicional no se cuenta como un fallo de las 43 pruebas pytest. La comprobación adicional confirmó búsqueda y falló exportación; se informa como **un escenario adicional fallido**, no como dos casos independientes.

## Pendientes de aceptación del ejecutable

No quedan pruebas existentes bloqueadas por dependencias. Permanecen pendientes la interacción visual directa de PF-01 a PF-18 sobre el ejecutable 0.2.1, el contraste de exportación con búsqueda activa en ese binario y la desconexión física de Internet. Se conservan las 18 filas GUI como NO EJECUTADO; el éxito de Qt offscreen no las reemplaza. Los 18 escenarios funcionales por código/CLI tienen ahora 17 aprobados y PF-16 bloqueado; el defecto adicional se registra fuera de ese conteo base.

Aplicar [MANUAL_GUI.md](MANUAL_GUI.md) seleccionando `TF/ProteinFuncAI 0.2.1/ProteinFuncAI.exe`, con perfil Windows de prueba o VM aislada. QSettings en Windows puede usar el Registro: cambiar solo APPDATA no garantiza aislar preferencias. No abrir una segunda instancia contra el historial del usuario. Añadir revisión de mensajes completos de ADN/ARN y baja complejidad, y exportación con búsqueda activa. No eliminar historial, cambiar conectividad del equipo ni manipular modelos originales durante esa validación. Los casos pendientes deben aportar capturas, versión, entrada, fecha y resultado para considerarse ejecutados.

Se recomienda que el equipo de desarrollo revise el defecto antes de aceptar el release; esta auditoría no autoriza ni realiza su corrección. No se reevaluó calidad biológica ni métrica oficial CAFA, y no se presentan estimaciones como mediciones.
'''
append('INFORME_QA.md',report)

base=[('PF-01','RF-01','FASTA válido','APROBADO','Fuente y CLI 0.2.1: carga y validación','cli-muestra.stdout.log'),
('PF-02','RF-01','Múltiples proteínas','APROBADO','Fuente Qt y CLI: tres proteínas','pytest-completo-021.xml'),
('PF-03','RF-02','Entrada vacía','APROBADO','test_empty_input_is_global_error','pytest-completo-021.xml'),
('PF-04','RF-02','IDs duplicados','APROBADO','test_reports_every_problem_not_only_the_first','pytest-completo-021.xml'),
('PF-05','RF-02','Caracteres inválidos','APROBADO','Errores y exclusión en fuente/CLI','cli-errores.stdout.log'),
('PF-06','RF-02','Aviso/truncamiento','APROBADO','Avisos y residues_used=512 en inferencia fuente','pytest-completo-021.xml'),
('PF-07','RF-07','Inferencia','APROBADO','Fuente frente a Kaggle; CLI real 0.2.1','pytest-completo-021.xml'),
('PF-08','RF-08','MF/BP/CC','APROBADO','Motor de filtros y Qt fuente; no GUI del binario','pytest-completo-021.xml'),
('PF-09','RF-08','Umbral','APROBADO','Motor y deslizador Qt fuente','pytest-completo-021.xml'),
('PF-10','RF-08','Buscar GO','APROBADO','Búsqueda GO:1 produce una fila en Qt offscreen','busqueda-exportacion-qt.json'),
('PF-11','RF-09','CSV sin búsqueda activa','APROBADO','Exportación por código con fixture; búsqueda activa falla aparte','pytest-completo-021.xml'),
('PF-12','RF-09','TSV sin búsqueda activa','APROBADO','Exportación por código, no diálogo del binario','pytest-completo-021.xml'),
('PF-13','RF-09','JSON sin búsqueda activa','APROBADO','Contrato y flujo de resultados Qt por código','pytest-completo-021.xml'),
('PF-14','RF-11','Historial','APROBADO','Base temporal; fuente y Qt','pytest-completo-021.xml'),
('PF-15','RF-10','Cancelar','APROBADO','Fuente y Qt cancelan sin parciales','pytest-completo-021.xml'),
('PF-16','RNF-02','Sin Internet físico','BLOQUEADO','Solo variables offline; red del sistema sin desconectar','cli-muestra.json'),
('PF-17','RF-06/RNF-06','Integridad','APROBADO','SHA, coherencia, carga 768/768 y rechazo de copias alteradas','integridad-modelos.json'),
('PF-18','RF-11','Reabrir resultados','APROBADO','SQLite temporal y Qt fuente','pytest-completo-021.xml')]
matrix='''# Ampliación de matriz: 0.2.1

Las tablas anteriores son históricas. Estado actual: suite fuente 43/43 aprobadas; 21 pendientes previas resueltas. No sumar ejecuciones repetidas como pruebas únicas. Base PF: 17 APROBADO, 0 FALLIDO, 1 BLOQUEADO en alcance código/CLI. Un escenario adicional de exportación con búsqueda activa está FALLIDO. Las 18 validaciones GUI del ejecutable permanecen NO EJECUTADO.

| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
'''
for cid,req,scenario,status,got,evidence in base:
    matrix+=f'| {cid}-021 | {req} | {scenario} | Comportamiento del requisito en el alcance evaluado | {got} | {status} | {link(evidence)} |\n'
matrix+=f'''| QA-021-ADN | RF-02 | ADN/ARN frente a proteína | Rechazar ambos nucleótidos y aceptar proteína | Fuente: mensajes de error; CLI 0.2.1 solo procesa proteina_valida | APROBADO | {link('mensajes-validacion-fuente-021.json')} / {link('cli-adn-arn.stdout.log')} |
| QA-021-COMPLEJIDAD | RF-02/UX | Causas de baja complejidad | Advertir causa y poca fiabilidad sin rechazar | Mensajes de predominio, diversidad y ambigüedad; Qt verifica banner | APROBADO | {link('mensajes-validacion-fuente-021.json')} / {link('pytest-completo-021.xml')} |
| QA-021-EXPORT-BUSQUEDA | RF-08/RF-09 | Exportar con búsqueda GO:1 | Exportar únicamente GO:1 visible | Una fila visible; JSON exporta GO:1 y GO:2 en fuente Qt offscreen | FALLIDO | {link('busqueda-exportacion-qt.json')} / {link('exportacion-con-busqueda.json')} |

## Resolución individual de las 21 pendientes

| Prueba | Modalidad | Estado 0.2.1 | Evidencia |
|---|---|---|---|
'''
for f,t in pending:
    mode='Qt offscreen fuente' if f=='test_gui.py' else 'Código/CLI fuente en venv'
    matrix+=f"| `{f}::{t['name']}` | {mode} | APROBADO | {link('pytest-completo-021.xml')} |\n"
matrix+='\n## Interfaz directa del ejecutable 0.2.1\n\n| ID | Estado | Próxima validación |\n|---|---|---|\n'
for cid,req,scenario,*_ in base: matrix+=f'| {cid}-GUI-021 | NO EJECUTADO | {scenario}, en perfil aislado según MANUAL_GUI.md |\n'
append('MATRIZ_PRUEBAS.md',matrix)

trace='''# Trazabilidad añadida para 0.2.1

La trazabilidad histórica anterior permanece válida para su fecha y alcance. Commit fuente sin cambios: c38323717be241cfa75d7684d0ff4ab7343270cd. Los resultados de tests/ son de la fuente, mientras los cuatro cli-*.stdout.log proceden del ejecutable 0.2.1. No se intercambian ambas atribuciones.

| Requerimiento | Código / prueba | Resultado actual | Evidencia 0.2.1 |
|---|---|---|---|
'''
rows=[('RF-01/RF-02','core/validation.py; tests/test_validation.py','Validación, rechazo ADN/ARN y mensajes de complejidad aprobados','mensajes-validacion-fuente-021.json'),
('RF-06/RNF-06','core/integrity.py; services.py; tests/test_integrity.py','Integridad, dimensiones y copias alteradas aprobadas','integridad-modelos.json'),
('RF-07/RNF-04','inference/protein_go.py; tests/test_inference.py','Referencia Kaggle y propagación aprobadas en fuente','pytest-completo-021.xml'),
('RF-07','proteinfunc-check.exe de 0.2.1','Inferencia real de tres proteínas y dos controles adicionales','cli-muestra.stdout.log'),
('RF-08','core/results.py; ui/main_window.py; tests/test_gui.py','Filtros, umbral y búsqueda aprobados en fuente Qt','pytest-completo-021.xml'),
('RF-09','core/results.py; tests/test_results_history.py; test_export_from_gui','Formatos aprobados sin búsqueda activa','pytest-completo-021.xml'),
('RF-08/RF-09','ui/main_window.py:600,656,781; core/results.py:43; qa_funcional_021.py','FALLIDO: exportación ignora búsqueda del proxy','busqueda-exportacion-qt.json'),
('RF-10','services.py; test_cancel_returns_none_not_partial; test_cancel_discards_partial_results','Cancelación sin resultados parciales aprobada en fuente','pytest-completo-021.xml'),
('RF-11','core/history.py; tests/test_results_history.py; test_history_reopen','Historial y reapertura aprobados con SQLite temporales','pytest-completo-021.xml'),
('RNF-02','services.py; test_cli.py','Offline lógico aprobado; desconexión física pendiente','cli-adn-arn.json'),
('RNF-05','core/perf.py; test_performance_is_recorded; test_preferences_apply_batch_and_threads','Registro de telemetría y preferencias aprobados en fuente','pytest-completo-021.xml'),
('Versionado de binario','ProteinFuncAI.exe --version; proteinfunc-check.exe','Ambos declaran 0.2.1; SHA de todos los archivos calculado','gui-version.stdout.log'),
('Conservación','Huellas antes/después, historial de documentos','Distribuciones y evidencias previas intactas','conservacion-y-cierre.json')]
for req,source,result,evidence in rows: trace+=f'| {req} | {source} | {result} | {link(evidence)} |\n'
trace+='\nLas 13 pruebas Qt no equivalen a las 18 comprobaciones manuales del ejecutable. El defecto adicional se confirmó en fuente; queda por contrastar su manifestación en el binario. No se probó procedencia criptográfica oficial del release ni exactitud biológica de las funciones predichas.\n'
append('TRAZABILIDAD.md',trace)

academic=f'''# Actualización académica: versión 0.2.1

El texto anterior describe la auditoría inicial y se conserva como antecedente. En la continuación del 22 de noviembre de 2026 se verificó una distribución local cuyos dos ejecutables declararon versión 0.2.1. Los siete archivos de su modelo coincidieron por SHA-256 con el repositorio y la distribución 0.2.0. Se registraron las huellas de todos los archivos de ambas distribuciones y se comprobó que permanecieran intactas durante la evaluación.

Con autorización del usuario se preparó un entorno virtual aislado de Python 3.12.10 con las versiones fijadas de las dependencias de producción, PyTorch CPU, pytest 9.2.0 y pytest-qt 4.5.0. La suite completa del código fuente 0.2.1, commit c38323717be241cfa75d7684d0ff4ab7343270cd, obtuvo 43 pruebas aprobadas, cero fallidas y cero omitidas, en 28.36 segundos según pytest. Esto resolvió las 21 pruebas previamente pendientes, incluidas trece pruebas Qt sin pantalla, la comparación numérica con la referencia exportada de Kaggle y la cancelación sin resultados parciales.

Cuatro comprobaciones del ejecutable 0.2.1 finalizaron correctamente: FASTA de tres proteínas, archivo con cuatro registros inválidos y uno válido, archivo con ADN/ARN y una proteína, y seis casos límite. En el control de nucleótidos se rechazaron ambos registros ADN/ARN y se procesó únicamente la proteína válida. Las verificaciones del validador fuente confirmaron mensajes que explican predominio de residuos, diversidad reducida y proporción de residuos ambiguos. Estas advertencias no impiden la inferencia y no acreditan fiabilidad biológica de los puntajes.

Una comprobación funcional adicional, independiente de la suite existente, reprodujo un defecto en fuente 0.2.1 con Qt sin pantalla: con búsqueda GO:1 activa se mostró una fila, mientras el JSON exportado incluyó GO:1 y GO:2. Por tanto, las 43 pruebas aprobadas no implican aceptación completa del producto. Quedan pendientes el contraste de este defecto en el ejecutable mediante interacción visual, las comprobaciones manuales de escritorio y la operación con conectividad física desactivada. No se modificaron producción, modelos, ejecutables, pruebas existentes ni el historial del usuario; tampoco se recalculó la calidad predictiva biológica o la métrica oficial CAFA.
'''
append('RESUMEN_ACADEMICO.md',academic)

# Verifica conservación de cada documento original como prefijo exacto.
for name in ['INFORME_QA.md','MATRIZ_PRUEBAS.md','TRAZABILIDAD.md','RESUMEN_ACADEMICO.md']:
    assert (QA/name).read_bytes().startswith((OUT/'HISTORICO'/name).read_bytes())
broken=[]
for p in QA.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if not target.startswith(('http:','https:','#')) and not (p.parent/target).exists(): broken.append((p.name,target))
save('validacion-documentos.json',{'historical_documents_preserved_as_prefix':True,'broken_relative_links':broken})
assert not broken
save('INDICE_SHA256_021.json',{p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='INDICE_SHA256_021.json'})
print(json.dumps({'pytest':stats,'additional_functional_status':bug['status'],'pending_resolved':len(pending),
    'historical_evidence_unchanged':not checks['historical_evidence_modified'],'new_evidence':str(OUT)},ensure_ascii=False))
