# Corrección QA-021-EXPORT-BUSQUEDA

Fecha: 2026-11-22T14:17:57.288670-05:00. **Estado: APROBADO en fuente local**, tras ejecutar las pruebas relacionadas y la suite completa. Base Git: c38323717be241cfa75d7684d0ff4ab7343270cd, con los cambios sin commit identificados en el patch de evidencia. La versión sigue siendo 0.2.1. Los ejecutables distribuidos 0.2.0 y 0.2.1 no se modificaron y **no incorporan esta corrección**.

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

Entorno existente `TF/.qa-venv-021`: Python 3.12.10, pytest 9.2.0, pytest-qt 4.5.0, PySide6/Qt 6.12.0; sin instalaciones adicionales. Se usaron QT_QPA_PLATFORM=offscreen, variables offline y bytecode deshabilitado. [Versiones exactas](EVIDENCIAS/correccion-exportacion-20261122/dependencias.txt).

| Ejecución | Casos | Aprobados | Fallidos | Omitidos | Duración pytest | Evidencia |
|---|---:|---:|---:|---:|---:|---|
| Regresiones antes de corregir | 41 | 3 | 38 | 0 | 2.12 s | [regresion-antes.log](EVIDENCIAS/correccion-exportacion-20261122/regresion-antes.log) |
| Relacionadas, después | 61 | 61 | 0 | 0 | 13.90 s | [pruebas-relacionadas.log](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.log) |
| Suite completa, después | 84 | 84 | 0 | 0 | 18.70 s | [suite-completa.log](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.log) |

La ejecución anterior de regresiones contiene tanto discrepancias funcionales como errores por las nuevas APIs aún ausentes; no representa 38 defectos independientes. Las capturas de exportación antes/después confirman por separado la discrepancia funcional. La suite final comprende las 43 pruebas originales, sin modificarlas, más 41 nuevas. No se suman las ejecuciones repetidas como casos únicos. Los procesos relacionados y completo finalizaron con código 0; los XML registran cero errores y cero skips. Las pequeñas diferencias de redondeo respecto al atributo time de JUnit no se interpretan como resultados diferentes. Comandos, horas y duraciones de proceso en los JSON homónimos.

Orden ejecutado:

```powershell
# Desde la raíz del repositorio, con el Python del venv QA:
..\.qa-venv-021\Scripts\python.exe -m pytest tests/test_export_search.py tests/test_results_history.py tests/test_gui.py -v
..\.qa-venv-021\Scripts\python.exe -m pytest tests -v
```

En las ejecuciones registradas se añadieron `-p no:cacheprovider`, `--basetemp` nuevo y `--junitxml` para conservar evidencias y evitar escribir cachés en el repositorio. [Comando relacionado exacto](EVIDENCIAS/correccion-exportacion-20261122/pruebas-relacionadas.json); [Comando completo exacto](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.json); [JUnit completo](EVIDENCIAS/correccion-exportacion-20261122/suite-completa.xml).

## Evidencia antes y después

Se capturó la misma fixture sintética en ambos estados: tres proteínas, términos GO compartidos entre P1/P2 y una proteína sin predicciones. Cada escenario se guardó en los tres formatos, sin sobrescribir archivos.

| Búsqueda | Predicciones visibles | Exportación antes, cada formato | Exportación después, cada formato |
|---|---:|---:|---:|
| Sin búsqueda | 5 | 5; se conserva registro de proteína sin términos | 5; mismo comportamiento |
| GO:1 | 2, una por proteína P1/P2 | 5, incorrecto | 2, exactamente las visibles |
| inexistente | 0 | 5, incorrecto | 0; sin registros de proteína añadidos |

[Comparación antes](EVIDENCIAS/correccion-exportacion-20261122/antes-comparacion.json); [Comparación después](EVIDENCIAS/correccion-exportacion-20261122/despues-comparacion.json). Archivos concretos: [JSON antes](EVIDENCIAS/correccion-exportacion-20261122/antes/GO1.json), [JSON después](EVIDENCIAS/correccion-exportacion-20261122/despues/GO1.json), [CSV después](EVIDENCIAS/correccion-exportacion-20261122/despues/GO1.csv), [TSV después](EVIDENCIAS/correccion-exportacion-20261122/despues/GO1.tsv). Las carpetas antes/ y despues/ contienen nueve salidas cada una, incluidas las búsquedas vacías y sin coincidencias. Los términos y secuencias son sintéticos; no constituyen predicciones experimentales.

El nuevo registro no reemplaza la evidencia histórica del caso original de una sola predicción visible; esta fixture amplía la comprobación a dos proteínas con el mismo GO para probar la identidad compuesta.

## Conservación y límites

[Verificación de conservación](EVIDENCIAS/correccion-exportacion-20261122/conservacion.json) confirma que los dos únicos archivos rastreados modificados son los dos componentes de producción indicados, que el modelo fuente y todos los archivos de las distribuciones 0.2.0/0.2.1 mantienen sus hashes, y que las evidencias anteriores no cambiaron. `git diff --check` aprobó. [Patch de producción](EVIDENCIAS/correccion-exportacion-20261122/correccion-produccion.patch) y [Copia exacta de las nuevas pruebas](EVIDENCIAS/correccion-exportacion-20261122/test_export_search.py) permiten identificar el código evaluado sin crear commits.

Los cuatro documentos QA previos se conservaron completos y recibieron únicamente anexos. Sus copias anteriores están en HISTORICO/. No se modificaron inferencia, pesos, versión, pruebas originales, resultados experimentales, ejecutables ni historial real. No se hicieron commits, pushes, compilaciones o releases.

La validación es automatizada sobre código fuente y Qt offscreen; no acredita revisión visual del escritorio. Los binarios distribuidos conservan la implementación anterior, por lo que el defecto no se declara resuelto en ellos. Permanecen pendientes, fuera de esta corrección, la comprobación visual de un futuro binario que incorpore el cambio y la operación con Internet físicamente desconectado. Los metadatos y el campo input de JSON conservan el contrato anterior: la búsqueda limita predicciones exportadas, no elimina el texto FASTA original ni añade un nuevo campo de búsqueda al esquema.

Reproducción de evidencias: [qa_correccion_exportacion.py](qa_correccion_exportacion.py), etapas prepare (solo antes de aplicar el patch y en carpeta nueva), related y full. Las rutas existentes no deben reutilizarse para sobrescribir esta auditoría. [qa_documentar_correccion.py](qa_documentar_correccion.py) añade los documentos solo si siguen coincidiendo con sus copias iniciales.
