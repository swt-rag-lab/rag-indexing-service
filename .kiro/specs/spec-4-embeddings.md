# Spec 4 — Embeddings: OpenAI Adapter

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 1

## Objetivo

Implementar el adaptador de generación de embeddings que cumple el puerto
`Embedder`. Usa la API de OpenAI para generar vectores a partir de texto.

## Diseño desacoplado

El embedding está completamente desacoplado del proveedor:

```text
domain/ports/embedder.py          ← Protocol (contrato)
        ↑
infrastructure/embeddings/
├── openai_embedder.py            ← Adaptador OpenAI (implementación actual)
├── (futuro) cohere_embedder.py   ← Adaptador Cohere
├── (futuro) local_embedder.py    ← Adaptador con sentence-transformers local
└── (futuro) bedrock_embedder.py  ← Adaptador AWS Bedrock
```

Para agregar un nuevo proveedor en el futuro:
1. Crear un nuevo archivo en `infrastructure/embeddings/` que implemente `Embedder`
2. Configurar el proveedor vía settings (e.g., `EMBEDDING_PROVIDER=cohere`)
3. En `bootstrap/container.py`, instanciar el adaptador según la config
4. **Cero cambios en dominio o application layer**

La selección del proveedor se hace en el composition root (`bootstrap/`),
no en el dominio ni en la capa de aplicación.

### Configuración de selección (futuro-ready)

```text
EMBEDDING_PROVIDER=openai          # openai | cohere | local | bedrock
OPENAI_API_KEY=sk-...              # solo si provider=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
```

Por ahora solo se implementa OpenAI, pero la config `EMBEDDING_PROVIDER`
queda preparada para routing en container.

## Entregables

### Adaptador (`infrastructure/embeddings/openai_embedder.py`)

#### `OpenAIEmbedder`

Implementa `Embedder`:

```python
class OpenAIEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        batch_size: int = 100,
    ) -> None:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        If len(texts) > batch_size, splits into sub-batches and concatenates results.
        Maintains order.
        """
        ...

    @property
    def model_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...
```

Comportamiento:
- Usa el SDK `openai` (AsyncOpenAI client)
- Modelo default: `text-embedding-3-small` (1536 dimensiones)
- Batch processing: si la lista excede `batch_size`, divide en sub-lotes
- Mantiene orden estricto: `results[i]` corresponde a `texts[i]`
- Valida que los vectores retornados tengan las dimensiones esperadas
- Retry con backoff exponencial usando `tenacity` para:
  - Rate limit errors (429)
  - Server errors (5xx)
  - Timeout errors
- Max reintentos: 3
- Backoff: 1s, 2s, 4s

Manejo de errores:
- `openai.RateLimitError` → retry con backoff
- `openai.APIError` → retry para 5xx, fail para 4xx
- `openai.AuthenticationError` → `EmbeddingError` inmediato (no retry)
- Timeout → retry
- Cualquier error tras agotar reintentos → `EmbeddingError` (excepción de dominio)
- Texto vacío en la lista → `EmbeddingError` (validación previa)

### `infrastructure/embeddings/__init__.py`

Export de `OpenAIEmbedder`.

### Configuración

Reutiliza settings de Spec 0:
- `OPENAI_API_KEY` (requerido)
- `OPENAI_EMBEDDING_MODEL` (default: text-embedding-3-small)
- `OPENAI_EMBEDDING_DIMENSIONS` (default: 1536)
- `OPENAI_EMBEDDING_BATCH_SIZE` (default: 100)

### Fakes (`tests/fakes/fake_embedder.py`)

#### `FakeEmbedder`

- Retorna vectores deterministas basados en hash del texto
- Dimensiones configurables
- `embed_batch(texts)` → lista de vectores de longitud fija
- Permite configurar fallos (para testing de error handling)
- Propiedades `model_name` y `dimensions` retornan valores fijos

```python
class FakeEmbedder:
    def __init__(self, dimensions: int = 1536, should_fail: bool = False) -> None:
        self._dimensions = dimensions
        self._should_fail = should_fail
        self.calls: list[list[str]] = []  # tracking de llamadas

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        if self._should_fail:
            raise EmbeddingError("Fake embedding failure")
        return [self._deterministic_vector(t) for t in texts]
```

## Pruebas

### Tests unitarios (`tests/unit/infrastructure/embeddings/`)

#### `test_openai_embedder.py`

- Batching: 250 textos con batch_size=100 → 3 llamadas a la API
- Orden preservado: resultado[i] corresponde a input[i]
- Validación de dimensiones: si la API retorna dims incorrectas → error
- Texto vacío en batch → `EmbeddingError`
- Lista vacía → retorna lista vacía

Nota: estos tests requieren mock del cliente OpenAI (usar `unittest.mock.AsyncMock` o similar).

### Tests de integración (`tests/integration/embeddings/`) [marcados `slow`]

#### `test_openai_embedder_integration.py`

- Embedding de un texto corto → vector de 1536 dims
- Embedding de batch de 3 textos → 3 vectores correctos
- Requiere `OPENAI_API_KEY` real (marcado `slow` + `integration`)

### Tests del fake

- FakeEmbedder retorna vectores con dimensiones correctas
- FakeEmbedder es determinista (mismo texto → mismo vector)
- FakeEmbedder registra llamadas

## Criterios de Aceptación

- [ ] `OpenAIEmbedder` implementa el puerto `Embedder`
- [ ] Batching funciona para listas grandes
- [ ] Orden estricto preservado
- [ ] Retry con backoff para rate limits y server errors
- [ ] Auth errors fallan inmediatamente (no retry)
- [ ] Errores del SDK traducidos en `EmbeddingError`
- [ ] `FakeEmbedder` disponible y determinista
- [ ] Tests unitarios (con mock) pasan
- [ ] Tests de integración pasan contra API real (marcados slow)
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
