"""Genera los documentos de esta auditoría a partir de sus evidencias reales."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

E=Path(__file__).resolve().parent
D=E.parent
R=D.parents[1]
def load(name): return json.loads((E/name).read_text(encoding='utf-8'))
def write(name,text): (D/name).write_text(text.strip()+'\n',encoding='utf-8')
env=load('entorno.json'); integrity=load('integridad_modelos.json'); perf=load('rendimiento-cli.json')
passed={x.attrib['name'] for x in ET.parse(E/'pytest-subconjunto.xml').iter('testcase') if x.find('failure') is None and x.find('error') is None}
fingerprint=integrity['repositorio']['fingerprint']
cases=[
('PF-01','RF-01','Cargar FASTA válido','Leer secuencias e identificadores','muestra.fasta: 3 registros válidos; lectura por código y CLI','APROBADO','validacion_ejemplos.json','core/validation.py','test_validation.py'),
('PF-02','RF-01','Cargar múltiples proteínas','Conservar registros del lote','8 proteínas conocidas y 300 sintéticas validadas; CLI predijo 3 proteínas','APROBADO','validacion_ejemplos.json','core/validation.py','test_validation.py'),
('PF-03','RF-02','Validar FASTA vacío','Rechazar entrada vacía','Error global y cero aceptadas en cadena vacía; prueba pytest aprobada','APROBADO','pytest-subconjunto.log','core/validation.py','test_validation.py'),
('PF-04','RF-02','Detectar identificadores duplicados','Informar duplicado y excluirlo','con_errores.fasta: segunda valida_1 rechazada','APROBADO','validacion_ejemplos.json','core/validation.py','test_validation.py'),
('PF-05','RF-02','Detectar caracteres inválidos','Informar símbolo y posición','Prueba verifica # en posición 11; CLI excluye entradas erróneas','APROBADO','pytest-subconjunto.log','core/validation.py','test_validation.py'),
('PF-06','RF-02','Advertir truncamiento','Avisar al exceder 512 residuos','muestra.fasta: un aviso; se conserva la secuencia completa en validación. Truncamiento tensorial pendiente','APROBADO','validacion_ejemplos.json','core/validation.py','test_validation.py'),
('PF-07','RF-07','Ejecutar inferencia','Obtener predicciones del modelo real','CLI: 3 proteínas; 36, 13 y 45 términos a umbral 0.45; salida ok=true','APROBADO','ejecutable-check.log','inference/protein_go.py','test_inference.py (bloqueada; ejecución CLI alternativa)'),
('PF-08','RF-08','Filtrar MF/BP/CC','Retener solo aspecto seleccionado','4 verificaciones adicionales: tres aspectos y umbrales; datos sintéticos','APROBADO','filtros_adicionales.json','core/results.py','test_results_history.py'),
('PF-09','RF-08','Modificar umbral','Cambiar filas según umbral','Fixture sintética: 4, 2 y 0 filas para 0.10, 0.45 y 0.95','APROBADO','filtros_adicionales.json','core/results.py','test_results_history.py'),
('PF-10','RF-08','Buscar términos GO','Filtrar por identificador o nombre','Depende del proxy Qt; PySide6 ausente y captura GUI fallida','BLOQUEADO','incidencias_gui.json','ui/main_window.py','test_gui.py::test_analyze_fasta_and_filter'),
('PF-11','RF-09','Exportar CSV','Columnas, metadatos y acentos correctos','pytest aprobado; archivo sintético conservado, incluye proteína sin términos','APROBADO','exportacion_sintetica.csv','core/results.py','test_results_history.py'),
('PF-12','RF-09','Exportar TSV','Separación por tabuladores y metadatos','pytest aprobado; archivo sintético conservado','APROBADO','exportacion_sintetica.tsv','core/results.py','test_results_history.py'),
('PF-13','RF-09','Exportar JSON','Contrato y metadatos recuperables','Roundtrip con acentos, estado y huella aprobado; salida sintética conservada','APROBADO','exportacion_sintetica.json','core/results.py','test_results_history.py'),
('PF-14','RF-11','Consultar historial','Listar y filtrar ejecuciones','SQLite nueva de prueba: estados, fecha y huella comprobados; no historial real','APROBADO','pytest-subconjunto.log','core/history.py','test_results_history.py::test_history_lifecycle'),
('PF-15','RF-10','Cancelar procesamiento','Descartar resultados parciales','Requiere runtime no instalado; GUI no disponible','BLOQUEADO','entorno.json','services.py','test_inference.py::test_cancel_returns_none_not_partial; test_gui.py'),
('PF-16','RNF-02','Ejecutar sin Internet','Inferir con conectividad del equipo desactivada','CLI aprobó con HF_HUB_OFFLINE y TRANSFORMERS_OFFLINE; no se desconectó la red física','BLOQUEADO','ejecutable-check.json','services.py; inference/protein_go.py','test_cli.py (bloqueada)'),
('PF-17','RF-06 / RNF-06','Verificar integridad del modelo','Hashes y coherencia correctos; rechazar daños','Ambos paquetes íntegros e idénticos; daños simulados en copias detectados; dimensiones 768 verificadas en CLI','APROBADO','integridad_modelos.json','core/integrity.py; services.py','test_integrity.py'),
('PF-18','RF-11','Reabrir resultados anteriores','Recuperar resultados persistidos','SQLite temporal reabierta conserva proteínas y huella; compatibilidad de esquema antiguo aprobada','APROBADO','pytest-subconjunto.log','core/history.py; core/results.py','test_results_history.py::test_history_lifecycle; test_history_migrates_v01_database'),
]

matrix='# Matriz de pruebas\n\nFecha: 22 de noviembre de 2026, America/Lima. Commit: `'+env['commit']+'`.\n\nLos estados de la primera tabla corresponden exclusivamente al alcance indicado (código, fixture o CLI). No acreditan interacción gráfica. 15 APROBADO, 0 FALLIDO y 3 BLOQUEADO; este conteo de escenarios no se suma al de pytest.\n\n| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |\n|---|---|---|---|---|---|---|\n'
for cid,req,scenario,expected,got,status,evidence,source,test in cases:
    matrix+=f'| {cid} | {req} | {scenario} | {expected} | {got} | {status} | [Registro](EVIDENCIAS/{evidence}) |\n'
matrix+='\n## Validación directa de la GUI\n\nNo hubo captura utilizable ni interacción funcional confirmada. Las 18 comprobaciones siguientes están NO EJECUTADO. La detección de una ventana existente no prueba el inicio correcto.\n\n| ID | Escenario | Estado | Evidencia |\n|---|---|---|---|\n'
for c in cases: matrix+=f'| {c[0]}-GUI | {c[2]} | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |\n'
matrix+='\n## Inventario de pruebas automatizadas\n\n43 funciones encontradas por AST. 22 ejecutadas y aprobadas; 21 bloqueadas por el entorno. Pytest: 0 fallidas, 0 omitidas mediante skip y 2 deseleccionadas en el subconjunto; los otros 19 casos no se recolectaron.\n\n| Prueba existente | Estado | Evidencia / motivo |\n|---|---|---|\n'
for file,tests in env['test_inventory'].items():
    for t in tests:
        ok=t['name'] in passed
        matrix+=f"| `{file}::{t['name']}` | {'APROBADO' if ok else 'BLOQUEADO'} | {'pytest-subconjunto.log y XML' if ok else 'Dependencias del runtime / pytest-qt ausentes; no ejecutada'} |\n"
write('MATRIZ_PRUEBAS.md',matrix)

trace='# Trazabilidad\n\nLos identificadores RF/RNF proceden del README del repositorio; no se dispone de una especificación externa de aceptación. Rutas relativas a la raíz del repositorio.\n\n| Escenario / requisito | Código fuente | Pruebas existentes | Resultado observado | Evidencia |\n|---|---|---|---|---|\n'
for cid,req,scenario,expected,got,status,evidence,source,test in cases:
    links='; '.join(f'[{s}](../../proteinfunc_app/{s})' for s in source.split('; '))
    trace+=f'| {cid} / {req} | {links} | {test} | {status}: {got} | [{evidence}](EVIDENCIAS/{evidence}) |\n'
trace+='\nLa inferencia empaquetada pertenece a la versión 0.2.0; sus resultados no demuestran equivalencia numérica con el código 0.2.1. La identidad del modelo se demuestra por los hashes. El archivo tests/data/reference_prediction.json existe, pero la comparación numérica con Kaggle no se ejecutó. Las métricas de entrenamiento del manifiesto no se recalcularon.\n'
write('TRAZABILIDAD.md',trace)

report=f'''# Informe técnico QA — ProteinFunc AI Desktop

Fecha de auditoría: 2026-11-22, zona America/Lima (UTC−05:00). Evidencias generadas hasta {dt.datetime.now().astimezone().isoformat()}.

## Resultado y alcance

Se clonó el repositorio solicitado en `TF/ProteinFunc-AI`, rama `main`, HEAD `{env['commit']}`. El árbol estaba limpio inmediatamente después de clonar. Se ejecutaron **22 pruebas pytest: 22 aprobadas, 0 fallidas y 0 skipped**, con **2 deseleccionadas** dentro del subconjunto elegido. El inventario completo contiene 43 funciones: **21 quedaron bloqueadas** por dependencias ausentes (incluye las dos deseleccionadas). No se ejecutó la orden completa `python -m pytest tests -v`, pues el entorno no estaba preparado. No se equiparan casos no ejecutados con pruebas aprobadas.

Dos ejecuciones reales de `proteinfunc-check.exe` finalizaron con código 0 y `ok=true`: una con tres proteínas válidas y otra con un archivo de cinco registros, de los cuales solo uno era válido. Además, cuatro verificaciones de filtros sobre datos sintéticos aprobaron. Esos controles adicionales y los dos procesos CLI se contabilizan por separado de pytest. La matriz de 18 escenarios registra 15 aprobados en el alcance de código/CLI y 3 bloqueados. Las 18 validaciones directas de GUI quedaron NO EJECUTADO.

No se modificaron producción, pruebas existentes, modelos, ejecutables ni historial del usuario; no se instalaron dependencias, no se entrenó y no se hicieron commits o pushes. Solo se añadieron documentos y scripts de evidencia. Las pruebas de integridad alteran exclusivamente copias temporales; las pruebas de historial crean SQLite nuevas. Esas copias temporales se trasladaron a la carpeta temporal del sistema para conservar evidencias pequeñas, sin eliminar archivos existentes. Véase `EVIDENCIAS/temporales.json`.

## Adquisición y entorno

Git disponible: 2.51.0.windows.1 (versión del archivo 2.51.0.1). La carpeta destino no existía. La primera clonación falló por conectividad a github.com:443 en el entorno aislado; se repitió con permiso adicional y concluyó correctamente. Git bloqueó después la consulta por propiedad distinta entre usuario aislado y propietario; se autorizó la consulta con el propietario. No se cambió la configuración global de Git.

Sistema observado: `{env['os']}`, AMD64. Python 3.12.10 de 64 bits, pytest 9.1.1, pluggy 1.6.0 y psutil 7.2.2. En este intérprete faltan numpy, torch, transformers, safetensors, PySide6 y pytest-qt. La consulta `py -0p` no enumeró otros intérpretes, aunque `python` sí funciona. No se identificó un entorno virtual del proyecto en las carpetas inspeccionadas. Se solicitó autorización para crear un entorno aislado e instalar dependencias; no se realizó instalación en esta auditoría.

Requisitos fijados: numpy 2.1.3, torch 2.11.0, transformers 5.20.2, safetensors 0.8.0 y PySide6 6.12.0. Desarrollo añade pytest, pytest-qt y pyinstaller sin fijar versión. El manifiesto registra torch 2.11.0+cu130 del entrenamiento; la distribución incluye metadatos torch 2.11.0+cpu, numpy 2.1.3 y safetensors 0.8.0. El archivo distribuido transformers/__init__.py declara 5.20.2. No se importaron sus bibliotecas dentro del Python externo ni se trató el paquete PyInstaller como entorno de desarrollo. La versión PySide6 incluida no se confirmó de manera independiente.

## Arquitectura y empaquetado

| Componente | Ubicación | Responsabilidad inspeccionada |
|---|---|---|
| Entrada | proteinfunc_app/app.py, __main__.py, run_app.py | GUI, argumentos --check y --model; rutas de historial |
| Recursos | proteinfunc_app/paths.py | Desarrollo, sys._MEIPASS y PROTEINFUNC_MODEL_DIR |
| Validación | core/validation.py | FASTA, IDs, caracteres, vacíos, complejidad y avisos de longitud |
| Integridad | core/integrity.py | Archivos, manifiesto, SHA-256 y ancestros |
| Inferencia | inference/protein_go.py | Tokenización, ESM-2 congelado, cabeza lineal, sigmoid y propagación GO |
| Servicio | services.py | QThread, carga única, CPU/GPU, lotes, progreso y cancelación |
| Resultados | core/results.py | Filtros y CSV/TSV/JSON; SCORE_FLOOR=0.05 |
| Persistencia | core/history.py | SQLite y resultados comprimidos; migración de esquema |
| Interfaz | ui/main_window.py, dialogs.py, widgets.py, theme.py | Tabla, búsqueda Qt, controles y diálogos |
| Pruebas | tests/test_*.py | Validación, inferencia real, integridad, resultados/historial, CLI y Qt offscreen |
| Distribución | proteinfunc.spec | PyInstaller onedir; GUI sin consola y comprobador con consola; librerías compartidas en _internal |
| Instalación/CI | installer/windows/ProteinFuncAI.iss; installer/linux/install.sh; .github/workflows | Inno Setup, instalación Linux y compilación/pruebas Windows/Linux |

El paquete contiene manifest.json, weights.pt y backbone/config.json, model.safetensors, tokenizer_config.json, vocab.txt, más SHA256SUMS. El manifiesto declara facebook/esm2_t6_8M_UR50D, 768 etiquetas (256 MF, 256 BP, 256 CC), umbral 0.45 y truncamiento de prefijo a 512 residuos. La configuración del backbone declara 320 dimensiones. Estos son datos inspeccionados del artefacto; no son resultados de reentrenamiento o evaluación biológica independiente.

La especificación incluye el modelo, muestra.fasta e icono. Los FASTA adicionales de examples/pruebas no se empaquetan. La CI declara pruebas offscreen y verificación de consola, pero no se consultó ni se asume aprobado ningún run remoto.

## Comparación repositorio–distribución

| Propiedad | Repositorio | Distribución local |
|---|---|---|
| Versión de aplicación | 0.2.1 en __init__.py | 0.2.0 informada por CLI |
| Modelo | 7 archivos, incluidos checksums | Los mismos 7 archivos, idénticos byte a byte por SHA-256 |
| Huella del paquete | `{fingerprint}` | Idéntica |
| Integridad estructural | APROBADO por verify_bundle | APROBADO por verify_bundle y CLI |
| Dimensiones de pesos cargados | No se cargaron en Python externo | CLI verificó 768 salidas / 768 etiquetas |
| Ejecución | Subconjunto sin dependencias ML/Qt | Inferencia real en CPU con librerías empaquetadas |

Ejecutable principal: `TF/ProteinFuncAI/ProteinFuncAI.exe`; comprobador: `TF/ProteinFuncAI/proteinfunc-check.exe`. Ambos existen y sus tamaños y hashes están en `hashes_distribucion.json`. No se ejecutó el desinstalador. La identidad del modelo no demuestra identidad del código empaquetado: no hay evidencia que vincule el binario con el HEAD evaluado. No se descompiló ni se recompiló.

## Ejecución automatizada y evidencias

Comando exacto, inicio y fin: [pytest-ejecucion.json](EVIDENCIAS/pytest-ejecucion.json). Salida íntegra: [pytest-subconjunto.log](EVIDENCIAS/pytest-subconjunto.log); formato JUnit: [pytest-subconjunto.xml](EVIDENCIAS/pytest-subconjunto.xml).

```powershell
python -m pytest tests/test_validation.py tests/test_results_history.py tests/test_integrity.py -v -k "not validation_agrees_with_runtime_parser and not mixed_versions_are_rejected_when_loading" -p no:cacheprovider --basetemp <carpeta-temporal-nueva> --junitxml <ruta-nueva.xml>
```

Pytest informó **0.53 s**; el proceso completo medido con perf_counter duró **1.7243 s**. Se ejecutaron 11 pruebas de validación, 7 de resultados/historial y 4 de integridad. Quedaron bloqueadas 1 de validación, 1 de integridad, 5 de inferencia, 13 de GUI y 1 de CLI. Detalle por función en la matriz. Las pruebas Qt existentes usan offscreen y sustituyen diálogos modales: aunque pudieran ejecutarse, deben distinguirse de un ensayo visual del ejecutable.

Los FASTA originales se leyeron sin cambiarlos. Los resultados por registro están en [validacion_ejemplos.json](EVIDENCIAS/validacion_ejemplos.json): muestra (3 válidos, 1 aviso), proteínas conocidas (8 válidos), casos límite (6 válidos, 2 avisos), errores ampliados (7 registros, 2 válidos, 5 errores), lote sintético (300 válidos, 94 avisos), texto antes de cabecera y ADN/ARN. Los rechazos y avisos esperados son comportamiento aprobado, no fallos del producto.

Las exportaciones conservadas `exportacion_sintetica.csv`, `.tsv` y `.json` proceden de la fixture de tests/test_results_history.py (GO:1, GO:2, GO:3 son identificadores sintéticos). No son predicciones reales de proteínas ni se presentan como tales. El historial probado es desechable y no corresponde al del usuario.

## Validación del ejecutable

| Comprobación | Estado | Alcance observado |
|---|---|---|
| Inicio correcto de GUI | NO EJECUTADO | Había una ventana existente; dos capturas fallaron |
| Carga del modelo | APROBADO | CLI: integridad y dimensiones; CPU |
| Validación de entradas | APROBADO | CLI con muestra.fasta y con_errores.fasta; no cubre todos los diálogos |
| Inferencia local | APROBADO | Tres proteínas y una válida de archivo mixto; offline lógico activado |
| Visualización de predicciones | NO EJECUTADO | Solo salida por consola, sin observación de tabla |
| Filtros gráficos | NO EJECUTADO | Solo motor de filtros del repositorio probado |
| Exportaciones gráficas | NO EJECUTADO | Solo exportación por código sobre fixture probada |
| Historial gráfico | NO EJECUTADO | Historial real no abierto ni alterado |
| Manejo de errores | APROBADO | Alcance limitado: archivo mixto excluye cuatro entradas erróneas |

Salida de muestra: P01308, 36 términos; ubiquitina, 13; ejemplo_kaggle, 45, todos al umbral 0.45. No se verificó que sean funciones biológicas verdaderas. El archivo erróneo produjo cinco registros, un válido y cuatro errores, e infirió únicamente valida_1. Ambos procesos terminaron con código 0.

## Rendimiento real

| Métrica | Resultado | Límite de interpretación |
|---|---|---|
| Inicio de GUI | No medido | No se lanzó una sesión gráfica nueva |
| Primera carga CLI, muestra.fasta | 27.5 s | Valor impreso por la app; incluye integridad/carga, precisión 0.1 s |
| Primera ejecución CLI completa | 29.0400 s | Inicio de proceso hasta salida; 3 proteínas |
| Segunda carga CLI, con_errores.fasta | 4.6 s | Segunda ejecución; condiciones de caché no controladas |
| Segunda ejecución CLI completa | {perf['seconds']:.4f} s | Un registro aceptado; incluye arranque/carga/validación/inferencia |
| Memoria máxima segunda ejecución | {perf['peak_working_set_bytes']} bytes ({perf['peak_working_set_bytes']/1024**2:.2f} MiB) | Peak working set del proceso CLI; psutil, {perf['samples']} muestras a intervalos nominales de 50 ms |
| Dispositivo | cpu | Declarado por ambas ejecuciones del comprobador |
| Tiempo de inferencia aislado | No medido | CLI no lo informa |
| Proteínas por segundo de inferencia | No medido | No se divide tiempo total que incluye carga para atribuirlo al motor |

No se presentan estimaciones ni promedios representativos. Dos ejecuciones con entradas distintas no constituyen benchmark estadístico. El máximo de memoria de la GUI existente no se utilizó como medición de esta prueba. Una consulta opcional de procesos mediante CIM fue denegada; se obtuvo la medición necesaria del proceso hijo propio con psutil sin cambiar permisos.

## Hallazgos y limitaciones

1. **Versiones distintas (confirmado):** fuente 0.2.1 y comprobador 0.2.0. El modelo sí coincide. No certificar equivalencia completa del ejecutable con HEAD.
2. **Entorno incompleto (bloqueo):** 21 pruebas existentes no ejecutadas; no se comprobó la referencia numérica Kaggle, propagación real, cancelación ni comportamiento Qt.
3. **Captura de escritorio no disponible (bloqueo):** primer intento `FrameArrived timed out: timed out waiting on channel`; tras recuperar y activar la ventana, segundo intento `window capture timed out: timed out waiting on channel`. Se detuvo la automatización y no se obtuvieron capturas. No se atribuye este fallo de herramienta a la aplicación.
4. **Offline físico pendiente:** las variables offline y rutas locales se verificaron, pero no se desactivó Internet ni se auditó tráfico. PF-16 no queda aprobado de extremo a extremo.
5. **Posible discrepancia búsqueda–exportación (inspección estática, sin reproducción):** main_window.py:656 filtra el proxy mediante setFilterFixedString; current_view():600 no contiene el texto buscado y export_results():781 entrega ese ViewFilter al exportador. La búsqueda podría no limitar el archivo exportado según las filas visibles. Validar manualmente antes de declarar defecto confirmado. Las pruebas actuales de exportación no cubren búsqueda activa.
6. **Registro con caracteres sustituidos:** el primer log CLI se decodificó como UTF-8 aunque el proceso usó consola Windows; contiene símbolos sustituidos. El segundo se lanzó con PYTHONIOENCODING=utf-8 y conserva acentos. Valores ASCII, conteos y códigos de salida del primero son legibles. Existe también un aviso de PyTorch sobre redirecciones no soportadas en Windows; ambos procesos concluyeron correctamente.

No se observaron fallos en las 22 pruebas ejecutadas. Esto no demuestra ausencia de defectos en funciones pendientes ni calidad predictiva de GO. Las métricas del manifiesto y su alcance CAFA no se revalidaron; los puntajes no se consideran probabilidades calibradas.

## Reproducción y pendientes

Los scripts [ejecutar_qa.py](EVIDENCIAS/ejecutar_qa.py) y [verificaciones_adicionales.py](EVIDENCIAS/verificaciones_adicionales.py) documentan comandos y fixtures. Para nuevas auditorías utilizar una copia nueva del directorio de evidencias: los nombres de salida son fijos y no deben sobrescribir la evidencia de esta ejecución. Ejecutarlos con `python -B` y el mismo commit. El primero usa una carpeta temporal nueva para pytest; los logs de esta auditoría conservan la ruta original utilizada antes de trasladar las copias.

Para completar la suite, obtener autorización de instalación en un venv; instalar requirements-dev.txt sin actualizar las versiones fijadas de producción y ejecutar `python -m pytest tests -v`, preferentemente con `PYTHONDONTWRITEBYTECODE=1`, `QT_QPA_PLATFORM=offscreen`, variables offline, basetemp nueva y JUnit/log nuevos. Registrar versiones resueltas de las dependencias de desarrollo no fijadas. La autorización de instalación no estaba concedida al preparar este informe.

Validar después los 18 escenarios gráficos siguiendo [MANUAL_GUI.md](MANUAL_GUI.md), con perfil temporal aislado o copia autorizada del historial. El constructor History actualiza registros en_curso a fallido al abrirse: no iniciar una segunda sesión sobre el historial existente. No desactivar la red del equipo ni cambiar preferencias del usuario sin autorización. Para la prueba offline completa usar un entorno aislado sin conectividad o una desconexión controlada autorizada. Para rendimiento usar la telemetría de ejecuciones nuevas del perfil de prueba, separar carga e inferencia, fijar CPU/hilos/lote y repetir con condiciones registradas.
'''
write('INFORME_QA.md',report)
write('RESUMEN_ACADEMICO.md',f'''# Resumen académico

El 22 de noviembre de 2026 se realizó una verificación técnica de ProteinFunc AI Desktop en Windows 10 de 64 bits, con Python 3.12.10 y pytest 9.1.1. Se evaluó el repositorio en la rama main, commit `{env['commit']}`, y la distribución local disponible. La revisión se efectuó sin modificar el código de producción, los modelos ni las pruebas existentes.

De las 43 funciones de prueba identificadas, se ejecutaron 22 y todas aprobaron, sin fallos ni omisiones mediante skip. Pytest informó una duración de 0.53 segundos. Se verificaron validación de secuencias, detección de entradas incorrectas, advertencias de longitud, filtros, exportación CSV/TSV/JSON, persistencia y reapertura de resultados en bases temporales e integridad de artefactos. Las 21 pruebas restantes quedaron bloqueadas por dependencias ausentes. Los filtros y exportaciones se comprobaron con datos sintéticos, sin atribuirles significado biológico.

El comprobador distribuido cargó el modelo real y obtuvo predicciones en CPU para tres proteínas de muestra. En otra ejecución procesó únicamente el registro válido de un FASTA con cinco registros, descartando cuatro incorrectos. Ambos procesos finalizaron correctamente. La primera ejecución completa duró 29.0400 segundos y reportó 27.5 segundos de carga; la segunda duró {perf['seconds']:.4f} segundos y reportó 4.6 segundos de carga. El máximo de memoria residente del segundo proceso fue {perf['peak_working_set_bytes']/1024**2:.2f} MiB. No se midió el tiempo aislado de inferencia ni su rendimiento en proteínas por segundo.

Los siete archivos del modelo de la distribución coincidieron con los del repositorio por SHA-256, con huella de paquete `{fingerprint}`. La aplicación fuente declara versión 0.2.1, mientras que el comprobador distribuido informa 0.2.0; por ello no se establece equivalencia completa entre ambos programas. Las comprobaciones visuales no se ejecutaron debido a fallos de captura de la herramienta de escritorio. Se utilizó configuración lógica offline, sin desconectar físicamente la red, por lo que la operación sin conectividad permanece pendiente. Los resultados obtenidos verifican únicamente los comportamientos ejecutados y no constituyen una evaluación independiente de exactitud biológica ni del rendimiento oficial de CAFA.
''')

steps=[
'Ctrl+O → examples/pruebas/01_proteinas_conocidas.fasta; comprobar 8 registros válidos e identificadores visibles.',
'Cargar examples/muestra.fasta; comprobar tres proteínas disponibles para análisis.',
'Usar un archivo temporal vacío o pegar espacios; comprobar error y botón Analizar deshabilitado.',
'Cargar examples/con_errores.fasta; abrir Ver validación y comprobar duplicado valida_1 excluido.',
'En el mismo archivo comprobar símbolo # y posición 11; contrastar tabla de validación.',
'Cargar muestra.fasta y casos límite; comprobar aviso de longitud >512 antes de ejecutar y marca truncated después.',
'En perfil aislado ejecutar muestra.fasta; esperar finalización, tres resultados y puntuaciones; registrar tiempos.',
'Alternar MF/BP/CC individualmente; comprobar aspecto de todas las filas visibles y restablecer selección.',
'Comparar umbrales 0.10, 0.45 y 0.90, con mismos filtros; verificar que al elevar umbral no aumentan filas.',
'Buscar binding y un identificador GO realmente presente; comprobar filas coincidentes y limpiar búsqueda.',
'Exportar CSV a carpeta temporal nueva; verificar columnas, metadatos, acentos y concordancia con vista. Repetir con búsqueda activa para investigar el hallazgo estático.',
'Exportar TSV temporal; verificar tabuladores y filas contra CSV bajo iguales filtros.',
'Exportar JSON temporal; verificar schema_version, metadata, umbral, huella y estados de proteínas.',
'Abrir Ctrl+H solo en perfil de prueba; comprobar nueva ejecución, estado completado y filtros por fecha/huella/estado. No eliminar registros.',
'Cargar examples/pruebas/05_lote_300_sinteticas.fasta; iniciar y cancelar durante progreso; comprobar estado cancelado y ausencia de resultados parciales.',
'En entorno autorizado sin red física, reiniciar y ejecutar muestra.fasta; registrar conectividad, carga y predicciones. No cambiar conectividad del usuario durante esta auditoría.',
'Abrir Modelo; comprobar huella contra integridad_modelos.json. No alterar modelos originales. Para ensayo negativo, usar solo copia temporal y --model con autorización apropiada.',
'En perfil aislado cerrar y reabrir la aplicación; Ctrl+H → Abrir resultados de la ejecución de prueba; comparar proteínas, huella y filas con salida guardada.',
]
manual='# Protocolo manual GUI pendiente\n\nEstado actual de PF-01-GUI a PF-18-GUI: **NO EJECUTADO**. No hay capturas gráficas válidas de esta sesión.\n\nUsar exclusivamente un perfil de aplicación temporal aislado. La aplicación escribe SQLite y QSettings; cambiar solo el directorio de trabajo no aísla el historial. En el código, app._history_path usa QStandardPaths.AppDataLocation y History.__init__ puede actualizar ejecuciones interrumpidas. Para no alterar historial existente, preparar una cuenta/VM de prueba o verificar el aislamiento de APPDATA, LOCALAPPDATA y preferencias antes de abrir. No abrir otra instancia sobre la base del usuario. Usar el ejecutable ya disponible, sin instalar ni desinstalar.\n\nGuardar capturas sin información personal, exportaciones en carpeta temporal nueva y tiempos con inicio/fin. Estos pasos son instrucciones pendientes, no evidencia de aprobación.\n\n| ID | Procedimiento y criterio |\n|---|---|\n'
for c,step in zip(cases,steps): manual+=f'| {c[0]}-GUI | {step} |\n'
manual+='\nPara cada caso registrar versión del ejecutable, fecha y hora, entrada exacta, estado, observación y ruta de captura/salida. Para errores de exportación usar una ruta de prueba no escribible, sin cambiar permisos del sistema ni archivos del usuario. No usar Eliminar del historial. No aceptar ni eludir advertencias de seguridad. Los controles no ejecutados deben conservar NO EJECUTADO o BLOQUEADO hasta disponer de evidencia.\n'
write('MANUAL_GUI.md',manual)
(E/'incidencias_gui.json').write_text(json.dumps({'date':'2026-11-22','window':'ProteinFunc AI Desktop (existente)',
 'attempts':[{'action':'get_window_state, screenshot + accessibility','error':'FrameArrived timed out: timed out waiting on channel'},
 {'action':'recover window, activate_window, get_window_state','error':'window capture timed out: timed out waiting on channel'}],
 'result':'NO EJECUTADO: sin captura válida; no se lanzaron inferencias en GUI ni se abrió el historial'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Documentos QA generados.')
