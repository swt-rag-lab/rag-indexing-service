---
inclusion: always
---

# Architecture Rules — Indexing Service

## Architectural Style

Hexagonal / Clean Architecture. Dependencies always point inward:

```
API / Consumers (input adapters)
        ↓
   Application (use cases)
        ↓
      Domain (entities, ports, policies)
        ↑
Infrastructure (output adapters)
```

## Layer Rules

### Domain (`domain/`)

Contains: entities (`IndexingJob`, `Chunk`), value objects (`IndexingStatus`, `ChunkId`, `EmbeddingModel`, `TenantId`), domain events, ports (interfaces), policies, exceptions.

Constraints:
- MUST NOT import or depend on FastAPI, SQLAlchemy, MinIO, aio-pika, OpenAI, Qdrant, tiktoken, or Pydantic.
- MUST NOT access environment variables or perform I/O.
- All external capabilities are expressed as port interfaces defined here.

### Application (`application/use_cases/`)

Contains: use cases that coordinate domain objects and invoke ports.

Constraints:
- Depends only on Domain.
- MUST NOT execute SQL, call SDKs directly, or reference `Request`/`Response` from FastAPI.
- Establishes transactional boundaries via a `UnitOfWork` port.
- Orchestrates: read canonical → chunk → embed → store vectors → persist state.

### Infrastructure (`infrastructure/`)

Contains: adapters implementing domain ports — OpenAI embedder, Qdrant vector store, semantic chunker, MinIO canonical reader, SQLAlchemy repositories, RabbitMQ consumer/publisher, Outbox publisher.

Constraints:
- Depends on Domain (implements its ports). MUST NOT depend on the API layer.
- Provider-specific exceptions MUST be caught and translated into domain exceptions before leaving the adapter boundary.
- Each adapter is independently replaceable without domain changes.

### API / Consumers (`api/`, `infrastructure/messaging/`)

Contains: FastAPI routes (health, indexing status, admin endpoints) and the RabbitMQ consumer — both are input adapters.

Constraints:
- Depends only on Application (use cases and DTOs).
- MUST NOT contain business rules.
- Translates application/domain exceptions to HTTP responses or NACK/DLQ decisions.

### Bootstrap (`bootstrap/`)

Composition root. Wires adapters to ports. May depend on all layers.

## Key Architectural Decisions

1. **Embeddings behind ports** — The domain defines an `Embedder` port. The concrete OpenAI adapter lives exclusively in `infrastructure/embeddings/`. Can be replaced by local models without domain changes.

2. **Vector store behind ports** — The domain defines a `VectorStore` port. Qdrant is the adapter. Search queries go through `retrieval-service`, not through indexing.

3. **Chunking as strategy** — The domain defines a `ChunkingStrategy` port. Concrete implementations (semantic, fixed-size, etc.) live in `infrastructure/chunking/`.

4. **Transactional Outbox** — Events are persisted in the `outbox_events` table within the same DB transaction as state changes, then published asynchronously.

5. **Multi-tenancy** — Every entity, query, and vector payload MUST be scoped to a `tenant_id`. Qdrant payloads include tenant_id for filtering.

6. **Idempotent consumers** — The RabbitMQ consumer MUST handle duplicate `document.ready_for_indexing.v1` events without producing duplicate vectors.

7. **Deterministic point IDs** — Qdrant point IDs are deterministic based on (tenant_id, document_id, version_id, chunk_index) to ensure idempotent upserts.

8. **Event immutability** — Published events are versioned and never mutated after creation.

## Dependency Direction Quick Reference

| From → To | Allowed? |
|---|---|
| Domain → anything external | NO |
| Application → Domain | YES |
| Application → Infrastructure | NO |
| Infrastructure → Domain (ports) | YES |
| Infrastructure → API | NO |
| API → Application | YES |
| API → Domain directly | NO |
| Bootstrap → all layers | YES |

## Non-Negotiable Rules

1. Dependencies always point inward.
2. Domain is independent of all frameworks and vendor SDKs.
3. OpenAI and Qdrant are hidden behind replaceable port interfaces.
4. This service owns its data exclusively — no shared DB access.
5. Multi-tenancy is mandatory on every resource and vector payload.
6. Events are immutable, versioned, and published via Transactional Outbox.
7. Consumers are idempotent.
8. Only this service writes to Qdrant.
