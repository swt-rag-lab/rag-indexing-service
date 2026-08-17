# Spec 1 — Dominio Core: Entidades, Value Objects, Puertos y Políticas

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 0

## Objetivo

Modelar las reglas de negocio de indexación documental sin dependencia de
infraestructura. El dominio define el ciclo de vida de un IndexingJob,
los metadatos de un Chunk, los puertos para capacidades externas y las
políticas de generación de IDs deterministas.

## Entregables

### Value Objects (`domain/value_objects/`)

#### `tenant_id.py` — TenantId

- Wrapper de `str` con validación (no vacío, formato slug)
- Igualdad por valor
- Mismo patrón que ingestion-service y document-processing-service

#### `indexing_status.py` — IndexingStatus

- Enum: `PENDING`, `CHUNKING`, `EMBEDDING`, `STORING`, `COMPLETED`, `FAILED`
- Transiciones válidas definidas como método estático o dict

#### `chunk_id.py` — ChunkId

- UUID del chunk
- Factory method `generate(document_id, version_id, chunk_index)` → determinista
  basado en UUID5 con namespace fijo

#### `point_id.py` — PointId

- ID del punto en Qdrant (string UUID determinista)
- Factory method `generate(tenant_id, document_id, version_id, chunk_index)` → UUID5
- Garantiza idempotencia: mismos inputs = mismo point_id

#### `embedding_model.py` — EmbeddingModel

- Dataclass con: `name` (str), `dimensions` (int), `version` (str)
- Validación: dimensions > 0, name no vacío

#### `chunking_config.py` — ChunkingConfig

- Dataclass con: `max_tokens` (int), `overlap_tokens` (int), `version` (str)
- Defaults: max_tokens=1024, overlap_tokens=200 (optimizado para RFPs)
- Invariante: `overlap_tokens < max_tokens`

#### `content_hash.py` — ContentHash

- Wrapper sobre SHA-256 hex string
- Factory method `from_text(text: str) -> ContentHash`

### Entidades (`domain/entities/`)

#### `indexing_job.py` — IndexingJob

Campos:
- `id: UUID`
- `tenant_id: TenantId`
- `document_id: UUID`
- `version_id: UUID`
- `status: IndexingStatus`
- `total_chunks: int | None`
- `processed_chunks: int`
- `embedding_model: str`
- `chunking_version: str`
- `error_message: str | None`
- `correlation_id: str`
- `created_at: datetime`
- `updated_at: datetime`

Métodos de transición:
- `start_chunking()` — PENDING → CHUNKING
- `start_embedding(total_chunks: int)` — CHUNKING → EMBEDDING
- `start_storing()` — EMBEDDING → STORING
- `complete()` — STORING → COMPLETED
- `fail(reason: str)` — cualquier estado → FAILED

Invariantes:
- Transiciones inválidas lanzan `InvalidStatusTransitionError`
- No puede completar si `total_chunks` es None
- `updated_at` se actualiza en cada transición

Factory method:
- `IndexingJob.create(tenant_id, document_id, version_id, correlation_id, embedding_model, chunking_version)` → job en PENDING

#### `chunk.py` — Chunk

Campos:
- `id: ChunkId`
- `tenant_id: TenantId`
- `document_id: UUID`
- `version_id: UUID`
- `chunk_index: int`
- `content: str`
- `token_count: int`
- `content_hash: ContentHash`
- `point_id: PointId` (ID determinista para Qdrant)
- `start_token: int` (posición de inicio en el documento, para trazabilidad)
- `end_token: int` (posición de fin en el documento)
- `has_overlap: bool` (indica si este chunk tiene overlap con el anterior)
- `created_at: datetime`

Metadata de origen (trazabilidad end-to-end):
- `source_content_type: str` (content_type del documento original, e.g. "application/pdf")
- `source_content_hash: str` (hash del canónico completo)
- `extractor_type: str` (qué extractor produjo el canónico: docling, pymupdf, plain_text)
- `extractor_version: str` (versión del extractor)
- `embedding_model: str` (modelo usado para generar el embedding)
- `chunking_version: str` (versión de la estrategia de chunking)

Metadata estructural (derivada del contenido del chunk):
- `section_type: str | None` — tipo de sección detectada (e.g., "heading", "paragraph", "table", "list", "requirements", "scope", "evaluation_criteria", "terms_and_conditions")
- `section_title: str | None` — título/heading más cercano al inicio del chunk (extraído del markdown del canónico)
- `page_start: int | None` — página de inicio estimada (si el canónico incluye marcadores de página)
- `page_end: int | None` — página de fin estimada
- `hierarchy: list[str]` — jerarquía de headings (e.g., ["1. Introduction", "1.2 Scope", "1.2.1 Technical Requirements"])

La metadata estructural es especialmente valiosa para documentos RFP porque:
- Permite filtrar búsquedas por tipo de sección ("buscar solo en requisitos técnicos")
- Permite mostrar contexto al usuario ("este resultado viene de la sección 3.2 Evaluación")
- Permite al retrieval-service ponderar resultados según la sección
- El campo `hierarchy` permite reconstruir la posición exacta en el documento

Invariantes:
- `chunk_index >= 0`
- `token_count > 0`
- `content` no vacío
- `start_token >= 0`
- `end_token > start_token`

Factory method:
- `Chunk.create(tenant_id, document_id, version_id, chunk_index, content, token_count, start_token, end_token, has_overlap, source_metadata, structural_metadata)` → calcula chunk_id, point_id y content_hash automáticamente

La metadata de origen permite trazar cualquier chunk hasta:
1. El documento original (document_id + version_id)
2. El canónico del que se derivó (source_content_hash)
3. El extractor que lo produjo (extractor_type + version)
4. El modelo de embedding usado (embedding_model)
5. La versión del chunking (chunking_version)
6. La sección del documento de donde proviene (section_type, section_title, hierarchy)

### Eventos de Dominio (`domain/events/`)

#### `document_indexing_started.py` — DocumentIndexingStarted

- tenant_id, document_id, version_id, job_id, correlation_id, occurred_at
- `event_type` → `"document.indexing.started.v1"`

#### `document_indexed.py` — DocumentIndexed

- tenant_id, document_id, version_id, job_id, total_chunks, embedding_model, chunking_version, correlation_id, occurred_at
- `event_type` → `"document.indexed.v1"`

#### `document_indexing_failed.py` — DocumentIndexingFailed

- tenant_id, document_id, version_id, job_id, reason, correlation_id, occurred_at
- `event_type` → `"document.indexing.failed.v1"`

### Puertos (`domain/ports/`)

#### `embedder.py` — Embedder Protocol

```python
class Embedder(Protocol):
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...

    @property
    def model_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...
```

#### `vector_store.py` — VectorStore Protocol

```python
class VectorStore(Protocol):
    async def upsert_points(
        self,
        points: list[VectorPoint],
    ) -> None:
        """Upsert points (vectors + payloads) to the store."""
        ...

    async def delete_points_by_document(
        self,
        tenant_id: str,
        document_id: str,
        version_id: str,
    ) -> int:
        """Delete all points for a specific document version. Returns count deleted."""
        ...

    async def ensure_collection(self, dimensions: int) -> None:
        """Ensure the collection exists with correct config."""
        ...

    async def health_check(self) -> bool:
        """Check if the vector store is reachable."""
        ...
```

#### `vector_point.py` — VectorPoint (dataclass de dominio usada por VectorStore)

```python
@dataclass(frozen=True)
class VectorPoint:
    id: str  # point_id determinista
    vector: list[float]
    payload: dict[str, str | int]
```

#### `chunking_strategy.py` — ChunkingStrategy Protocol

```python
class ChunkingStrategy(Protocol):
    def chunk(self, text: str) -> list[ChunkResult]:
        """Split text into chunks. Extracts structural metadata from markdown."""
        ...

@dataclass(frozen=True)
class ChunkResult:
    content: str
    token_count: int
    index: int
    start_token: int       # posición del primer token en el texto original
    end_token: int         # posición del último token (exclusivo) en el texto original
    has_overlap: bool      # True si los primeros tokens son overlap del chunk anterior
    forced_split: bool     # True si se forzó un split que rompe una estructura (tabla > hard_max)
    # Metadata estructural extraída del contenido
    section_type: str | None      # "heading", "paragraph", "table", "list", etc.
    section_title: str | None     # heading más cercano al chunk
    page_start: int | None        # página estimada de inicio
    page_end: int | None          # página estimada de fin
    hierarchy: list[str]          # jerarquía de headings ["Section 1", "1.1 Scope"]
```

El chunker analiza el markdown del canónico (producido por Docling) y detecta:
- Headings (`#`, `##`, `###`) → construye jerarquía y section_title
- Tablas → marca section_type como "table"
- Listas → marca section_type como "list"
- Párrafos → marca section_type como "paragraph"
- Marcadores de página (si existen en el markdown) → page_start/page_end

#### `canonical_reader.py` — CanonicalReader Protocol

```python
class CanonicalReader(Protocol):
    async def read_canonical(self, location: str) -> str:
        """Read the canonical text from storage."""
        ...
```

#### `indexing_repository.py` — IndexingRepository Protocol

```python
class IndexingRepository(Protocol):
    async def save_job(self, job: IndexingJob) -> None: ...
    async def find_job_by_id(self, tenant_id: str, job_id: UUID) -> IndexingJob | None: ...
    async def find_job_by_document(
        self, tenant_id: str, document_id: UUID, version_id: UUID
    ) -> IndexingJob | None: ...
    async def save_chunks(self, chunks: list[Chunk]) -> None: ...
    async def delete_chunks_by_document(
        self, tenant_id: str, document_id: UUID, version_id: UUID
    ) -> int: ...
```

#### `unit_of_work.py` — UnitOfWork Protocol

```python
class UnitOfWork(Protocol):
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def save_outbox_event(self, event_type: str, payload: dict[str, Any]) -> None: ...
```

#### `event_publisher.py` — EventPublisher Protocol

```python
class EventPublisher(Protocol):
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None: ...
```

### Políticas (`domain/policies/`)

#### `point_id_policy.py` — PointIdPolicy

- Lógica de generación de point IDs deterministas
- Input: (tenant_id, document_id, version_id, chunk_index)
- Output: UUID5 string
- Namespace fijo para el servicio (constante UUID)
- Garantiza que el mismo chunk siempre produce el mismo point_id

#### `indexing_transition_policy.py` — IndexingTransitionPolicy

- Define transiciones válidas del IndexingJob:
  - PENDING → CHUNKING
  - CHUNKING → EMBEDDING
  - EMBEDDING → STORING
  - STORING → COMPLETED
  - (cualquiera) → FAILED
- Método `can_transition(from_status, to_status) -> bool`

### Excepciones (`domain/exceptions.py`)

```python
class DomainError(Exception): ...
class InvalidStatusTransitionError(DomainError): ...
class InvalidTenantIdError(DomainError): ...
class ChunkingError(DomainError): ...
class EmbeddingError(DomainError): ...
class VectorStoreError(DomainError): ...
class DocumentNotFoundError(DomainError): ...
class CanonicalReadError(DomainError): ...
```

## Pruebas

### `tests/unit/domain/value_objects/`

- TenantId: creación válida, vacío falla, formato inválido falla
- IndexingStatus: valores del enum, transiciones
- ChunkId: generación determinista, mismos inputs = mismo resultado
- PointId: generación determinista, diferentes inputs = diferentes resultados
- EmbeddingModel: validación, dimensions > 0
- ChunkingConfig: invariante overlap < max_tokens
- ContentHash: from_text produce SHA-256 correcto

### `tests/unit/domain/entities/`

- IndexingJob: creación en PENDING, transiciones válidas, transiciones inválidas lanzan error, fail desde cualquier estado
- Chunk: creación con factory method, invariantes (content no vacío, token_count > 0, chunk_index >= 0)

### `tests/unit/domain/policies/`

- PointIdPolicy: determinismo, unicidad, formato UUID válido
- IndexingTransitionPolicy: todas las transiciones válidas/inválidas

### `tests/unit/domain/events/`

- Cada evento: creación, event_type correcto, schema_version

## Criterios de Aceptación

- [ ] Ningún import de infraestructura en `domain/` (no FastAPI, SQLAlchemy, Pydantic, OpenAI, Qdrant, tiktoken, minio, aio-pika)
- [ ] Transiciones de estado protegidas con errores explícitos
- [ ] Point IDs son deterministas (mismo input → mismo output)
- [ ] Chunk IDs son deterministas
- [ ] Puertos definen contratos claros sin acoplamiento a tecnología
- [ ] `uv run pytest tests/unit/domain/ -v` pasa
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
