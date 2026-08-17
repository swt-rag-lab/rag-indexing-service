# Spec 3 — Chunking: SemanticChunker

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 1

## Objetivo

Implementar el adaptador de chunking semántico que cumple el puerto
`ChunkingStrategy`. Divide texto canónico en chunks basados en tokens
usando tiktoken y semchunk.

## Entregables

### Adaptador (`infrastructure/chunking/semantic_chunker.py`)

#### `SemanticChunker`

Implementa `ChunkingStrategy`:

```python
class SemanticChunker:
    def __init__(self, max_tokens: int = 1024, overlap_tokens: int = 200, hard_max_tokens: int = 2048) -> None:
        ...

    def chunk(self, text: str) -> list[ChunkResult]:
        """Split text into semantic chunks respecting token and structural boundaries."""
        ...

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken (cl100k_base)."""
        ...
```

Comportamiento:
- Usa `tiktoken` con encoding `cl100k_base` (el tokenizer de OpenAI)
- Usa `semchunk` para splitting semántico que respeta oraciones/párrafos
- Cada chunk resultante tiene como máximo `max_tokens` tokens
- **Overlap obligatorio** entre chunks consecutivos:
  - Los últimos `overlap_tokens` tokens del chunk N se repiten al inicio del chunk N+1
  - Esto garantiza contexto compartido entre chunks adyacentes
  - El overlap mejora la calidad de retrieval en boundaries de chunks
  - Si un chunk es el último (o único), no tiene overlap posterior
  - El overlap se calcula en tokens, no en caracteres
  - Ejemplo con max_tokens=1024, overlap=200:
    - Chunk 0: tokens 0–1023
    - Chunk 1: tokens 824–1847 (los tokens 824–1023 son el overlap)
    - Chunk 2: tokens 1648–2671
- Retorna `list[ChunkResult]` con content, token_count, index, posición y metadata estructural
- Texto vacío retorna lista vacía
- Texto que cabe en un solo chunk retorna un solo ChunkResult (sin overlap)

### Extracción de metadata estructural

El canónico producido por Docling es **Markdown** con estructura explícita.
El SemanticChunker analiza esta estructura para enriquecer cada chunk:

#### Detección de secciones

| Patrón Markdown | section_type | Notas |
|---|---|---|
| `# Heading` | heading | H1 |
| `## Heading` | heading | H2 |
| `### Heading` | heading | H3+ |
| `\| col \| col \|` | table | Tablas markdown |
| `- item` / `* item` / `1. item` | list | Listas |
| Texto libre | paragraph | Default |

#### Jerarquía (hierarchy)

Se mantiene un stack de headings mientras se recorre el texto:

```text
# 1. General Information         → hierarchy: ["1. General Information"]
## 1.1 Purpose                   → hierarchy: ["1. General Information", "1.1 Purpose"]
## 1.2 Scope                     → hierarchy: ["1. General Information", "1.2 Scope"]
# 2. Technical Requirements      → hierarchy: ["2. Technical Requirements"]
## 2.1 Infrastructure            → hierarchy: ["2. Technical Requirements", "2.1 Infrastructure"]
```

Cada chunk hereda la jerarquía activa al momento de su inicio.

#### section_title

Es el heading más reciente antes del inicio del chunk.
Si el chunk comienza con un heading, ese es su `section_title`.

#### Páginas (page_start, page_end)

Si el markdown del canónico incluye marcadores de página (e.g., `<!-- page:3 -->`
o patrones similares insertados por el extractor), el chunker los detecta.
Si no hay marcadores → `page_start` y `page_end` son `None`.

Esto es best-effort: depende de que el extractor (Docling) inserte la info.

Manejo de errores:
- Si el texto tiene caracteres problemáticos → limpieza previa
- Si semchunk falla → fallback a split por tokens fijos
- Errores internos se traducen en `ChunkingError` (excepción de dominio)

### Preservación de contexto estructural

El chunker **NO debe romper** las siguientes estructuras del Markdown:

#### Reglas de preservación

| Estructura | Regla | Comportamiento si excede max_tokens |
|---|---|---|
| Tablas | NUNCA partir una tabla a la mitad | Si la tabla cabe → un solo chunk. Si la tabla excede max_tokens → chunk completo con la tabla (excepción al límite) |
| Listas | NUNCA partir un ítem de lista a la mitad | Si la lista completa cabe → un solo chunk. Si no cabe → partir entre ítems (nunca dentro de un ítem) |
| Headings | NUNCA separar un heading de su primer párrafo | El heading siempre va con al menos el primer bloque de contenido que le sigue |
| Secciones cortas | Sección completa (heading + contenido) < max_tokens → un solo chunk | No fragmentar secciones que caben enteras |
| Code blocks | NUNCA partir un bloque de código | Mismo tratamiento que tablas |

#### Algoritmo de chunking boundary-aware

```text
1. PARSE: Dividir el Markdown en bloques estructurales:
   - heading_block: heading + primer párrafo/contenido
   - table_block: tabla completa (desde | hasta última fila)
   - list_block: lista completa (todos los ítems)
   - paragraph_block: párrafo de texto libre
   - code_block: bloque de código completo

2. MERGE: Acumular bloques hasta llenar max_tokens:
   - Agregar bloques secuencialmente al chunk actual
   - Si agregar el siguiente bloque excede max_tokens:
     a. Si el chunk actual tiene contenido → cerrar chunk, empezar nuevo
     b. Si el chunk actual está vacío (bloque individual > max_tokens):
        - Es tabla/code/lista? → aceptar excepción (chunk grande)
        - Es párrafo largo? → partir por oraciones respetando max_tokens

3. OVERLAP: Aplicar overlap entre chunks:
   - El overlap se toma del FINAL del chunk anterior
   - El overlap NUNCA rompe una estructura (se ajusta al boundary más cercano)
   - Si el overlap caería a mitad de tabla → reducir overlap hasta antes de la tabla
   - Si el overlap caería a mitad de lista → reducir hasta antes del ítem

4. INDEX: Asignar metadata estructural a cada chunk
```

#### Ejemplos

**Ejemplo 1: Tabla que cabe en max_tokens**
```markdown
## 2.1 Requisitos técnicos          ← heading
                                     
El proveedor debe cumplir:           ← párrafo

| Requisito | Obligatorio |          ← tabla (inicio)
|---|---|
| AWS certified | Sí |
| ISO 27001 | Sí |
| SOC 2 | No |                       ← tabla (fin)
```
→ Un solo chunk (heading + párrafo + tabla juntos)

**Ejemplo 2: Tabla que excede max_tokens**
```markdown
| ... tabla de 1500 tokens ... |
```
→ Chunk individual con la tabla completa (excepción al límite de 1024 tokens).
Se prefiere un chunk grande a romper la tabla.

**Ejemplo 3: Lista larga**
```markdown
## Criterios de evaluación

1. Experiencia previa (300 tokens de detalle)
2. Capacidad técnica (400 tokens de detalle)
3. Propuesta económica (350 tokens de detalle)
4. Plan de implementación (300 tokens de detalle)
```
→ Chunk 1: heading + ítems 1 y 2 (≤ 1024 tokens)
→ Chunk 2: ítems 3 y 4 (con overlap que incluye el final del ítem 2)

**Ejemplo 4: Overlap respeta boundaries**
```markdown
[... chunk N termina con:]
| tabla completa |

[chunk N+1 empieza con:]
## Nueva sección
```
→ El overlap NO incluye parte de la tabla. Se toma del texto antes de la tabla,
o se reduce a 0 si no hay texto previo adecuado.

#### Configuración de tolerancia

| Parámetro | Default | Descripción |
|---|---|---|
| CHUNKING_MAX_TOKENS | 1024 | Límite soft (puede excederse para preservar estructuras) |
| CHUNKING_HARD_MAX_TOKENS | 2048 | Límite hard absoluto. Si un bloque atómico excede esto → warning + partir forzado |
| CHUNKING_OVERLAP_TOKENS | 200 | Target de overlap (se ajusta para respetar boundaries) |

Si una estructura atómica (tabla, code block) excede `HARD_MAX_TOKENS`:
- Log warning con el document_id y chunk_index
- Partir forzadamente por token boundary como último recurso
- Marcar el chunk con metadata `forced_split: true` para revisión

### `infrastructure/chunking/__init__.py`

Export de `SemanticChunker`.

### Configuración

Reutiliza settings de Spec 0:
- `CHUNKING_MAX_TOKENS` (default 1024)
- `CHUNKING_OVERLAP_TOKENS` (default 200)

#### Justificación del tamaño para RFP

Los documentos procesados son **RFPs (Request for Proposals)**, que se caracterizan por:
- Secciones densas con requisitos técnicos, legales y financieros
- Cláusulas que dependen del contexto de párrafos anteriores
- Tablas con especificaciones y criterios de evaluación
- Referencias cruzadas entre secciones

Por estas razones:
- **1024 tokens por chunk**: permite capturar secciones completas de requisitos sin fragmentar cláusulas a medio camino. Un chunk más pequeño (256–512) cortaría requisitos compuestos y perdería contexto necesario para responder preguntas sobre elegibilidad o cumplimiento.
- **200 tokens de overlap**: garantiza que el contexto compartido entre chunks adyacentes es suficiente para que el retrieval capture requisitos que cruzan boundaries. En RFPs, las oraciones de transición ("Additionally, the proposer must..." ) a menudo conectan requisitos del párrafo anterior.

Estos valores son configurables vía environment variables para ajustar según el tipo específico de RFP.

### Fakes (`tests/fakes/fake_chunking_strategy.py`)

#### `FakeChunkingStrategy`

- Acepta cualquier texto
- Retorna chunks de tamaño fijo predecible (e.g., divide por "\n\n" o cada N caracteres)
- Configurable: `chunk_size` en el constructor
- Útil para tests de application layer

## Pruebas

### Tests unitarios (`tests/unit/infrastructure/chunking/`)

#### `test_semantic_chunker.py`

**Básicos:**
- Texto corto (< max_tokens) → un solo chunk
- Texto largo → múltiples chunks, cada uno ≤ max_tokens (soft limit)
- Texto con párrafos → chunks respetan boundaries semánticos
- Token count correcto por chunk (verificado con tiktoken)
- Overlap: tokens compartidos entre chunks consecutivos
- Overlap: últimos N tokens del chunk i == primeros N tokens del chunk i+1
- Overlap: chunk único no tiene overlap
- Overlap: con 2 chunks, verificar que tokens compartidos = overlap_tokens
- Overlap con overlap_tokens=0 → sin repetición (chunks contiguos sin solapamiento)
- Texto vacío → lista vacía
- Texto solo whitespace → lista vacía
- Texto con caracteres Unicode → funciona correctamente
- Chunks indexados secuencialmente (0, 1, 2, ...)
- Content hash calculable para cada chunk

**Preservación de tablas:**
- Tabla que cabe en max_tokens → no se parte
- Tabla que excede max_tokens pero < hard_max → un solo chunk (excepción)
- Tabla que excede hard_max_tokens → split forzado + flag forced_split
- Heading + tabla juntos cuando caben

**Preservación de listas:**
- Lista completa que cabe → un solo chunk
- Lista larga → parte entre ítems, nunca dentro de un ítem
- Ítem con sub-ítems → no se parte el ítem padre
- Lista numerada preserva numeración en cada chunk

**Preservación de headings:**
- Heading nunca queda solo al final de un chunk (siempre va con contenido)
- Heading + primer párrafo son atómicos
- Sección completa < max_tokens → un solo chunk

**Preservación de code blocks:**
- Code block no se parte
- Code block que excede max_tokens → chunk individual (excepción)

**Overlap y boundaries:**
- Overlap no incluye parte de una tabla
- Overlap se ajusta hacia abajo si caería a mitad de estructura
- Overlap 0 si no hay texto adecuado antes de una estructura

**Metadata estructural:**
- section_type detectado correctamente para headings, tables, lists, paragraphs
- section_title asignado desde el heading más cercano
- hierarchy construida correctamente con headings anidados
- page markers detectados si están presentes

### Tests de edge cases

- Texto con una sola oración muy larga (> max_tokens) → se parte por oraciones o token boundary
- Tabla enorme (> hard_max_tokens) → split forzado con warning
- Documento con 50 tablas pequeñas consecutivas
- Texto con muchos saltos de línea consecutivos
- Texto con tabs y espacios mixtos
- Markdown con headings sin contenido entre ellos
- Lista con un solo ítem de 2000 tokens

## Criterios de Aceptación

- [ ] `SemanticChunker` implementa el puerto `ChunkingStrategy`
- [ ] Chunks respetan `max_tokens` como límite superior
- [ ] Tokenización usa tiktoken cl100k_base (compatible con OpenAI embeddings)
- [ ] Overlap funciona entre chunks consecutivos
- [ ] Texto vacío no produce chunks
- [ ] Errores internos se traducen en `ChunkingError`
- [ ] `FakeChunkingStrategy` disponible para tests de aplicación
- [ ] Tests unitarios pasan
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
