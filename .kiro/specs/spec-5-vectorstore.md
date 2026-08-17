# Spec 5 — Vector Store: Qdrant Adapter

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 1

## Objetivo

Implementar el adaptador de almacenamiento vectorial que cumple el puerto
`VectorStore`. Usa `qdrant-client` para interactuar con Qdrant.

## Entregables

### Adaptador (`infrastructure/vectorstore/qdrant_store.py`)

#### `QdrantVectorStore`

Implementa `VectorStore`:

```python
class QdrantVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
        collection_name: str = "documents",
    ) -> None:
        ...

    async def upsert_points(self, points: list[VectorPoint]) -> None:
        """Upsert points to Qdrant. Idempotent via deterministic point IDs."""
        ...

    async def delete_points_by_document(
        self,
        tenant_id: str,
        document_id: str,
        version_id: str,
    ) -> int:
        """Delete all points matching tenant + document + version. Returns count."""
        ...

    async def ensure_collection(self, dimensions: int) -> None:
        """Create collection if not exists. Verify dimensions if exists."""
        ...

    async def health_check(self) -> bool:
        """Check Qdrant connectivity."""
        ...

    async def close(self) -> None:
        """Close the client connection."""
        ...
```

Comportamiento:

**`upsert_points`**:
- Convierte `list[VectorPoint]` a `qdrant_client.models.PointStruct`
- Point ID: usa el `point_id` determinista (UUID string) del VectorPoint
- Vector: embedding float list
- Payload: dict con metadata (tenant_id, document_id, version_id, chunk_index, chunk_hash, embedding_model, chunking_version)
- Batch upsert (el cliente maneja el batching interno)
- Idempotente: upsert con mismo point_id reemplaza el punto existente

**`delete_points_by_document`**:
- Usa filter por payload: `tenant_id` AND `document_id` AND `version_id`
- Scroll para contar puntos antes de delete (o usa count API)
- Delete con filter
- Retorna cantidad de puntos eliminados

**`ensure_collection`**:
- Check si existe la colección
- Si no existe: crear con `vectors_config` (dimensions, distance=Cosine)
- Si existe: verificar que dimensions coincida, warning si no
- Crear payload indexes para:
  - `tenant_id` (keyword) — multi-tenancy
  - `document_id` (keyword) — delete/reindex
  - `version_id` (keyword) — delete por versión
  - `embedding_model` (keyword) — identificar modelo obsoleto
  - `chunking_version` (keyword) — identificar chunking obsoleto
  - `section_type` (keyword) — filtrado por sección en retrieval
  - `page_start` (integer) — filtrado por rango de páginas

**`health_check`**:
- Llama a `/readyz` o usa `client.get_collections()` como probe
- Retorna True/False

Manejo de errores:
- Errores de conexión → `VectorStoreError`
- Errores de Qdrant API → `VectorStoreError` con mensaje descriptivo
- Timeout → retry con tenacity (max 3 intentos)
- Collection not found en upsert → `VectorStoreError`

### `infrastructure/vectorstore/__init__.py`

Export de `QdrantVectorStore`.

### Configuración

Reutiliza settings de Spec 0:
- `QDRANT_HOST` (default: localhost)
- `QDRANT_PORT` (default: 6333)
- `QDRANT_API_KEY` (opcional)
- `QDRANT_COLLECTION` (default: documents)

### Payloads en Qdrant

Cada punto almacenado tiene este payload con metadata completa de trazabilidad:

```json
{
  "tenant_id": "tenant-01",
  "document_id": "uuid-string",
  "version_id": "uuid-string",
  "chunk_index": 0,
  "chunk_hash": "sha256hex",
  "token_count": 987,
  "start_token": 0,
  "end_token": 987,
  "has_overlap": false,
  "source_content_type": "application/pdf",
  "source_content_hash": "sha256hex-del-canonico-completo",
  "extractor_type": "docling",
  "extractor_version": "1.0",
  "embedding_model": "text-embedding-3-small",
  "chunking_version": "semantic-v1",
  "section_type": "requirements",
  "section_title": "2.1 Technical Requirements",
  "page_start": 5,
  "page_end": 6,
  "hierarchy": ["2. Technical Requirements", "2.1 Technical Requirements"]
}
```

Este payload permite:
- **Multi-tenancy**: filtrar por `tenant_id` en retrieval
- **Reindexación**: identificar y eliminar puntos por `document_id` + `version_id`
- **Trazabilidad end-to-end**: desde un chunk encontrado en retrieval, trazar hasta el documento original, saber qué extractor lo procesó, con qué modelo de embedding y versión de chunking
- **Filtrado por sección**: el retrieval-service puede filtrar por `section_type` (e.g., "solo buscar en requisitos técnicos")
- **Contexto para el usuario**: mostrar de qué sección y página viene un resultado
- **Ponderación en retrieval**: dar más peso a chunks de secciones específicas según la query
- **Debugging**: saber si un chunk tiene overlap, cuántos tokens tiene, y su posición en el documento
- **Versionado**: si se cambia el modelo de embedding o la estrategia de chunking, se puede identificar qué puntos necesitan reindexación

Los payload indexes permiten filtrado eficiente por:
- `tenant_id` (keyword index) — para multi-tenancy
- `document_id` (keyword index) — para delete/reindex por documento
- `version_id` (keyword index) — para delete por versión específica
- `embedding_model` (keyword index) — para identificar puntos con modelo obsoleto
- `chunking_version` (keyword index) — para identificar puntos con chunking obsoleto
- `section_type` (keyword index) — para filtrar por tipo de sección en retrieval
- `page_start` (integer index) — para filtrar por rango de páginas

### Fakes (`tests/fakes/fake_vector_store.py`)

#### `FakeVectorStore`

- Almacena puntos en `dict[str, VectorPoint]` (key = point_id)
- `upsert_points` → agrega/reemplaza en dict
- `delete_points_by_document` → filtra y elimina del dict, retorna count
- `ensure_collection` → no-op (siempre exitoso)
- `health_check` → True
- Helpers para inspección en tests:
  - `get_all_points() -> list[VectorPoint]`
  - `get_points_by_tenant(tenant_id) -> list[VectorPoint]`
  - `count() -> int`

## Pruebas

### Tests unitarios (`tests/unit/infrastructure/vectorstore/`)

#### `test_qdrant_store.py` (con mock del client)

- `upsert_points` llama al client con PointStructs correctos
- `delete_points_by_document` construye filter correcto
- `ensure_collection` crea colección con config correcta
- `health_check` retorna True si client responde
- Errores del client se traducen en `VectorStoreError`

### Tests de integración (`tests/integration/vectorstore/`)

#### `test_qdrant_store_integration.py` (requiere Qdrant corriendo)

- Ensure collection crea la colección
- Upsert 5 puntos → consultables en Qdrant
- Upsert idempotente: mismo point_id actualiza, no duplica
- Delete by document: elimina solo los puntos del documento/versión
- Delete no afecta puntos de otro tenant
- Delete no afecta puntos de otro documento
- Health check contra Qdrant real → True

### Tests del fake

- FakeVectorStore: upsert, delete, idempotencia, tenant isolation

## Criterios de Aceptación

- [ ] `QdrantVectorStore` implementa el puerto `VectorStore`
- [ ] Upsert es idempotente (mismos point_ids no duplican)
- [ ] Delete filtra correctamente por tenant + document + version
- [ ] Payload indexes creados para filtrado eficiente
- [ ] Errores del SDK traducidos en `VectorStoreError`
- [ ] Collection se crea con dimensiones y distancia correctas
- [ ] `FakeVectorStore` disponible con helpers de inspección
- [ ] Tests unitarios (mock) pasan
- [ ] Tests de integración pasan contra Qdrant local
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
