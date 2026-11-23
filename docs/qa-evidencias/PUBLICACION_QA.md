# Verificación previa al Pull Request

Rama preparada: `fix/qa-021-export-search`, destinada a `main` de `d-a-b-o/ProteinFunc-AI`. Base revisada: `c38323717be241cfa75d7684d0ff4ab7343270cd`. Los resultados siguientes corresponden al código corregido en esta rama; los registros anteriores se mantienen como históricos.

## Alcance de código

- `proteinfunc_app/core/results.py`: selección opcional por identidad y tratamiento de selección vacía; validación de claves únicas y aplicación común en CSV/TSV/JSON.
- `proteinfunc_app/ui/main_window.py`: captura de las identidades visibles del proxy, sin duplicar su búsqueda, y manejo de claves ambiguas.
- `tests/test_export_search.py`: 41 casos nuevos sobre datos sintéticos, Qt offscreen y archivos temporales.

No hay cambios de código fuera de esos tres archivos. No se cambian versión, inferencia, modelo, pesos, dependencias ni ejecutables.

## Última ejecución antes de publicar

Se utilizó el entorno existente `TF/.qa-venv-021`, sin instalar dependencias. Ambas ejecuciones finalizaron con código 0 y se realizaron en ese orden:

| Ejecución | Aprobadas | Fallidas | Omitidas | Duración pytest |
|---|---:|---:|---:|---:|
| Exportación, resultados/historial y GUI | 61 | 0 | 0 | 14.78 s |
| Suite completa: 43 originales + 41 regresiones | 84 | 0 | 0 | 18.06 s |

Evidencias nuevas, sin sobrescribir las anteriores:

- [Comando y hora de pruebas relacionadas](EVIDENCIAS/pre-publicacion-20261122/pruebas-relacionadas.json), [log](EVIDENCIAS/pre-publicacion-20261122/pruebas-relacionadas.log) y [JUnit](EVIDENCIAS/pre-publicacion-20261122/pruebas-relacionadas.xml).
- [Comando y hora de la suite completa](EVIDENCIAS/pre-publicacion-20261122/suite-completa.json), [log](EVIDENCIAS/pre-publicacion-20261122/suite-completa.log) y [JUnit](EVIDENCIAS/pre-publicacion-20261122/suite-completa.xml).
- [Exportaciones verificadas de nuevo](EVIDENCIAS/pre-publicacion-20261122/despues-comparacion.json).
- [Causa raíz, cobertura y evidencia antes/después](CORRECCION_EXPORTACION.md).

Las duraciones son de estas ejecuciones locales, no del servicio CI de GitHub. Las pruebas Qt se ejecutaron sin pantalla y no sustituyen una revisión visual del binario.

## Selección de documentación y evidencias

Se incluyen los documentos QA actualizados, scripts de reproducción, registros de pruebas, salidas sintéticas y huellas de integridad de los modelos y ejecutables. Los manifiestos de todas las bibliotecas distribuidas no son necesarios para revisar este defecto.

Se excluyen del commit los siguientes archivos de `EVIDENCIAS/release-0.2.1-20261122/`:

- `instalacion-dependencias.log.gz` (2 198 387 bytes): registro detallado de instalación.
- `distribucion-0.2.0-sha256.json` (850 825 bytes) y `distribucion-0.2.1-sha256.json` (850 673 bytes): inventarios completos de unas cinco mil bibliotecas por distribución.

Permanecen intactos en el equipo, al igual que el log bruto señalado en `registro-instalacion.json`. Los índices y enlaces históricos pueden citarlos como artefactos locales; su ausencia en Git no implica que se eliminaron durante esta preparación. La evidencia pequeña `integridad-modelos.json`, los hashes de ejecutables y `conservacion.json` siguen disponibles en el PR.

No se incluyen el entorno virtual externo al repositorio, temporales de pytest, bases SQLite, cachés, modelos duplicados ni ejecutables. Los documentos anteriores y los índices de evidencias se conservan; la selección de publicación no modifica sus resultados.

## Límite de publicación

Los ejecutables distribuidos todavía no incorporan la corrección. Este trabajo publica únicamente código, pruebas y evidencia QA mediante rama y PR; no incluye merge, release ni compilación. Los hashes y frases sobre ausencia de commits en informes anteriores describen el momento histórico de cada auditoría, anterior a la autorización de publicación.
