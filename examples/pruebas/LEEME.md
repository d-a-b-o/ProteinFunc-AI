# FASTA de prueba

Archivos para probar la aplicación. Están solo en el repositorio; el instalador no los incluye. Se abren con **Cargar FASTA** o arrastrándolos a la ventana; `02` se pega en el cuadro de texto.

| Archivo | Contenido | Resultado esperado |
|---|---|---|
| `01_proteinas_conocidas.fasta` | 8 proteínas conocidas: hemoglobina α y β, mioglobina, citocromo c, calmodulina, lisozima C (humanas), GFP (*Aequorea victoria*) e insulina | 8 válidos. Por ejemplo, la calmodulina (P0DP23) recibe «calcium ion binding» con ~0,98 |
| `02_secuencia_para_pegar.txt` | Secuencia de GFP sin cabecera | 1 válido, identificado como `query_1` |
| `03_casos_limite.fasta` | Secuencia muy corta, minúsculas con espacios, `*` final, residuos ambiguos (X/B/Z/U/O), poliglicina y una secuencia aleatoria de 1500 aa | 6 válidos, 2 con aviso: la poliglicina (secuencia atípica) y la de 1500 aa (se truncará a 512) |
| `04_errores.fasta` | Secuencias vacías, números en la secuencia, ID duplicado y cabecera vacía | 7 registros, 2 válidos y 5 con error; el diálogo indica la línea y el problema de cada uno |
| `05_lote_300_sinteticas.fasta` | 300 secuencias aleatorias de 80 a 700 aa | Todas válidas; sirve para ver el progreso y probar **Cancelar** (Esc). ~13 s en CPU |
| `06_texto_antes_de_cabecera.fasta` | Una secuencia escrita antes de la primera cabecera `>` | Error claro: «hay texto antes de la primera cabecera» |
| `07_adn_en_vez_de_proteina.fasta` | Una secuencia de ADN, la misma como ARN y una proteína | 1 válido y 2 con error: «parece una secuencia de ADN/ARN; tradúcela primero» |

## Notas

- Las secuencias de `01` corresponden a entradas de UniProt (Swiss-Prot) y se usan solo para probar la aplicación. Antes de citarlas en un informe, conviene compararlas con UniProt.
- Las secuencias de `05` y la de 1500 aa de `03` son **aleatorias**: no son proteínas reales. El modelo les asigna funciones igualmente, lo que ilustra que los puntajes no son probabilidades calibradas.
- La poliglicina de `03` recibe muchas funciones sobre el umbral; la aplicación la marca como secuencia atípica.
- Un error frecuente es cargar ADN en lugar de proteína. Como A, C, G y T también son letras de aminoácidos, sin esta comprobación el modelo «predeciría» funciones sin sentido; por eso la aplicación rechaza las secuencias formadas casi solo por nucleótidos.
