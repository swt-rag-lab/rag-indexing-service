# Spec 6 — Caso de Uso: IndexDocumentUseCase

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 1, Spec 2, Spec 3, Spec 4, Spec 5

## Objetivo

Implementar el caso de uso principal que orquesta la indexación completa de un
documento: lee el canónico, lo divide en chunks, genera embeddings, almacena
vectores en Qdrant, persiste metadata y publica eventos.

## Entregables

### Application Layer

#### `application/commands/index_document.py` — IndexDocumentCommand

```python
@dataclass(frozen=True)
class IndexDocumentCommand:
    tenant_id: str
    document_id: UUID
    version_id: UUID
    canonical_location: str
    content_hash: str
    content_type: str
    correlation_id: str
    # Metadata de origen para trazabilidad end-to-end
    extractor_type: str       # qué extractor produjo el canónico (docling, pymupdf, plain_text)
    extractor_version: str    # versión del extractor
    page_count: int           # páginas del documento original
    word_count: int           # palabras en el canónico
```

Origen: deserializado del evento `document.ready_for_indexing.v1` que incluye
toda esta metadata. Se propaga a cada chunk para trazabilidad completa.

#### `application/use_cases/index_document.py` — IndexDocumentUseCase

Flujo principal:

```text
1. Verificar idempotencia
   - Si existe IndexingJob COMPLETED para (tenant, doc, version) → reindexar
   - Eliminar chunks previos de PostgreSQL
   - Eliminar puntos previos de Qdrant

2. Crear IndexingJob en PENDING
   - Guardar outbox event: document.indexing.started.v1

3. Transicionar a CHUNKING
   - Leer texto canónico de MinIO (CanonicalReader)
   - Aplicar ChunkingStrategy → list[ChunkResult] (con start_token, end_token, has_overlap)
   - Crear entidades Chunk con:
     - IDs deterministas (chunk_id, point_id)
     - Posición (start_token, end_token, has_overlap)
     - Metadata de origen propagada desde el command:
       - source_content_type ← command.content_type
       - source_content_hash ← command.content_hash
       - extractor_type ← command.extractor_type
       - extractor_version ← command.extractor_version
       - embedding_model ← settings.embedding_model
       - chunking_version ← settings.chunking_version

4. Transicionar a EMBEDDING
   - Preparar textos para embedding con **context prepend**:
     - Para cada chunk, construir texto enriquecido:
       `f"Section: {' > '.join(chunk.hierarchy)}\n\n{chunk.content}"`
     - Si hierarchy está vacía, usar solo el content
     - Esto mejora la calidad del retrieval al darle al vector
       contexto de qué sección del documento pertenece
     - IMPORTANTE: el `content` almacenado en PostgreSQL sigue siendo
       el chunk puro (sin prepend). El prepend es SOLO para el embedding.
   - Llamar Embedder.embed_batch(enriched_texts) → vectores
   - Validar dimensiones de vectores

5. Transicionar a STORING
   - Construir VectorPoints (point_id, vector, payload con TODA la metadata)
   - Payload incluye:
     - Identificación: tenant_id, document_id, version_id, chunk_index
     - Integridad: chunk_hash, token_count
     - Posición: start_token, end_token, has_overlap, forced_split
     - Origen: source_content_type, source_content_hash,
       extractor_type, extractor_version
     - Pipeline: embedding_model, chunking_version
     - Estructural: section_type, section_title, page_start, page_end, hierarchy
   - Llamar VectorStore.upsert_points(points)

6. Completar
   - Persistir IndexingJob como COMPLETED
   - Persistir Chunks metadata en PostgreSQL (con toda la metadata)
   - Guardar outbox event: document.indexed.v1
   - Commit via UnitOfWork

En caso de error en cualquier paso:
   - Marcar IndexingJob como FAILED con razón
   - Guardar outbox event: document.indexing.failed.v1
   - Commit via UnitOfWork (persistir el fallo)
   - NO hacer retry aquí (el consumer decide retry)
```

Dependencias inyectadas:
- `CanonicalReader`
- `ChunkingStrategy`
- `Embedder`
- `VectorStore`
- `IndexingRepository`
- `UnitOfWork`

```python
class IndexDocumentUseCase:
    def __init__(
        self,
        canonical_reader: CanonicalReader,
        chunking_strategy: ChunkingStrategy,
        embedder: Embedder,
        vector_store: VectorStore,
        repository: IndexingRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        ...

    async def execute(self, command: IndexDocumentCommand) -> IndexingResult:
        ...
```

#### `application/dto/indexing_result.py` — IndexingResult

```python
@dataclass(frozen=True)
class IndexingResult:
    job_id: UUID
    tenant_id: str
    document_id: UUID
    version_id: UUID
    status: str
    total_chunks: int
    embedding_model: str
    chunking_version: str
```

#### `application/exceptions.py`

- `ApplicationError` — base
- `IndexingFailedError` — error durante indexación
- `DocumentNotAccessibleError` — no se pudo leer canónico
- `IdempotencyConflictError` — conflicto no resuelto

### API (consulta de estado)

#### `api/routes/indexing.py`

- `GET /api/v1/indexing/jobs/{job_id}` — estado de un IndexingJob
  - Requiere header `X-Tenant-ID`
  - Respuesta: job_id, status, total_chunks, processed_chunks, embedding_model, error_message, created_at, updated_at
  - 404 si no existe o es de otro tenant

- `GET /api/v1/indexing/jobs?document_id={uuid}&version_id={uuid}` — buscar job por documento
  - Requiere header `X-Tenant-ID`
  - Respuesta: mismo formato que arriba

#### `api/schemas/indexing.py`

- Pydantic response models para los endpoints

### Bootstrap

- Wiring completo en `bootstrap/container.py`:
  - Instanciar CanonicalReader (MinioCanonicalReader)
  - Instanciar ChunkingStrategy (SemanticChunker con config)
  - Instanciar Embedder (OpenAIEmbedder con settings)
  - Instanciar VectorStore (QdrantVectorStore)
  - Factory method para crear UseCase con todas las dependencias

### Storage Adapter (`infrastructure/storage/minio_canonical_reader.py`)

#### `MinioCanonicalReader`

Implementa `CanonicalReader`:

```python
class MinioCanonicalReader:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False) -> None:
        ...

    async def read_canonical(self, location: str) -> str:
        """Read canonical text from MinIO. Location is the object key."""
        ...
```

- Lee del bucket `processed-documents`
- Decodifica como UTF-8
- Errores de MinIO → `CanonicalReadError`

### Fake

#### `tests/fakes/fake_canonical_reader.py`

- Dict en memoria: `{location: text_content}`
- `read_canonical(location)` → retorna texto o `CanonicalReadError`

## Pruebas

### Tests de aplicación (`tests/application/use_cases/`)

#### `test_index_document.py`

Todos con fakes (FakeCanonicalReader, FakeChunkingStrategy, FakeEmbedder, FakeVectorStore, FakeIndexingRepository, FakeUnitOfWork):

**Flujo feliz:**
- Documento se indexa completamente → job COMPLETED
- Chunks guardados en repositorio con metadata correcta
- Vectores guardados en VectorStore con payloads correctos
- Outbox event `document.indexing.started.v1` con payload correcto
- Outbox event `document.indexed.v1` con payload correcto
- UoW committed
- IndexingResult retornado con datos correctos

**Idempotencia (reindexación):**
- Job COMPLETED previo existe → chunks previos eliminados de PostgreSQL
- Puntos previos eliminados de Qdrant
- Nueva indexación se ejecuta normalmente
- Nuevo job COMPLETED al final

**Errores:**
- CanonicalReader falla → job FAILED, outbox event de fallo, UoW committed
- ChunkingStrategy falla → job FAILED con razón "chunking failed"
- Embedder falla → job FAILED con razón "embedding failed"
- VectorStore falla → job FAILED con razón "vector store failed"
- UoW commit falla → excepción propagada (no se puede guardar estado)

**Point IDs:**
- Verificar que los point_ids en VectorStore son deterministas
- Mismo documento reindexado produce mismos point_ids

**Batch embedding:**
- 50 chunks → una llamada a embed_batch con 50 textos
- Orden preservado entre chunks y embeddings

**Context prepend:**
- Chunk con hierarchy ["Section 2", "2.1 Requirements"] → embedding text incluye "Section: Section 2 > 2.1 Requirements\n\n{content}"
- Chunk con hierarchy vacía → embedding text es solo el content
- El content almacenado en PostgreSQL NO tiene prepend
- El vector en Qdrant fue generado con el texto enriquecido

### Tests de API (`tests/api/`)

#### `test_indexing_routes.py`

- GET job existente → 200 con datos correctos
- GET job inexistente → 404
- GET job de otro tenant → 404 (tenant isolation)
- GET por document_id + version_id → 200
- Sin header X-Tenant-ID → 400 o 422

## Criterios de Aceptación

- [ ] Use case orquesta flujo completo: read → chunk → embed → store → persist
- [ ] Idempotencia: reindexación elimina previos y crea nuevos
- [ ] Point IDs deterministas garantizan upsert idempotente en Qdrant
- [ ] Errores en cualquier paso → job FAILED + outbox event de fallo
- [ ] Outbox events correctos para started, indexed y failed
- [ ] API expone estado del job con tenant isolation
- [ ] MinioCanonicalReader implementa el puerto correctamente
- [ ] Tests de aplicación pasan con fakes
- [ ] Tests de API pasan con HTTPX
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
