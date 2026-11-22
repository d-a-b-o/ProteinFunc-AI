# Protocolo manual GUI pendiente

Estado actual de PF-01-GUI a PF-18-GUI: **NO EJECUTADO**. No hay capturas gráficas válidas de esta sesión.

Usar exclusivamente un perfil de aplicación temporal aislado. La aplicación escribe SQLite y QSettings; cambiar solo el directorio de trabajo no aísla el historial. En el código, app._history_path usa QStandardPaths.AppDataLocation y History.__init__ puede actualizar ejecuciones interrumpidas. Para no alterar historial existente, preparar una cuenta/VM de prueba o verificar el aislamiento de APPDATA, LOCALAPPDATA y preferencias antes de abrir. No abrir otra instancia sobre la base del usuario. Usar el ejecutable ya disponible, sin instalar ni desinstalar.

Guardar capturas sin información personal, exportaciones en carpeta temporal nueva y tiempos con inicio/fin. Estos pasos son instrucciones pendientes, no evidencia de aprobación.

| ID | Procedimiento y criterio |
|---|---|
| PF-01-GUI | Ctrl+O → examples/pruebas/01_proteinas_conocidas.fasta; comprobar 8 registros válidos e identificadores visibles. |
| PF-02-GUI | Cargar examples/muestra.fasta; comprobar tres proteínas disponibles para análisis. |
| PF-03-GUI | Usar un archivo temporal vacío o pegar espacios; comprobar error y botón Analizar deshabilitado. |
| PF-04-GUI | Cargar examples/con_errores.fasta; abrir Ver validación y comprobar duplicado valida_1 excluido. |
| PF-05-GUI | En el mismo archivo comprobar símbolo # y posición 11; contrastar tabla de validación. |
| PF-06-GUI | Cargar muestra.fasta y casos límite; comprobar aviso de longitud >512 antes de ejecutar y marca truncated después. |
| PF-07-GUI | En perfil aislado ejecutar muestra.fasta; esperar finalización, tres resultados y puntuaciones; registrar tiempos. |
| PF-08-GUI | Alternar MF/BP/CC individualmente; comprobar aspecto de todas las filas visibles y restablecer selección. |
| PF-09-GUI | Comparar umbrales 0.10, 0.45 y 0.90, con mismos filtros; verificar que al elevar umbral no aumentan filas. |
| PF-10-GUI | Buscar binding y un identificador GO realmente presente; comprobar filas coincidentes y limpiar búsqueda. |
| PF-11-GUI | Exportar CSV a carpeta temporal nueva; verificar columnas, metadatos, acentos y concordancia con vista. Repetir con búsqueda activa para investigar el hallazgo estático. |
| PF-12-GUI | Exportar TSV temporal; verificar tabuladores y filas contra CSV bajo iguales filtros. |
| PF-13-GUI | Exportar JSON temporal; verificar schema_version, metadata, umbral, huella y estados de proteínas. |
| PF-14-GUI | Abrir Ctrl+H solo en perfil de prueba; comprobar nueva ejecución, estado completado y filtros por fecha/huella/estado. No eliminar registros. |
| PF-15-GUI | Cargar examples/pruebas/05_lote_300_sinteticas.fasta; iniciar y cancelar durante progreso; comprobar estado cancelado y ausencia de resultados parciales. |
| PF-16-GUI | En entorno autorizado sin red física, reiniciar y ejecutar muestra.fasta; registrar conectividad, carga y predicciones. No cambiar conectividad del usuario durante esta auditoría. |
| PF-17-GUI | Abrir Modelo; comprobar huella contra integridad_modelos.json. No alterar modelos originales. Para ensayo negativo, usar solo copia temporal y --model con autorización apropiada. |
| PF-18-GUI | En perfil aislado cerrar y reabrir la aplicación; Ctrl+H → Abrir resultados de la ejecución de prueba; comparar proteínas, huella y filas con salida guardada. |

Para cada caso registrar versión del ejecutable, fecha y hora, entrada exacta, estado, observación y ruta de captura/salida. Para errores de exportación usar una ruta de prueba no escribible, sin cambiar permisos del sistema ni archivos del usuario. No usar Eliminar del historial. No aceptar ni eludir advertencias de seguridad. Los controles no ejecutados deben conservar NO EJECUTADO o BLOQUEADO hasta disponer de evidencia.
