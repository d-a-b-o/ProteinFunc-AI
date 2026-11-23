# Registro de adquisición y cierre

Registro redactado a partir de las salidas de herramientas de esta sesión; no es una transcripción de Git.

- Fecha: 2026-11-22, America/Lima.
- Antes de clonar: Git localizado en `C:\Program Files\Git\cmd\git.exe`; `Test-Path ProteinFunc-AI` devolvió False.
- Primer intento: `git clone https://github.com/d-a-b-o/ProteinFunc-AI ProteinFunc-AI`; falló con `Failed to connect to github.com port 443 ... Could not connect to server` en el entorno restringido.
- Reintento con permiso adicional de red: completado con código 0.
- Consulta inicial de Git desde usuario aislado: `detected dubious ownership`. Se consultaron rama, HEAD y estado con el propietario tras autorización, sin modificar configuración global.
- Rama: main. Commit: c38323717be241cfa75d7684d0ff4ab7343270cd. Estado inicial: limpio.
- Estado final leído mediante excepción safe.directory limitada a la invocación (`git -c`, sin persistir configuración): únicamente `?? docs/`.
- `git diff --stat` final: vacío. HEAD final: c38323717be241cfa75d7684d0ff4ab7343270cd.
- No commits, pushes, correcciones de código ni instalaciones de dependencias.
- Se comprobaron los enlaces relativos de los cinco Markdown de entrega: ninguno roto.
- Inventario AST: 43 funciones de prueba. JUnit y log: 22 aprobadas, 0 fallidas, 0 skipped. Dos deseleccionadas dentro del subconjunto. Otras 19 no recolectadas por selección de módulos; total pendiente 21.
- Cuatro comprobaciones adicionales de filtros aprobadas y dos procesos CLI con código 0, contabilizados aparte.
- Evidencias pequeñas: aproximadamente 131 KB antes de este registro y el inventario final. Las copias de modelos de pytest se trasladaron fuera del directorio de evidencias a temporales del sistema, sin eliminar datos existentes.
- Autorización para instalar dependencias: solicitada; no concedida al cierre de esta ejecución. No se asumió autorización por ausencia de respuesta.

No se generaron capturas válidas: los errores de la herramienta de escritorio constan en incidencias_gui.json. No se atribuyen esos errores al producto.
