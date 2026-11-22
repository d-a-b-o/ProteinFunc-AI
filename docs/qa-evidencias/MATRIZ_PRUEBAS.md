# Matriz de pruebas

Fecha: 22 de noviembre de 2026, America/Lima. Commit: `c38323717be241cfa75d7684d0ff4ab7343270cd`.

Los estados de la primera tabla corresponden exclusivamente al alcance indicado (código, fixture o CLI). No acreditan interacción gráfica. 15 APROBADO, 0 FALLIDO y 3 BLOQUEADO; este conteo de escenarios no se suma al de pytest.

| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| PF-01 | RF-01 | Cargar FASTA válido | Leer secuencias e identificadores | muestra.fasta: 3 registros válidos; lectura por código y CLI | APROBADO | [Registro](EVIDENCIAS/validacion_ejemplos.json) |
| PF-02 | RF-01 | Cargar múltiples proteínas | Conservar registros del lote | 8 proteínas conocidas y 300 sintéticas validadas; CLI predijo 3 proteínas | APROBADO | [Registro](EVIDENCIAS/validacion_ejemplos.json) |
| PF-03 | RF-02 | Validar FASTA vacío | Rechazar entrada vacía | Error global y cero aceptadas en cadena vacía; prueba pytest aprobada | APROBADO | [Registro](EVIDENCIAS/pytest-subconjunto.log) |
| PF-04 | RF-02 | Detectar identificadores duplicados | Informar duplicado y excluirlo | con_errores.fasta: segunda valida_1 rechazada | APROBADO | [Registro](EVIDENCIAS/validacion_ejemplos.json) |
| PF-05 | RF-02 | Detectar caracteres inválidos | Informar símbolo y posición | Prueba verifica # en posición 11; CLI excluye entradas erróneas | APROBADO | [Registro](EVIDENCIAS/pytest-subconjunto.log) |
| PF-06 | RF-02 | Advertir truncamiento | Avisar al exceder 512 residuos | muestra.fasta: un aviso; se conserva la secuencia completa en validación. Truncamiento tensorial pendiente | APROBADO | [Registro](EVIDENCIAS/validacion_ejemplos.json) |
| PF-07 | RF-07 | Ejecutar inferencia | Obtener predicciones del modelo real | CLI: 3 proteínas; 36, 13 y 45 términos a umbral 0.45; salida ok=true | APROBADO | [Registro](EVIDENCIAS/ejecutable-check.log) |
| PF-08 | RF-08 | Filtrar MF/BP/CC | Retener solo aspecto seleccionado | 4 verificaciones adicionales: tres aspectos y umbrales; datos sintéticos | APROBADO | [Registro](EVIDENCIAS/filtros_adicionales.json) |
| PF-09 | RF-08 | Modificar umbral | Cambiar filas según umbral | Fixture sintética: 4, 2 y 0 filas para 0.10, 0.45 y 0.95 | APROBADO | [Registro](EVIDENCIAS/filtros_adicionales.json) |
| PF-10 | RF-08 | Buscar términos GO | Filtrar por identificador o nombre | Depende del proxy Qt; PySide6 ausente y captura GUI fallida | BLOQUEADO | [Registro](EVIDENCIAS/incidencias_gui.json) |
| PF-11 | RF-09 | Exportar CSV | Columnas, metadatos y acentos correctos | pytest aprobado; archivo sintético conservado, incluye proteína sin términos | APROBADO | [Registro](EVIDENCIAS/exportacion_sintetica.csv) |
| PF-12 | RF-09 | Exportar TSV | Separación por tabuladores y metadatos | pytest aprobado; archivo sintético conservado | APROBADO | [Registro](EVIDENCIAS/exportacion_sintetica.tsv) |
| PF-13 | RF-09 | Exportar JSON | Contrato y metadatos recuperables | Roundtrip con acentos, estado y huella aprobado; salida sintética conservada | APROBADO | [Registro](EVIDENCIAS/exportacion_sintetica.json) |
| PF-14 | RF-11 | Consultar historial | Listar y filtrar ejecuciones | SQLite nueva de prueba: estados, fecha y huella comprobados; no historial real | APROBADO | [Registro](EVIDENCIAS/pytest-subconjunto.log) |
| PF-15 | RF-10 | Cancelar procesamiento | Descartar resultados parciales | Requiere runtime no instalado; GUI no disponible | BLOQUEADO | [Registro](EVIDENCIAS/entorno.json) |
| PF-16 | RNF-02 | Ejecutar sin Internet | Inferir con conectividad del equipo desactivada | CLI aprobó con HF_HUB_OFFLINE y TRANSFORMERS_OFFLINE; no se desconectó la red física | BLOQUEADO | [Registro](EVIDENCIAS/ejecutable-check.json) |
| PF-17 | RF-06 / RNF-06 | Verificar integridad del modelo | Hashes y coherencia correctos; rechazar daños | Ambos paquetes íntegros e idénticos; daños simulados en copias detectados; dimensiones 768 verificadas en CLI | APROBADO | [Registro](EVIDENCIAS/integridad_modelos.json) |
| PF-18 | RF-11 | Reabrir resultados anteriores | Recuperar resultados persistidos | SQLite temporal reabierta conserva proteínas y huella; compatibilidad de esquema antiguo aprobada | APROBADO | [Registro](EVIDENCIAS/pytest-subconjunto.log) |

## Validación directa de la GUI

No hubo captura utilizable ni interacción funcional confirmada. Las 18 comprobaciones siguientes están NO EJECUTADO. La detección de una ventana existente no prueba el inicio correcto.

| ID | Escenario | Estado | Evidencia |
|---|---|---|---|
| PF-01-GUI | Cargar FASTA válido | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-02-GUI | Cargar múltiples proteínas | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-03-GUI | Validar FASTA vacío | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-04-GUI | Detectar identificadores duplicados | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-05-GUI | Detectar caracteres inválidos | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-06-GUI | Advertir truncamiento | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-07-GUI | Ejecutar inferencia | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-08-GUI | Filtrar MF/BP/CC | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-09-GUI | Modificar umbral | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-10-GUI | Buscar términos GO | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-11-GUI | Exportar CSV | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-12-GUI | Exportar TSV | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-13-GUI | Exportar JSON | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-14-GUI | Consultar historial | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-15-GUI | Cancelar procesamiento | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-16-GUI | Ejecutar sin Internet | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-17-GUI | Verificar integridad del modelo | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |
| PF-18-GUI | Reabrir resultados anteriores | NO EJECUTADO | [Fallos de captura](EVIDENCIAS/incidencias_gui.json) |

## Inventario de pruebas automatizadas

43 funciones encontradas por AST. 22 ejecutadas y aprobadas; 21 bloqueadas por el entorno. Pytest: 0 fallidas, 0 omitidas mediante skip y 2 deseleccionadas en el subconjunto; los otros 19 casos no se recolectaron.

| Prueba existente | Estado | Evidencia / motivo |
|---|---|---|
| `test_cli.py::test_check_runs_from_other_directory_with_spaces` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_analyze_fasta_and_filter` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_model_loaded_once` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_gui_matches_predictor` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_invalid_records_are_excluded` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_cancel_discards_partial_results` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_export_from_gui` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_history_reopen` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_broken_bundle_disables_analysis` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_summary_panel_and_atypical_warning` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_performance_is_recorded` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_preferences_apply_batch_and_threads` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_settings_persist` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_gui.py::test_about_and_preferences_dialogs` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_inference.py::test_matches_reference_prediction_from_kaggle` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_inference.py::test_direct_and_propagated_scores` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_inference.py::test_chunked_prediction_equals_single_call` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_inference.py::test_cancel_returns_none_not_partial` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_inference.py::test_truncation_flag` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_integrity.py::test_real_bundle_passes_and_matches_checksums` | APROBADO | pytest-subconjunto.log y XML |
| `test_integrity.py::test_tampered_file_is_detected` | APROBADO | pytest-subconjunto.log y XML |
| `test_integrity.py::test_missing_file_is_detected` | APROBADO | pytest-subconjunto.log y XML |
| `test_integrity.py::test_inconsistent_manifest_is_detected` | APROBADO | pytest-subconjunto.log y XML |
| `test_integrity.py::test_mixed_versions_are_rejected_when_loading` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_results_history.py::test_filters` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_json_export_roundtrip_with_accents` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_csv_and_tsv_exports_match_view` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_history_lifecycle` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_specific_only_hides_visible_ancestors` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_history_migrates_v01_database` | APROBADO | pytest-subconjunto.log y XML |
| `test_results_history.py::test_peak_memory_is_measured` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_raw_sequence_is_single_query` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_empty_input_is_global_error` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_reports_every_problem_not_only_the_first` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_long_sequence_is_warning_and_keeps_full_sequence` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_uniprot_ids_are_normalised_like_runtime` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_validation_agrees_with_runtime_parser` | BLOQUEADO | Dependencias del runtime / pytest-qt ausentes; no ejecutada |
| `test_validation.py::test_reads_latin1_files` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_text_before_first_header_is_clear_error` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_low_complexity_is_warning_but_real_proteins_are_not` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_example_test_files_validate_as_documented` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_dna_and_rna_are_rejected_but_protein_extremes_are_not` | APROBADO | pytest-subconjunto.log y XML |
| `test_validation.py::test_low_complexity_message_explains_the_cause` | APROBADO | pytest-subconjunto.log y XML |


---

# Ampliación de matriz: 0.2.1

Las tablas anteriores son históricas. Estado actual: suite fuente 43/43 aprobadas; 21 pendientes previas resueltas. No sumar ejecuciones repetidas como pruebas únicas. Base PF: 17 APROBADO, 0 FALLIDO, 1 BLOQUEADO en alcance código/CLI. Un escenario adicional de exportación con búsqueda activa está FALLIDO. Las 18 validaciones GUI del ejecutable permanecen NO EJECUTADO.

| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| PF-01-021 | RF-01 | FASTA válido | Comportamiento del requisito en el alcance evaluado | Fuente y CLI 0.2.1: carga y validación | APROBADO | [cli-muestra.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-muestra.stdout.log) |
| PF-02-021 | RF-01 | Múltiples proteínas | Comportamiento del requisito en el alcance evaluado | Fuente Qt y CLI: tres proteínas | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-03-021 | RF-02 | Entrada vacía | Comportamiento del requisito en el alcance evaluado | test_empty_input_is_global_error | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-04-021 | RF-02 | IDs duplicados | Comportamiento del requisito en el alcance evaluado | test_reports_every_problem_not_only_the_first | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-05-021 | RF-02 | Caracteres inválidos | Comportamiento del requisito en el alcance evaluado | Errores y exclusión en fuente/CLI | APROBADO | [cli-errores.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-errores.stdout.log) |
| PF-06-021 | RF-02 | Aviso/truncamiento | Comportamiento del requisito en el alcance evaluado | Avisos y residues_used=512 en inferencia fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-07-021 | RF-07 | Inferencia | Comportamiento del requisito en el alcance evaluado | Fuente frente a Kaggle; CLI real 0.2.1 | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-08-021 | RF-08 | MF/BP/CC | Comportamiento del requisito en el alcance evaluado | Motor de filtros y Qt fuente; no GUI del binario | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-09-021 | RF-08 | Umbral | Comportamiento del requisito en el alcance evaluado | Motor y deslizador Qt fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-10-021 | RF-08 | Buscar GO | Comportamiento del requisito en el alcance evaluado | Búsqueda GO:1 produce una fila en Qt offscreen | APROBADO | [busqueda-exportacion-qt.json](EVIDENCIAS/release-0.2.1-20261122/busqueda-exportacion-qt.json) |
| PF-11-021 | RF-09 | CSV sin búsqueda activa | Comportamiento del requisito en el alcance evaluado | Exportación por código con fixture; búsqueda activa falla aparte | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-12-021 | RF-09 | TSV sin búsqueda activa | Comportamiento del requisito en el alcance evaluado | Exportación por código, no diálogo del binario | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-13-021 | RF-09 | JSON sin búsqueda activa | Comportamiento del requisito en el alcance evaluado | Contrato y flujo de resultados Qt por código | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-14-021 | RF-11 | Historial | Comportamiento del requisito en el alcance evaluado | Base temporal; fuente y Qt | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-15-021 | RF-10 | Cancelar | Comportamiento del requisito en el alcance evaluado | Fuente y Qt cancelan sin parciales | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| PF-16-021 | RNF-02 | Sin Internet físico | Comportamiento del requisito en el alcance evaluado | Solo variables offline; red del sistema sin desconectar | BLOQUEADO | [cli-muestra.json](EVIDENCIAS/release-0.2.1-20261122/cli-muestra.json) |
| PF-17-021 | RF-06/RNF-06 | Integridad | Comportamiento del requisito en el alcance evaluado | SHA, coherencia, carga 768/768 y rechazo de copias alteradas | APROBADO | [integridad-modelos.json](EVIDENCIAS/release-0.2.1-20261122/integridad-modelos.json) |
| PF-18-021 | RF-11 | Reabrir resultados | Comportamiento del requisito en el alcance evaluado | SQLite temporal y Qt fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| QA-021-ADN | RF-02 | ADN/ARN frente a proteína | Rechazar ambos nucleótidos y aceptar proteína | Fuente: mensajes de error; CLI 0.2.1 solo procesa proteina_valida | APROBADO | [mensajes-validacion-fuente-021.json](EVIDENCIAS/release-0.2.1-20261122/mensajes-validacion-fuente-021.json) / [cli-adn-arn.stdout.log](EVIDENCIAS/release-0.2.1-20261122/cli-adn-arn.stdout.log) |
| QA-021-COMPLEJIDAD | RF-02/UX | Causas de baja complejidad | Advertir causa y poca fiabilidad sin rechazar | Mensajes de predominio, diversidad y ambigüedad; Qt verifica banner | APROBADO | [mensajes-validacion-fuente-021.json](EVIDENCIAS/release-0.2.1-20261122/mensajes-validacion-fuente-021.json) / [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| QA-021-EXPORT-BUSQUEDA | RF-08/RF-09 | Exportar con búsqueda GO:1 | Exportar únicamente GO:1 visible | Una fila visible; JSON exporta GO:1 y GO:2 en fuente Qt offscreen | FALLIDO | [busqueda-exportacion-qt.json](EVIDENCIAS/release-0.2.1-20261122/busqueda-exportacion-qt.json) / [exportacion-con-busqueda.json](EVIDENCIAS/release-0.2.1-20261122/exportacion-con-busqueda.json) |

## Resolución individual de las 21 pendientes

| Prueba | Modalidad | Estado 0.2.1 | Evidencia |
|---|---|---|---|
| `test_cli.py::test_check_runs_from_other_directory_with_spaces` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_analyze_fasta_and_filter` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_model_loaded_once` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_gui_matches_predictor` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_invalid_records_are_excluded` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_cancel_discards_partial_results` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_export_from_gui` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_history_reopen` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_broken_bundle_disables_analysis` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_summary_panel_and_atypical_warning` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_performance_is_recorded` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_preferences_apply_batch_and_threads` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_settings_persist` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_gui.py::test_about_and_preferences_dialogs` | Qt offscreen fuente | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_inference.py::test_matches_reference_prediction_from_kaggle` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_inference.py::test_direct_and_propagated_scores` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_inference.py::test_chunked_prediction_equals_single_call` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_inference.py::test_cancel_returns_none_not_partial` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_inference.py::test_truncation_flag` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_integrity.py::test_mixed_versions_are_rejected_when_loading` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |
| `test_validation.py::test_validation_agrees_with_runtime_parser` | Código/CLI fuente en venv | APROBADO | [pytest-completo-021.xml](EVIDENCIAS/release-0.2.1-20261122/pytest-completo-021.xml) |

## Interfaz directa del ejecutable 0.2.1

| ID | Estado | Próxima validación |
|---|---|---|
| PF-01-GUI-021 | NO EJECUTADO | FASTA válido, en perfil aislado según MANUAL_GUI.md |
| PF-02-GUI-021 | NO EJECUTADO | Múltiples proteínas, en perfil aislado según MANUAL_GUI.md |
| PF-03-GUI-021 | NO EJECUTADO | Entrada vacía, en perfil aislado según MANUAL_GUI.md |
| PF-04-GUI-021 | NO EJECUTADO | IDs duplicados, en perfil aislado según MANUAL_GUI.md |
| PF-05-GUI-021 | NO EJECUTADO | Caracteres inválidos, en perfil aislado según MANUAL_GUI.md |
| PF-06-GUI-021 | NO EJECUTADO | Aviso/truncamiento, en perfil aislado según MANUAL_GUI.md |
| PF-07-GUI-021 | NO EJECUTADO | Inferencia, en perfil aislado según MANUAL_GUI.md |
| PF-08-GUI-021 | NO EJECUTADO | MF/BP/CC, en perfil aislado según MANUAL_GUI.md |
| PF-09-GUI-021 | NO EJECUTADO | Umbral, en perfil aislado según MANUAL_GUI.md |
| PF-10-GUI-021 | NO EJECUTADO | Buscar GO, en perfil aislado según MANUAL_GUI.md |
| PF-11-GUI-021 | NO EJECUTADO | CSV sin búsqueda activa, en perfil aislado según MANUAL_GUI.md |
| PF-12-GUI-021 | NO EJECUTADO | TSV sin búsqueda activa, en perfil aislado según MANUAL_GUI.md |
| PF-13-GUI-021 | NO EJECUTADO | JSON sin búsqueda activa, en perfil aislado según MANUAL_GUI.md |
| PF-14-GUI-021 | NO EJECUTADO | Historial, en perfil aislado según MANUAL_GUI.md |
| PF-15-GUI-021 | NO EJECUTADO | Cancelar, en perfil aislado según MANUAL_GUI.md |
| PF-16-GUI-021 | NO EJECUTADO | Sin Internet físico, en perfil aislado según MANUAL_GUI.md |
| PF-17-GUI-021 | NO EJECUTADO | Integridad, en perfil aislado según MANUAL_GUI.md |
| PF-18-GUI-021 | NO EJECUTADO | Reabrir resultados, en perfil aislado según MANUAL_GUI.md |


---

# Regresión de la corrección QA-021-EXPORT-BUSQUEDA

Los estados históricos anteriores se mantienen. Este anexo acredita la fuente local corregida, no los ejecutables distribuidos. Suite final: 84 APROBADO, 0 FALLIDO, 0 BLOQUEADO y 0 NO EJECUTADO entre los casos automatizados recolectados; las comprobaciones manuales pendientes conservan su estado anterior.

| ID | Requerimiento | Escenario | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| FIX-01 | RF-09 | Sin búsqueda | Mismas predicciones y estados anteriores | 5 predicciones; se conserva proteína sin términos | APROBADO | [despues/sin-busqueda.json](EVIDENCIAS/correccion-exportacion-20261122/despues/sin-busqueda.json) |
| FIX-02 | RF-08/RF-09 | Buscar GO:1 | Solo pares visibles | 2 visibles y 2 exportados, P1/GO:1 y P2/GO:1 | APROBADO | [despues/GO1.json](EVIDENCIAS/correccion-exportacion-20261122/despues/GO1.json) |
| FIX-03 | RF-08/RF-09 | Nombre, mayúsculas y espacios | Mismas coincidencias que Qt | Regresiones CSV/TSV/JSON aprobadas | APROBADO | [pruebas-relacionadas.xml](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.xml) |
| FIX-04 | RF-08/RF-09 | Búsqueda + MF/BP/CC y umbral | Intersección de filtros | Tres aspectos y umbrales comprobados | APROBADO | [pruebas-relacionadas.xml](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.xml) |
| FIX-05 | RF-09 | Sin coincidencias | Cero predicciones, sin volver a todas | JSON results vacío; CSV/TSV solo metadatos y cabecera | APROBADO | [despues/sin-coincidencias.json](EVIDENCIAS/correccion-exportacion-20261122/despues/sin-coincidencias.json) |
| FIX-06 | RF-08/RF-09 | Limpiar búsqueda y ordenar | Recuperar datos sin cambiar identidades | None frente a conjunto vacío y orden comprobados | APROBADO | [pruebas-relacionadas.xml](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.xml) |
| FIX-07 | RF-09 | Identidad compuesta | GO compartido entre proteínas no colisiona | Mismo GO en P1/P2 independiente; pares duplicados rechazados | APROBADO | [pruebas-relacionadas.xml](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.xml) |
| FIX-08 | RF-11 | Historial y reapertura | Selección temporal sin migraciones | SQLite temporal reabierta; selección no persistida | APROBADO | [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml) |
| FIX-09 | RF-08/RF-09 | Solo específicos y propagados | Mantener filtros anteriores | Ancestro oculto no reaparece; opción de propagados limita selección | APROBADO | [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml) |

Todas las regresiones identificadas individualmente en [suite-completa.xml](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml). El fallo reproducido antes de la implementación se conserva en [regresion-antes.log](EVIDENCIAS/correccion-exportacion-20261122/regresion-antes.log); no se cuenta como fallo de la suite final.
