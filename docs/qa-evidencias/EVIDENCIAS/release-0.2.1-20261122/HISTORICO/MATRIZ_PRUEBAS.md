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
