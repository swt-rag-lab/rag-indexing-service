# Spec 2 — Persistencia PostgreSQL

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 0, Spec 1

## Objetivo

Implementar adaptadores de persistencia con SQLAlchemy Async, Alembic y
migraciones para IndexingJobs, Chunks metadata y Outbox events.

## Entregables

### Base de datos (`infrastructure/persistence/database.py`)

- `create_async_engine` con pool_pre_ping
- `async_sessionmaker` configurado
- Helper para obtener sesiones

### Modelos SQLAlchemy (`infrastructure/persistence/models/`)

#### `indexing_job_model.py` — IndexingJobModel

| Columna | Tipo | Notas |
|---|---|---|
| id | UUID | PK |
| tenant_id | VARCHAR(100) | NOT NULL |
| document_id | UUID | NOT NULL |
| version_id | UUID | NOT NULL |
| status | VARCHAR(20) | NOT NULL, default PENDING |
| total_chunks | INTEGER | NULLABLE |
| processed_chunks | INTEGER | default 0 |
| embedding_model | VARCHAR(100) | NOT NULL |
| chunking_version | VARCHAR(50) | NOT NULL |
| error_message | TEXT | NULLABLE |
| correlation_id | VARCHAR(100) | NOT NULL |
| created_at | TIMESTAMP(TZ) | NOT NULL |
| updated_at | TIMESTAMP(TZ) | NOT NULL |

Índices:
- `ix_indexing_jobs_tenant_id` — (tenant_id)
- `ix_indexing_jobs_document_lookup` — (tenant_id, document_id, version_id) UNIQUE

#### `chunk_model.py` — ChunkModel

| Columna | Tipo | Notas |
|---|---|---|
| id | UUID | PK (chunk_id determinista) |
| tenant_id | VARCHAR(100) | NOT NULL |
| document_id | UUID | NOT NULL |
| version_id | UUID | NOT NULL |
| chunk_index | INTEGER | NOT NULL |
| content | TEXT | NOT NULL |
| token_count | INTEGER | NOT NULL |
| start_token | INTEGER | NOT NULL (posición inicio en doc) |
| end_token | INTEGER | NOT NULL (posición fin en doc) |
| has_overlap | BOOLEAN | NOT NULL, default false |
| content_hash | VARCHAR(64) | NOT NULL (SHA-256 del chunk) |
| point_id | VARCHAR(36) | NOT NULL (UUID del punto en Qdrant) |
| source_content_type | VARCHAR(100) | NOT NULL (content_type original) |
| source_content_hash | VARCHAR(64) | NOT NULL (hash del canónico completo) |
| extractor_type | VARCHAR(50) | NOT NULL (extractor que produjo el canónico) |
| extractor_version | VARCHAR(20) | NOT NULL |
| embedding_model | VARCHAR(100) | NOT NULL |
| chunking_version | VARCHAR(50) | NOT NULL |
| section_type | VARCHAR(50) | NULLABLE (heading, paragraph, table, list, etc.) |
| section_title | VARCHAR(500) | NULLABLE (heading más cercano) |
| page_start | INTEGER | NULLABLE (página de inicio estimada) |
| page_end | INTEGER | NULLABLE (página de fin estimada) |
| hierarchy | JSONB | NOT NULL, default '[]' (jerarquía de headings) |
| created_at | TIMESTAMP(TZ) | NOT NULL |

Índices:
- `ix_chunks_tenant_document` — (tenant_id, document_id, version_id)
- `ix_chunks_point_id` — (point_id) UNIQUE
- `ix_chunks_section_type` — (tenant_id, section_type) — para queries por tipo de sección

#### `outbox_event_model.py` — OutboxEventModel

| Columna | Tipo | Notas |
|---|---|---|
| id | UUID | PK |
| event_type | VARCHAR(200) | NOT NULL |
| payload | JSONB | NOT NULL |
| status | VARCHAR(20) | default 'pending' |
| attempts | INTEGER | default 0 |
| max_attempts | INTEGER | default 5 |
| created_at | TIMESTAMP(TZ) | NOT NULL |
| published_at | TIMESTAMP(TZ) | NULLABLE |
| error_message | TEXT | NULLABLE |

Índices:
- `ix_outbox_events_pending` — (status, created_at) WHERE status = 'pending'

#### `__init__.py` con `Base` declarativo

### Mappers (`infrastructure/persistence/mappers/`)

#### `indexing_job_mapper.py`

- `to_model(entity: IndexingJob) -> IndexingJobModel`
- `to_entity(model: IndexingJobModel) -> IndexingJob`

#### `chunk_mapper.py`

- `to_model(entity: Chunk) -> ChunkModel`
- `to_entity(model: ChunkModel) -> Chunk`
- `to_models(entities: list[Chunk]) -> list[ChunkModel]` (batch)

### Repositorios (`infrastructure/persistence/repositories/`)

#### `sqlalchemy_indexing_repository.py`

Implementa `IndexingRepository`:

- `save_job(job)` — INSERT o UPDATE (upsert por id)
- `find_job_by_id(tenant_id, job_id)` — SELECT con filtro tenant
- `find_job_by_document(tenant_id, document_id, version_id)` — SELECT con filtro compuesto
- `save_chunks(chunks)` — Bulk INSERT
- `delete_chunks_by_document(tenant_id, document_id, version_id)` → DELETE, retorna count

Todas las queries filtran SIEMPRE por `tenant_id`.

### UnitOfWork (`infrastructure/persistence/unit_of_work.py`)

#### `SqlAlchemyUnitOfWork`

- Recibe `async_sessionmaker`
- `async with uow:` → abre sesión
- `commit()` → flush + commit
- `rollback()` → rollback
- `save_outbox_event(event_type, payload)` → INSERT en outbox_events dentro de la misma transacción
- Expone la sesión al repositorio

### Alembic

#### `alembic.ini`

- `script_location = migrations`
- `sqlalchemy.url` desde env var

#### `migrations/env.py`

- Configuración async con asyncpg
- Target metadata desde los modelos

#### Migración inicial

- Tabla `indexing_jobs`
- Tabla `chunks`
- Tabla `outbox_events`
- Todos los índices

### Fakes (`tests/fakes/`)

#### `fake_indexing_repository.py` — FakeIndexingRepository

- Almacena en `dict` en memoria
- Implementa la misma interfaz del puerto
- Filtra por tenant_id

#### `fake_unit_of_work.py` — FakeUnitOfWork

- Lista de outbox events en memoria
- Flags: `committed`, `rolled_back`
- `save_outbox_event` agrega a la lista

## Pruebas

### Tests de integración (`tests/integration/persistence/`)

- `test_indexing_job_repository.py`:
  - Save y find by id
  - Find by document (tenant, doc_id, version_id)
  - Update status
  - Tenant isolation (job de tenant A no visible para tenant B)

- `test_chunk_repository.py`:
  - Bulk save chunks
  - Find by document
  - Delete by document retorna count correcto
  - Tenant isolation

- `test_unit_of_work.py`:
  - Commit persiste job + outbox event en misma transacción
  - Rollback no persiste nada
  - save_outbox_event within transaction

- `test_migrations.py`:
  - `alembic upgrade head` corre sin errores
  - `alembic downgrade -1` revierte

## Criterios de Aceptación

- [ ] `uv run alembic upgrade head` crea las 3 tablas con índices
- [ ] `uv run alembic downgrade -1` revierte limpiamente
- [ ] Repositorio implementa `IndexingRepository` port
- [ ] Toda query filtra por tenant_id (tenant isolation)
- [ ] UoW persiste estado + outbox event atómicamente
- [ ] Bulk insert de chunks funciona eficientemente
- [ ] Tests de integración pasan contra PostgreSQL
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
