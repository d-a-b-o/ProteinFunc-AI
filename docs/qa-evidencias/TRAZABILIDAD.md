# Trazabilidad

Los identificadores RF/RNF proceden del README del repositorio; no se dispone de una especificación externa de aceptación. Rutas relativas a la raíz del repositorio.

| Escenario / requisito | Código fuente | Pruebas existentes | Resultado observado | Evidencia |
|---|---|---|---|---|
| PF-01 / RF-01 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: muestra.fasta: 3 registros válidos; lectura por código y CLI | [validacion_ejemplos.json](EVIDENCIAS/validacion_ejemplos.json) |
| PF-02 / RF-01 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: 8 proteínas conocidas y 300 sintéticas validadas; CLI predijo 3 proteínas | [validacion_ejemplos.json](EVIDENCIAS/validacion_ejemplos.json) |
| PF-03 / RF-02 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: Error global y cero aceptadas en cadena vacía; prueba pytest aprobada | [pytest-subconjunto.log](EVIDENCIAS/pytest-subconjunto.log) |
| PF-04 / RF-02 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: con_errores.fasta: segunda valida_1 rechazada | [validacion_ejemplos.json](EVIDENCIAS/validacion_ejemplos.json) |
| PF-05 / RF-02 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: Prueba verifica # en posición 11; CLI excluye entradas erróneas | [pytest-subconjunto.log](EVIDENCIAS/pytest-subconjunto.log) |
| PF-06 / RF-02 | [core/validation.py](../../proteinfunc_app/core/validation.py) | test_validation.py | APROBADO: muestra.fasta: un aviso; se conserva la secuencia completa en validación. Truncamiento tensorial pendiente | [validacion_ejemplos.json](EVIDENCIAS/validacion_ejemplos.json) |
| PF-07 / RF-07 | [inference/protein_go.py](../../proteinfunc_app/inference/protein_go.py) | test_inference.py (bloqueada; ejecución CLI alternativa) | APROBADO: CLI: 3 proteínas; 36, 13 y 45 términos a umbral 0.45; salida ok=true | [ejecutable-check.log](EVIDENCIAS/ejecutable-check.log) |
| PF-08 / RF-08 | [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py | APROBADO: 4 verificaciones adicionales: tres aspectos y umbrales; datos sintéticos | [filtros_adicionales.json](EVIDENCIAS/filtros_adicionales.json) |
| PF-09 / RF-08 | [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py | APROBADO: Fixture sintética: 4, 2 y 0 filas para 0.10, 0.45 y 0.95 | [filtros_adicionales.json](EVIDENCIAS/filtros_adicionales.json) |
| PF-10 / RF-08 | [ui/main_window.py](../../proteinfunc_app/ui/main_window.py) | test_gui.py::test_analyze_fasta_and_filter | BLOQUEADO: Depende del proxy Qt; PySide6 ausente y captura GUI fallida | [incidencias_gui.json](EVIDENCIAS/incidencias_gui.json) |
| PF-11 / RF-09 | [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py | APROBADO: pytest aprobado; archivo sintético conservado, incluye proteína sin términos | [exportacion_sintetica.csv](EVIDENCIAS/exportacion_sintetica.csv) |
| PF-12 / RF-09 | [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py | APROBADO: pytest aprobado; archivo sintético conservado | [exportacion_sintetica.tsv](EVIDENCIAS/exportacion_sintetica.tsv) |
| PF-13 / RF-09 | [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py | APROBADO: Roundtrip con acentos, estado y huella aprobado; salida sintética conservada | [exportacion_sintetica.json](EVIDENCIAS/exportacion_sintetica.json) |
| PF-14 / RF-11 | [core/history.py](../../proteinfunc_app/core/history.py) | test_results_history.py::test_history_lifecycle | APROBADO: SQLite nueva de prueba: estados, fecha y huella comprobados; no historial real | [pytest-subconjunto.log](EVIDENCIAS/pytest-subconjunto.log) |
| PF-15 / RF-10 | [services.py](../../proteinfunc_app/services.py) | test_inference.py::test_cancel_returns_none_not_partial; test_gui.py | BLOQUEADO: Requiere runtime no instalado; GUI no disponible | [entorno.json](EVIDENCIAS/entorno.json) |
| PF-16 / RNF-02 | [services.py](../../proteinfunc_app/services.py); [inference/protein_go.py](../../proteinfunc_app/inference/protein_go.py) | test_cli.py (bloqueada) | BLOQUEADO: CLI aprobó con HF_HUB_OFFLINE y TRANSFORMERS_OFFLINE; no se desconectó la red física | [ejecutable-check.json](EVIDENCIAS/ejecutable-check.json) |
| PF-17 / RF-06 / RNF-06 | [core/integrity.py](../../proteinfunc_app/core/integrity.py); [services.py](../../proteinfunc_app/services.py) | test_integrity.py | APROBADO: Ambos paquetes íntegros e idénticos; daños simulados en copias detectados; dimensiones 768 verificadas en CLI | [integridad_modelos.json](EVIDENCIAS/integridad_modelos.json) |
| PF-18 / RF-11 | [core/history.py](../../proteinfunc_app/core/history.py); [core/results.py](../../proteinfunc_app/core/results.py) | test_results_history.py::test_history_lifecycle; test_history_migrates_v01_database | APROBADO: SQLite temporal reabierta conserva proteínas y huella; compatibilidad de esquema antiguo aprobada | [pytest-subconjunto.log](EVIDENCIAS/pytest-subconjunto.log) |

La inferencia empaquetada pertenece a la versión 0.2.0; sus resultados no demuestran equivalencia numérica con el código 0.2.1. La identidad del modelo se demuestra por los hashes. El archivo tests/data/reference_prediction.json existe, pero la comparación numérica con Kaggle no se ejecutó. Las métricas de entrenamiento del manifiesto no se recalcularon.


---

# Trazabilidad añadida para 0.2.1

La trazabilidad histórica anterior permanece válida para su fecha y alcance. Commit fuente sin cambios: c38323717be241cfa75d7684d0ff4ab7343270cd. Los resultados de tests/ son de la fuente, mientras los cuatro cli-*.stdout.log proceden del ejecutable 0.2.1. No se intercambian ambas atribuciones.

| Requerimiento | Código / prueba | Resultado actual | Evidencia 0.2.1 |
|---|---|---|---|
| RF-01/RF-02 | core/validation.py; tests/test_validation.py | Validación, rechazo ADN/ARN y mensajes de complejidad aprobados | [mensajes-validacion-fuente-021.json](EVIDENCIAS/release-0.2.1-20261122/mensajes-validacion-fuente-021.json) |
| RF-06/RNF-06 | core/integrity.py; services.py; tests/test_integrity.py | Integridad, dimensiones y copias alteradas aprobadas | [integridad-modelos.json](EVIDENCIAS/release-0.2.1-20261122/integridad-modelos.json) |
| RF-07/RNF-04 | inference/protein_go.py; tests/test_inference.py | Referencia Kaggle y propagación aprobadas en fuente | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| RF-07 | proteinfunc-check.exe de 0.2.1 | Inferencia real de tres proteínas y dos controles adicionales | [cli-muestra.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-muestra.stdout.log) |
| RF-08 | core/results.py; ui/main_window.py; tests/test_gui.py | Filtros, umbral y búsqueda aprobados en fuente Qt | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| RF-09 | core/results.py; tests/test_results_history.py; test_export_from_gui | Formatos aprobados sin búsqueda activa | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| RF-08/RF-09 | ui/main_window.py:600,656,781; core/results.py:43; qa_funcional_021.py | FALLIDO: exportación ignora búsqueda del proxy | [busqueda-exportacion-qt.json](EVIDENCIAS/release-0.2.1-20261122/busqueda-exportacion-qt.json) |
| RF-10 | services.py; test_cancel_returns_none_not_partial; test_cancel_discards_partial_results | Cancelación sin resultados parciales aprobada en fuente | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| RF-11 | core/history.py; tests/test_results_history.py; test_history_reopen | Historial y reapertura aprobados con SQLite temporales | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| RNF-02 | services.py; test_cli.py | Offline lógico aprobado; desconexión física pendiente | [cli-adn-arn.json](EVIDENCIAS/release-0.2.1-20261122/cli-adn-arn.json) |
| RNF-05 | core/perf.py; test_performance_is_recorded; test_preferences_apply_batch_and_threads | Registro de telemetría y preferencias aprobados en fuente | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| Versionado de binario | ProteinFuncAI.exe --version; proteinfunc-check.exe | Ambos declaran 0.2.1; SHA de todos los archivos calculado | [gui-version.stdout.log](EVIDENCIAS/release-0.2.1-20261122/gui-version.stdout.log) |
| Conservación | Huellas antes/después, historial de documentos | Distribuciones y evidencias previas intactas | [conservacion-y-cierre.json](EVIDENCIAS/release-0.2.1-20261122/conservacion-y-cierre.json) |

Las 13 pruebas Qt no equivalen a las 18 comprobaciones manuales del ejecutable. El defecto adicional se confirmó en fuente; queda por contrastar su manifestación en el binario. No se probó procedencia criptográfica oficial del release ni exactitud biológica de las funciones predichas.


---

# Trazabilidad de la corrección de exportación

| Requisito | Implementación corregida | Regresión | Resultado / evidencia |
|---|---|---|---|
| RF-08/RF-09 | main_window.current_view(): identidades desde el proxy; ViewFilter.visible_keys | test_export_matches_visible_rows y test_search_reset_and_sorting_keep_identity | APROBADO; [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml) |
| RF-09 | RunResult.visible_predictions(), to_contract(), proteins_without_terms() | test_absent_and_empty_selection_are_distinct; once escenarios en tres formatos | APROBADO; [despues-comparacion.json](EVIDENCIAS/correccion-exportacion-20261122/despues-comparacion.json) |
| Identidad única | RunResult.validate_prediction_keys(); guarda en export_results() | test_ambiguous_prediction_keys_are_rejected; identidad P1/GO:1 frente a P2/GO:1 | APROBADO; [pruebas-relacionadas.xml](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.xml) |
| RF-11 | RunResult/SQLite sin selección persistida ni cambios de esquema | test_prediction_identity_is_unique_across_proteins_and_history más pruebas anteriores | APROBADO; [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml) |
| Conservación de filtros | Reconstrucción y resumen con include_search=False; intersección después de especificidad | Búsqueda de ancestro oculto y test_propagated_export_option_still_limits_visible_selection | APROBADO; [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml) |

Código evaluado: cambios sin commit sobre HEAD c38323717be241cfa75d7684d0ff4ab7343270cd, identificado mediante [correccion-produccion.patch](EVIDENCIAS/correccion-exportacion-20261122/correccion-produccion.patch) y sus hashes en [conservacion.json](EVIDENCIAS/correccion-exportacion-20261122/conservacion.json). Las 43 pruebas previas permanecen y pasan junto con 41 nuevas. Los ejecutables 0.2.0/0.2.1 siguen sin esta corrección. [Resumen de corrección](CORRECCION_EXPORTACION.md).
