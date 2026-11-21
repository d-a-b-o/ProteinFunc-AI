# ProteinFunc AI Desktop

Aplicación de escritorio para **predecir funciones Gene Ontology (MF, BP, CC) de proteínas** a partir de su secuencia, con **inferencia 100 % local** (sin conexión). Usa el modelo entrenado en Kaggle con los datos de CAFA 6: ESM-2 congelado + cabeza de clasificación multietiqueta.

Funciona en **Windows 64 bits y Linux** (Python + PySide6).

> Las predicciones son hipótesis computacionales. Los puntajes son salidas sigmoid con propagación por la jerarquía GO: **no son probabilidades calibradas**. Que ninguna función supere el umbral no implica que la proteína carezca de función.

## Qué hace

| Función | Requisito |
|---|---|
| Cargar un FASTA (botón o arrastrar y soltar) o pegar una secuencia / FASTA | RF-01 |
| Validar **todos** los registros: vacíos, IDs duplicados, cabeceras vacías, símbolos no admitidos (con posición), secuencias que se truncarán | RF-02 |
| Verificar el paquete del modelo antes de analizar: archivos, manifiesto, ancestros GO, dimensiones pesos ↔ vocabulario y **SHA-256** de cada archivo contra `model/SHA256SUMS` | RF-06, RNF-06 |
| Predecir y aplicar las reglas GO (`is_a`, `part_of`); distinguir puntaje **directo** de **propagado** | RF-07 |
| Tabla Proteína · Término GO · Nombre · Aspecto · Origen · Puntuación; filtros MF/BP/CC, umbral, proteína y búsqueda; panel de detalle | RF-08 |
| Exportar **CSV, TSV o JSON** con los filtros visibles y metadatos (versión, huella del modelo, umbral) | RF-09 |
| Análisis en segundo plano con progreso y **cancelación** (nunca muestra resultados parciales) | RF-10 |
| **Historial** local en SQLite: filtrar por fecha, versión del modelo y estado; reabrir resultados | RF-11 |

## Instalación (desarrollo)

Requiere **Python 3.11, 3.12 o 3.13** (64 bits). La instalación necesita Internet; el uso posterior no.

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m proteinfunc_app
```

**Linux:**

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
```

```bash
pip install -r requirements.txt
```

```bash
python -m proteinfunc_app
```

En Linux, PySide6 necesita las librerías gráficas del sistema (en Debian/Ubuntu: `sudo apt install libegl1 libgl1 libxkbcommon0 libfontconfig1`).

### Verificación sin interfaz

Comprueba el paquete y predice un FASTA desde consola. Sirve para validar una instalación nueva con la red desactivada:

```bash
python -m proteinfunc_app --check examples/muestra.fasta
```

## Uso

1. **Cargar FASTA** (Ctrl+O), arrastrar el archivo a la ventana o pegar la secuencia en el cuadro de texto.
2. Revisar el resumen de validación; «Ver validación» muestra cada registro y su problema.
3. **Analizar** (Ctrl+Enter). **Esc** cancela.
4. Filtrar por aspecto, umbral (por defecto el del modelo, 0,45), proteína o texto (Ctrl+F). Seleccionar una fila muestra el detalle: puntaje directo, origen y ancestros GO.
5. **Exportar** (Ctrl+E) en CSV (UTF-8 con BOM, compatible con Excel), TSV o JSON.
6. **Historial** (Ctrl+H) para reabrir ejecuciones anteriores. **Paquete del modelo** muestra manifiesto, verificaciones, huellas SHA-256, métricas de validación y versiones.

`examples/muestra.fasta` trae tres proteínas (una se trunca a 512 residuos) y `examples/con_errores.fasta` muestra cómo se reportan los errores.

### Formatos de exportación

- **CSV / TSV**: líneas de metadatos que empiezan con `#` y luego las columnas `protein_id, go_term, name, aspect, score, direct_score, origin, length, residues_used, truncated`. Las proteínas sin funciones sobre el umbral aparecen con `go_term` vacío. En pandas: `pd.read_csv(ruta, comment="#")`.
- **JSON**: el mismo contrato que `ProteinGOPredictor.predict` (`schema_version`, `model`, `input`, `results` con `status` y `truncated`) más una clave `metadata`.

## Estructura

```text
proteinfunc_app/
├── app.py                 # Punto de entrada (GUI y --check)
├── paths.py               # Rutas de recursos (desarrollo y ejecutable)
├── services.py            # Hilo de inferencia: carga única, bloques, progreso, cancelación
├── inference/protein_go.py# Runtime exportado desde Kaggle (+ direct_score/origin para RF-07)
├── core/                  # Sin interfaz: validation, integrity, results (exportación), history
└── ui/                    # PySide6: main_window, dialogs, widgets, theme (estilo de la maqueta)
model/                     # Paquete del modelo (manifest.json, weights.pt, backbone/, SHA256SUMS)
examples/                  # FASTA de ejemplo
tests/                     # pytest (usa el modelo real)
tools/make_checksums.py    # Regenera model/SHA256SUMS
proteinfunc.spec           # PyInstaller
```

## Actualizar el modelo

1. Exportar el nuevo `desktop_model.zip` desde el notebook de Kaggle.
2. Reemplazar el contenido de `model/` por la carpeta `model/` del ZIP (`manifest.json`, `weights.pt`, `backbone/`).
3. Si cambió `protein_go.py`, copiarlo a `proteinfunc_app/inference/` y volver a añadir los campos `direct_score` y `origin` en `predict_records`.
4. Regenerar las huellas y correr las pruebas:

```bash
python tools/make_checksums.py
```

```bash
python -m pytest tests -q
```

`tests/data/reference_prediction.json` es el `example_prediction.json` del ZIP: la prueba `test_matches_reference_prediction_from_kaggle` comprueba que la app reproduce las salidas del notebook (RNF-04). Hay que reemplazarlo junto con el modelo.

Para usar otro paquete sin tocar `model/`: `python -m proteinfunc_app --model RUTA` o la variable de entorno `PROTEINFUNC_MODEL_DIR`.

## Pruebas

```bash
pip install -r requirements-dev.txt
```

```bash
python -m pytest tests -q
```

Cubren validación, integridad (archivo alterado, faltante, manifiesto incoherente, versiones mezcladas), consistencia con el notebook, puntajes directos/propagados, cancelación, exportación CSV/TSV/JSON con acentos, historial y la interfaz completa en modo sin pantalla.

## Ejecutable (PyInstaller)

PyInstaller no compila entre sistemas: el `.exe` se genera en Windows y el binario de Linux en Linux. Instalar PyTorch **CPU** antes de empaquetar para no incluir CUDA.

```bash
pip install -r requirements-dev.txt
```

```bash
pyinstaller proteinfunc.spec --noconfirm
```

El resultado queda en `dist/ProteinFuncAI/` (ejecutable `ProteinFuncAI` / `ProteinFuncAI.exe` junto con `_internal/`, que incluye el modelo). Se distribuye la carpeta completa.

## Datos del modelo incluido

Según `model/manifest.json`:

- Backbone `facebook/esm2_t6_8M_UR50D` congelado (320 dimensiones) + capa lineal a **768 términos GO** (256 por aspecto, mínimo 20 proteínas de entrenamiento).
- Secuencias de más de **512 residuos se truncan** (prefijo); la app lo avisa por proteína.
- Umbral 0,45 elegido en validación. Validación: micro-F1 0,399 (MF 0,421 · BP 0,328 · CC 0,484).
- 82 404 proteínas de CAFA 6; particiones 70/15/15 agrupando solo secuencias idénticas.
- Las métricas cubren el vocabulario seleccionado y **no equivalen al puntaje oficial de CAFA**.

## Licencias

ESM-2 (Meta AI) se distribuye con licencia MIT. Revisar las reglas de la competencia CAFA 6 en Kaggle antes de redistribuir artefactos derivados de sus datos.
