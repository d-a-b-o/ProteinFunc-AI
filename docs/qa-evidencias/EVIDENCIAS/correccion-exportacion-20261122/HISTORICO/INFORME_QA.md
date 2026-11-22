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


---

# Ampliación QA: release final candidato 0.2.1

Fecha de cierre: 2026-11-22T14:00:18.024481-05:00. La sección anterior se conserva como **auditoría histórica**, con fuente 0.2.1 y distribución 0.2.0. Este anexo incorpora el ejecutable 0.2.1; no atribuye al binario las pruebas ejecutadas sobre el código fuente. Copias exactas de los cuatro documentos anteriores: `EVIDENCIAS/release-0.2.1-20261122/HISTORICO/`.

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
| ProteinFuncAI.exe | `f3dff02b5211e424d445f5161c95730aa0388339f379b91c41b8fc675c440acd` | `fd19a88d5cf15c4200244254d8d150b27dc0ed0e990bc9d1a74c0a5141ebbb12` |
| proteinfunc-check.exe | `94f346f18f0c12ee1d11f337e276a57da5a84c2da31d31399a91462ea38e071c` | `e5436f60f5891bf35028f449fb1c3b9f17c24a452e405cd3025148eb9b841612` |

Versiones observadas: [GUI --version](EVIDENCIAS/release-0.2.1-20261122/gui-version.stdout.log) y [CLI 0.2.1](EVIDENCIAS/release-0.2.1-20261122/cli-muestra.stdout.log). `--version` termina antes de construir QApplication/History; no es una prueba de inicio visual ni de carga del modelo en la GUI. El binario se ejecutó con stdout/stderr capturados y rutas de datos temporales para esta consulta.

Se calculó SHA-256 de **todos los archivos** de las dos distribuciones: [distribucion-0.2.0-sha256.json](EVIDENCIAS/release-0.2.1-20261122/distribucion-0.2.0-sha256.json) y [distribucion-0.2.1-sha256.json](EVIDENCIAS/release-0.2.1-20261122/distribucion-0.2.1-sha256.json). Estas huellas identifican los archivos locales y permiten detectar cambios; **no sustituyen una comparación con checksums oficiales del editor**, que no se suministraron.

Los siete archivos del modelo, incluido SHA256SUMS, coinciden entre fuente, 0.2.0 y 0.2.1. Huella estructurada del paquete: `7b9148321accb7d5d1b6b0b9727b5f307b9c173df68e0f1a85f8c561f210f2b0`. Los seis archivos listados en SHA256SUMS coinciden con los valores esperados, y el CLI 0.2.1 verificó 768 salidas/768 etiquetas al cargar pesos. [Evidencia de modelos](EVIDENCIAS/release-0.2.1-20261122/integridad-modelos.json). Los hashes de los dos ejecutables 0.2.0 también coinciden con los registrados en la auditoría previa, pese al cambio de nombre de su carpeta realizado antes de esta continuación.

La comprobación final no detectó archivos añadidos, eliminados o modificados en ninguna distribución, ni cambios en modelos o evidencias previas. No hubo commits ni pushes. [Registro de conservación](EVIDENCIAS/release-0.2.1-20261122/conservacion-y-cierre.json). El código empaquetado no contiene una atestación de commit comprobada: la versión declarada y la igualdad de modelos no prueban por sí solas identidad de todo el código con HEAD.

## Entorno autorizado y suite completa

El usuario autorizó crear `TF/.qa-venv-021`, con Python 3.12.10 e `include-system-site-packages=false`. Se instalaron los requisitos fijados sin actualizar el entorno global: numpy 2.1.3, torch 2.11.0+cpu, transformers 5.20.2, safetensors 0.8.0 y PySide6 6.12.0. Las herramientas de prueba resolvieron a pytest 9.2.0 y pytest-qt 4.5.0; Qt runtime/compilado 6.12.0 y pluggy 1.7.0. No se instaló PyInstaller, porque no se reconstruyeron binarios. `pip check` finalizó sin requisitos rotos. [Versiones completas](EVIDENCIAS/release-0.2.1-20261122/pip-freeze.stdout.log); [Consistencia de dependencias](EVIDENCIAS/release-0.2.1-20261122/pip-check.stdout.log); [Autorización y comandos de instalación](EVIDENCIAS/release-0.2.1-20261122/registro-instalacion.json). El log detallado se conserva comprimido y el bruto permanece en el venv, sin eliminarse.

El primer intento de descarga de torch falló por WinError 10013 del entorno aislado. Se autorizó el acceso de red adicional y la instalación concluyó correctamente. Esto es una incidencia de preparación del entorno, no un fallo de producto.

```powershell
.\.qa-venv-021\Scripts\python.exe -m pytest tests -v -p no:cacheprovider --basetemp <temporal-nueva> --junitxml <salida-nueva.xml>
```

Se ejecutó desde la raíz del repositorio, con QT_QPA_PLATFORM=offscreen, variables HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE=1 y bytecode deshabilitado. El comando y las rutas reales están en [pytest-completo-021.json](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.json). Resultado: **43 passed in 28.36s**, proceso completo **30.6897 s**, código 0. [Log completo](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.stdout.log); [JUnit](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml). Una ejecución preliminar de cuatro pruebas de validación también aprobó (0.11 s; ocho deseleccionadas), pero esas cuatro están incluidas en las 43 y **no se suman como casos únicos adicionales**.

Las 21 pendientes eran: una prueba de acuerdo validador/parser, una de versiones de modelo mezcladas, cinco de inferencia, trece de Qt y una de CLI. Todas aprobaron. Esto incorpora la comparación con reference_prediction.json de Kaggle con tolerancia absoluta 1e-5, consistencia de propagación GO, equivalencia por bloques, truncamiento, cancelación sin parciales y reapertura del historial. Las bases SQLite, preferencias y copias de modelos utilizadas son temporales y nuevas; el historial del usuario no se abrió.

## Repetición del comprobador 0.2.1

| Entrada | Salida real | Duración total medida | Evidencia |
|---|---|---|---|
| examples/muestra.fasta | 3 proteínas: P01308=36, ubiquitina=13, ejemplo_kaggle=45 términos a 0.45; ok=true | 7.0257 s | [cli-muestra.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-muestra.stdout.log) |
| examples/con_errores.fasta | 5 registros, 1 válido, 4 errores; solo valida_1 procesada; ok=true | 5.7295 s | [cli-errores.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-errores.stdout.log) |
| examples/pruebas/07_adn_en_vez_de_proteina.fasta | 3 registros, 1 válido, 2 errores; solo proteina_valida procesada; ok=true | 5.5897 s | [cli-adn-arn.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-adn-arn.stdout.log) |
| examples/pruebas/03_casos_limite.fasta | 6 válidos, 2 avisos; seis proteínas procesadas; ok=true | 6.0260 s | [cli-limites.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-limites.stdout.log) |

Los cuatro procesos terminaron con código 0. Los conteos del par muestra/errores coinciden con los registrados para 0.2.0. El CLI muestra solo una síntesis y los primeros términos redondeados: no demuestra igualdad numérica de todas las predicciones entre binarios. Los tiempos incluyen arranque, integridad, carga, validación e inferencia; no son tiempos aislados de inferencia ni permiten comparar velocidad entre versiones con condiciones de caché diferentes. Las cargas impresas para muestra, errores, ADN/ARN y límites fueron respectivamente 5.5, 5.0, 4.9 y 5.0 s. No se midió memoria máxima ni proteínas/s en esta ampliación.

Los logs CLI contienen algunos caracteres sustituidos por la codificación de consola Windows del binario; los identificadores, cifras y códigos de salida son legibles. Los mensajes completos y con acentos se conservan desde el validador fuente en JSON. No se reemplazaron estos logs por resultados de nuevas ejecuciones. El aviso PyTorch sobre redirecciones no soportadas en Windows no impidió finalizar.

## ADN/ARN y baja complejidad

El validador fuente 0.2.1 rechaza `adn_codificante` y `arn_mensajero` con estado error y el mensaje que comienza: “Parece una secuencia de ADN/ARN ... no de proteína”. El binario 0.2.1 confirma dos rechazos y solo infiere la proteína válida; no muestra los mensajes detallados en su CLI. El criterio inspeccionado es heurístico: longitud mínima 20, al menos 90% de A/C/G/T/U/N y tres nucleótidos distintos. No constituye una identificación universal de ADN/ARN.

Se comprobaron mensajes de causa: poliglicina de 50 residuos → “G ocupa el 100%”; ACDE repetido → “4 aminoácidos distintos”, diversidad 2.0 bits; residuos ambiguos → porcentaje y advertencia de poca fiabilidad. La secuencia corta ACGTACGT se acepta como control del límite de la heurística. Los avisos no excluyen proteínas: el CLI también predice para secuencias sintéticas de baja complejidad, por lo que esos puntajes no deben interpretarse como evidencia biológica. Las pruebas de Qt verifican además el aviso de secuencia atípica y el panel de resumen. [Mensajes y estados exactos](EVIDENCIAS/release-0.2.1-20261122/mensajes-validacion-fuente-021.json); tests/test_validation.py y test_gui.py::test_summary_panel_and_atypical_warning en el JUnit.

## Defecto adicional QA-021-EXPORT-BUSQUEDA

**Estado: FALLIDO. Severidad propuesta: media**, por discrepancia entre resultados visibles y archivo exportado. Alcance reproducido: código fuente 0.2.1, Qt offscreen, fixture sintética existente; no se ha confirmado la manifestación en el ejecutable mediante interacción visual.

Pasos reproducidos: construir MainWindow con History y QSettings temporales; cargar make_result() de tests/test_results_history.py; desactivar “solo específicos”; buscar GO:1; obtener el filtro con current_view() y exportar por el mismo mecanismo que usa export_results(). Resultado visible: **1 fila**. Resultado JSON: predicciones **GO:1 y GO:2**. Esperado según “Guardar los resultados visibles”: solo GO:1. La búsqueda sí funciona; es su aplicación a la exportación la que falla.

Evidencia: [busqueda-exportacion-qt.json](EVIDENCIAS/release-0.2.1-20261122/busqueda-exportacion-qt.json), [exportacion-con-busqueda.json](EVIDENCIAS/release-0.2.1-20261122/exportacion-con-busqueda.json); reproducción: [qa_funcional_021.py](qa_funcional_021.py). El script finaliza normalmente para conservar el diagnóstico; la conclusión funcional está en su campo status=FALLIDO. El código observado es main_window.py:600 (current_view), :656 (proxy de búsqueda), :781 (export_results), y core/results.py:43 (ViewFilter sin campo de búsqueda). La suite existente no cubre esta combinación; por ello el fallo adicional no se cuenta como un fallo de las 43 pruebas pytest. La comprobación adicional confirmó búsqueda y falló exportación; se informa como **un escenario adicional fallido**, no como dos casos independientes.

## Pendientes de aceptación del ejecutable

No quedan pruebas existentes bloqueadas por dependencias. Permanecen pendientes la interacción visual directa de PF-01 a PF-18 sobre el ejecutable 0.2.1, el contraste de exportación con búsqueda activa en ese binario y la desconexión física de Internet. Se conservan las 18 filas GUI como NO EJECUTADO; el éxito de Qt offscreen no las reemplaza. Los 18 escenarios funcionales por código/CLI tienen ahora 17 aprobados y PF-16 bloqueado; el defecto adicional se registra fuera de ese conteo base.

Aplicar [MANUAL_GUI.md](MANUAL_GUI.md) seleccionando `TF/ProteinFuncAI 0.2.1/ProteinFuncAI.exe`, con perfil Windows de prueba o VM aislada. QSettings en Windows puede usar el Registro: cambiar solo APPDATA no garantiza aislar preferencias. No abrir una segunda instancia contra el historial del usuario. Añadir revisión de mensajes completos de ADN/ARN y baja complejidad, y exportación con búsqueda activa. No eliminar historial, cambiar conectividad del equipo ni manipular modelos originales durante esa validación. Los casos pendientes deben aportar capturas, versión, entrada, fecha y resultado para considerarse ejecutados.

Se recomienda que el equipo de desarrollo revise el defecto antes de aceptar el release; esta auditoría no autoriza ni realiza su corrección. No se reevaluó calidad biológica ni métrica oficial CAFA, y no se presentan estimaciones como mediciones.
