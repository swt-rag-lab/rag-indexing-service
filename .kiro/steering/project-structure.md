# Estructura del Proyecto de Indexing Service

**Proyecto:** RAG Lab  
**Servicio:** `indexing-service`  
**Tipo:** Kiro Steering  
**Estado:** Activo  
**Versión:** 1.0  
**Última actualización:** 2026-08-15

## Paquete importable

```text
src/indexing_service/
```

No se debe utilizar un paquete genérico `app`.

## Estructura

```text
indexing-service/
├── .kiro/
│   ├── steering/
│   └── specs/
├── src/
│   └── indexing_service/
│       ├── __init__.py
│       ├── domain/
│       │   ├── entities/
│       │   ├── value_objects/
│       │   ├── events/
│       │   ├── ports/
│       │   ├── policies/
│       │   └── exceptions.py
│       ├── application/
│       │   ├── commands/
│       │   ├── use_cases/
│       │   ├── dto/
│       │   └── exceptions.py
│       ├── infrastructure/
│       │   ├── persistence/
│       │   │   ├── models/
│       │   │   ├── repositories/
│       │   │   └── mappers/
│       │   ├── embeddings/
│       │   │   └── openai_embedder.py
│       │   ├── vectorstore/
│       │   │   └── qdrant_store.py
│       │   ├── chunking/
│       │   │   └── semantic_chunker.py
│       │   ├── storage/
│       │   │   └── minio_canonical_reader.py
│       │   ├── messaging/
│       │   │   ├── rabbitmq_consumer.py
│       │   │   ├── rabbitmq_event_publisher.py
│       │   │   └── outbox_publisher.py
│       │   └── observability/
│       ├── api/
│       │   ├── routes/
│       │   ├── schemas/
│       │   └── middleware.py
│       ├── bootstrap/
│       │   ├── container.py
│       │   └── lifecycle.py
│       ├── config/
│       │   └── settings.py
│       └── main.py
├── tests/
│   ├── unit/
│   ├── application/
│   ├── integration/
│   └── fakes/
├── migrations/
├── pyproject.toml
└── uv.lock
```

## Convenciones

- Imports absolutos: `from indexing_service.domain.entities...`
- Archivos: `snake_case`
- Clases: `PascalCase`
- Puertos: nombrados por capacidad (`Embedder`, `VectorStore`, `ChunkingStrategy`)
- Adaptadores: incluyen tecnología (`OpenAIEmbedder`, `QdrantVectorStore`, `SemanticChunker`)

## Entry point

```text
indexing_service.main:create_app
```

Ejecución local:

```bash
uv run uvicorn indexing_service.main:create_app --factory --reload --port 8003
```

## Reglas

1. El paquete importable es `indexing_service`.
2. El código de producción vive en `src/indexing_service/`.
3. Tests viven fuera del paquete de producción.
4. No se crean carpetas genéricas sin responsabilidad.
