Aplicación de escritorio para **predecir funciones Gene Ontology (MF, BP, CC)** de proteínas a partir de su secuencia. La inferencia es **100 % local**: no se necesita Internet ni Python, y no se envían secuencias a ningún servicio.

## Descargas

| Sistema | Archivo | Cómo instalar |
|---|---|---|
| **Windows 10/11 (64 bits)** | `ProteinFuncAI-VERSION-windows-x64-setup.exe` | Doble clic y seguir el asistente. No requiere permisos de administrador. |
| Windows (portable) | `ProteinFuncAI-VERSION-windows-x64-portable.zip` | Descomprimir y abrir `ProteinFuncAI\ProteinFuncAI.exe`. |
| **Linux x86_64** | `ProteinFuncAI-VERSION-linux-x86_64.tar.gz` | Descomprimir y ejecutar `./install.sh` (ver abajo). |

`SHA256SUMS.txt` contiene las huellas de cada descarga.

### Windows

1. Descarga el `setup.exe` y ábrelo.
2. Como el instalador no está firmado digitalmente, Windows puede mostrar «Windows protegió su PC»: pulsa **Más información → Ejecutar de todas formas**.
3. Abre **ProteinFunc AI Desktop** desde el menú Inicio. «Verificar instalación» comprueba el modelo sin conexión.

### Linux

```bash
tar -xzf ProteinFuncAI-VERSION-linux-x86_64.tar.gz
cd ProteinFuncAI-VERSION-linux-x86_64
./install.sh
```

Se instala para tu usuario (sin `sudo`) y aparece en el menú de aplicaciones. Si el instalador avisa de librerías faltantes, en Debian/Ubuntu: `sudo apt install libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libfontconfig1`; en Arch: `sudo pacman -S --needed mesa libxkbcommon-x11 xcb-util-cursor fontconfig`. Para desinstalar: `./install.sh --uninstall`.

## Novedades de esta versión

- **Rechazo de ADN/ARN**: si cargas una secuencia de nucleótidos (solo A, C, G, T/U), la aplicación la rechaza con un mensaje que pide traducirla a proteína. Antes se aceptaba como «proteína» y el modelo le asignaba funciones sin sentido.
- **Aviso de baja complejidad más claro**: indica la causa real (residuo dominante o poca diversidad de aminoácidos).
- **FASTA de prueba** en el repositorio (`examples/pruebas/`), con una guía del resultado esperado. No se incluyen en el instalador.

Incluye también todo lo de la 0.2.0: solo términos específicos, resumen por proteína, aviso de secuencias atípicas, Preferencias, rendimiento en el historial y licencias de terceros.

## Uso

Carga un FASTA (o pega una secuencia), pulsa **Analizar**, filtra por aspecto y umbral, y exporta a CSV, TSV o JSON. El historial guarda las ejecuciones anteriores.

## Modelo incluido

ESM-2 (`esm2_t6_8M_UR50D`, congelado) + capa lineal a 768 términos GO, entrenado con CAFA 6. Umbral 0,45; secuencias de más de 512 residuos se truncan (la app lo avisa). Micro-F1 de validación 0,399. Las métricas cubren el vocabulario seleccionado y no equivalen al puntaje oficial de CAFA.

> Los puntajes **no son probabilidades calibradas**. Las predicciones son hipótesis computacionales.
