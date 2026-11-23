# Informe técnico QA — ProteinFunc AI Desktop

Fecha de auditoría: 2026-11-22, zona America/Lima (UTC−05:00). Evidencias generadas hasta 2026-11-22T13:38:14.551417-05:00.

## Resultado y alcance

Se clonó el repositorio solicitado en `TF/ProteinFunc-AI`, rama `main`, HEAD `c38323717be241cfa75d7684d0ff4ab7343270cd`. El árbol estaba limpio inmediatamente después de clonar. Se ejecutaron **22 pruebas pytest: 22 aprobadas, 0 fallidas y 0 skipped**, con **2 deseleccionadas** dentro del subconjunto elegido. El inventario completo contiene 43 funciones: **21 quedaron bloqueadas** por dependencias ausentes (incluye las dos deseleccionadas). No se ejecutó la orden completa `python -m pytest tests -v`, pues el entorno no estaba preparado. No se equiparan casos no ejecutados con pruebas aprobadas.

Dos ejecuciones reales de `proteinfunc-check.exe` finalizaron con código 0 y `ok=true`: una con tres proteínas válidas y otra con un archivo de cinco registros, de los cuales solo uno era válido. Además, cuatro verificaciones de filtros sobre datos sintéticos aprobaron. Esos controles adicionales y los dos procesos CLI se contabilizan por separado de pytest. La matriz de 18 escenarios registra 15 aprobados en el alcance de código/CLI y 3 bloqueados. Las 18 validaciones directas de GUI quedaron NO EJECUTADO.

No se modificaron producción, pruebas existentes, modelos, ejecutables ni historial del usuario; no se instalaron dependencias, no se entrenó y no se hicieron commits o pushes. Solo se añadieron documentos y scripts de evidencia. Las pruebas de integridad alteran exclusivamente copias temporales; las pruebas de historial crean SQLite nuevas. Esas copias temporales se trasladaron a la carpeta temporal del sistema para conservar evidencias pequeñas, sin eliminar archivos existentes. Véase `EVIDENCIAS/temporales.json`.

## Adquisición y entorno

Git disponible: 2.51.0.windows.1 (versión del archivo 2.51.0.1). La carpeta destino no existía. La primera clonación falló por conectividad a github.com:443 en el entorno aislado; se repitió con permiso adicional y concluyó correctamente. Git bloqueó después la consulta por propiedad distinta entre usuario aislado y propietario; se autorizó la consulta con el propietario. No se cambió la configuración global de Git.

Sistema observado: `Windows-10-10.0.19045-SP0`, AMD64. Python 3.12.10 de 64 bits, pytest 9.1.1, pluggy 1.6.0 y psutil 7.2.2. En este intérprete faltan numpy, torch, transformers, safetensors, PySide6 y pytest-qt. La consulta `py -0p` no enumeró otros intérpretes, aunque `python` sí funciona. No se identificó un entorno virtual del proyecto en las carpetas inspeccionadas. Se solicitó autorización para crear un entorno aislado e instalar dependencias; no se realizó instalación en esta auditoría.

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
| Huella del paquete | `7b9148321accb7d5d1b6b0b9727b5f307b9c173df68e0f1a85f8c561f210f2b0` | Idéntica |
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
| Segunda ejecución CLI completa | 5.2669 s | Un registro aceptado; incluye arranque/carga/validación/inferencia |
| Memoria máxima segunda ejecución | 411533312 bytes (392.47 MiB) | Peak working set del proceso CLI; psutil, 104 muestras a intervalos nominales de 50 ms |
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
