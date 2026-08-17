# Stack Tecnológico de Indexing Service

**Proyecto:** RAG Lab  
**Servicio:** `indexing-service`  
**Tipo:** Kiro Steering  
**Estado:** Activo  
**Versión:** 1.0  
**Última actualización:** 2026-08-15

## Línea base

| Área | Tecnología | Estado |
|---|---|---|
| Lenguaje | Python 3.12+ | Obligatorio |
| Gestión | `uv` | Obligatorio |
| API HTTP | FastAPI | Obligatorio |
| Servidor ASGI | Uvicorn | Obligatorio |
| Validación | Pydantic | Obligatorio |
| Configuración | pydantic-settings | Obligatorio |
| Base de datos | PostgreSQL | Obligatorio |
| ORM | SQLAlchemy Async | Obligatorio |
| Driver | asyncpg | Obligatorio |
| Migraciones | Alembic | Obligatorio |
| Object Storage | MinIO (lectura) | Obligatorio |
| Vector Store | Qdrant | Obligatorio |
| Cliente Qdrant | qdrant-client | Obligatorio |
| Embeddings | OpenAI | Obligatorio |
| Cliente OpenAI | openai | Obligatorio |
| Chunking | semchunk / custom | Obligatorio |
| Tokenizer | tiktoken | Obligatorio |
| Broker | RabbitMQ | Obligatorio |
| Cliente RabbitMQ | aio-pika | Obligatorio |
| Logging | structlog | Obligatorio |
| Pruebas | pytest, pytest-asyncio, httpx, pytest-cov | Obligatorio |
| Calidad | Ruff, mypy | Obligatorio |

## Dependencias de ejecución

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
structlog
sqlalchemy[asyncio]
alembic
asyncpg
minio
aio-pika
tenacity
openai
qdrant-client
tiktoken
semchunk
```

## Dependencias de desarrollo

```text
pytest
pytest-asyncio
pytest-cov
httpx
ruff
mypy
```

## Embeddings

### OpenAI

Proveedor de embeddings configurado. Se usa via un puerto/adaptador para ser reemplazable.

- Modelo default: `text-embedding-3-small`
- Dimensiones: 1536
- Batch size configurable

Solo se usa dentro de `infrastructure/embeddings/openai_embedder.py`.

## Chunking

### Estrategia

- Chunking semántico basado en tokens
- Tamaño de chunk configurable (default: 512 tokens)
- Overlap configurable (default: 50 tokens)
- Tokenizer: tiktoken (modelo cl100k_base)

Solo se usa dentro de `infrastructure/chunking/`.

## Qdrant

- Almacena vectores con payloads de metadata
- Colecciones por tenant o globales con filtro de tenant
- Cada punto incluye: tenant_id, document_id, version_id, chunk_id
- Solo este servicio escribe en Qdrant

## Tecnologías prohibidas

```text
docling
pymupdf
langchain
langgraph
sentence-transformers
```

## RabbitMQ

- Consume de: exchange `rag.documents.events`, routing key `document.ready_for_indexing.v1`
- Publica en: exchange `rag.documents.events`, routing keys de indexación
- Garantía: at-least-once, consumidores idempotentes
- Patrón: Transactional Outbox para publicación

## PostgreSQL

Base de datos propia: `indexing`

Almacena:
- indexing_jobs
- chunks (metadata, no el vector)
- outbox_events

## MinIO

- Lee documentos canónicos del bucket `processed-documents` (solo lectura)
- NO escribe en MinIO

## Puerto local

```text
8003  Indexing Service
```

## Reglas no negociables

1. OpenAI y Qdrant solo en Infraestructura (adaptadores).
2. Dominio no importa SDKs de embeddings ni vector store.
3. PostgreSQL almacena estado; Qdrant almacena vectores.
4. Publicación confiable via Transactional Outbox.
5. `uv.lock` es la fuente reproducible.
6. No se agregan dependencias sin necesidad real.
