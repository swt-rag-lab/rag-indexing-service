# Límites de Indexing Service

**Proyecto:** RAG Lab  
**Servicio:** `indexing-service`  
**Tipo:** Kiro Steering  
**Estado:** Activo  
**Versión:** 1.0  
**Última actualización:** 2026-08-15

## Propósito

Convertir documentos canónicos en unidades recuperables (chunks + embeddings)
y mantener su representación en el índice vectorial (Qdrant).

## Responsabilidad principal

La responsabilidad comienza cuando recibe un evento `DocumentReadyForIndexing.v1`
indicando que existe un documento canónico procesado y listo para indexación.

La responsabilidad termina cuando los vectores han sido almacenados en Qdrant
y se ha producido un evento `DocumentIndexed.v1`.

## Capacidades permitidas

Indexing Service PUEDE:

- leer documentos canónicos desde MinIO (bucket `processed-documents`);
- aplicar estrategias versionadas de chunking sobre el texto canónico;
- generar embeddings con OpenAI (u otro proveedor configurado);
- insertar, actualizar y retirar vectores en Qdrant idempotentemente;
- construir payloads de trazabilidad (tenant_id, document_id, version_id, chunk_id);
- mantener estado de indexación (IndexingJob);
- mantener metadata de chunks en PostgreSQL;
- validar dimensiones, modelo y compatibilidad del embedding;
- crear y administrar colecciones en Qdrant;
- publicar eventos de integración mediante Transactional Outbox;
- consultar el estado de indexación via API;
- aplicar aislamiento por tenant en vectores (payload filter);
- permitir reindexación idempotente;
- producir logs, métricas y trazas.

## Capacidades prohibidas

Indexing Service NO DEBE:

- aceptar cargas de archivos directamente de usuarios;
- extraer texto de PDFs, DOCX u otros formatos (eso lo hace document-processing);
- decidir identidad, numeración de versiones ni validar archivos;
- ejecutar consultas de usuario como capacidad pública de retrieval;
- generar respuestas con LLMs;
- administrar usuarios, roles o credenciales;
- acceder directamente a las bases de datos de otros servicios;
- escribir en MinIO;
- usar Docling, PyMuPDF ni cualquier extractor de documentos.

## Flujo de procesamiento

```text
DocumentReadyForIndexing.v1
        ↓
  Read canonical from MinIO
        ↓
  Chunk text (semantic chunking)
        ↓
  Generate embeddings (OpenAI)
        ↓
  Upsert vectors to Qdrant
        ↓
  Persist IndexingJob + Chunks metadata
        ↓
  Publish DocumentIndexed.v1
```

## Ciclo de vida del IndexingJob

```text
PENDING → CHUNKING → EMBEDDING → STORING → COMPLETED
                                           ↓
                                        FAILED
```

## Eventos que consume

- `document.ready_for_indexing.v1` — dispara la indexación
- (futuro) `document.deletion_requested.v1` — desindexación

## Eventos que publica

- `document.indexing.started.v1`
- `document.indexed.v1`
- `document.indexing.failed.v1`

## Propiedad de datos

Indexing Service es propietario de:

- IndexingJob (estado y tracking de la indexación)
- Chunk (metadata: posición, tokens, hash)
- Vectores en Qdrant (puntos con payloads)
- Manifiestos de indexación (versiones de chunking + embedding)
- Outbox events propios

NO es propietario de:

- Documentos originales (pertenecen a ingestion-service)
- Documentos canónicos (pertenecen a document-processing-service)
- Resultados de búsqueda (pertenecen a retrieval-service)

## Persistencia

### PostgreSQL

Base de datos propia: `indexing`

- `indexing_jobs` — tracking de la indexación
- `chunks` — metadata de cada chunk (no el texto completo)
- `outbox_events` — publicación confiable de eventos

### Qdrant

- Colección: `documents` (o por tenant según estrategia)
- Cada punto incluye:
  - vector: embedding del chunk
  - payload: `tenant_id`, `document_id`, `version_id`, `chunk_index`, `chunk_hash`, `embedding_model`, `chunking_version`
- Point ID: determinista basado en (document_id, version_id, chunk_index)

### MinIO

- Lee canónicos del bucket `processed-documents` (solo lectura)

## Dependencias permitidas

- Qdrant (vector store)
- OpenAI (embeddings)
- PostgreSQL propio
- MinIO (lectura de canónicos)
- RabbitMQ (consumir y publicar eventos)
- structlog, OpenTelemetry

## Dependencias prohibidas

- docling
- pymupdf
- langchain
- langgraph
- sentence-transformers

## Multi-tenancy

Todo vector en Qdrant incluye `tenant_id` en su payload.
Las búsquedas (via retrieval-service) SIEMPRE filtran por tenant_id.
No hay acceso cross-tenant a vectores.

## Idempotencia

- Point IDs deterministas previenen duplicados en Qdrant
- Si ya existe un IndexingJob COMPLETED para (document_id, version_id):
  - Se eliminan puntos anteriores de esa versión
  - Se reindexa (upsert)
- Mensajes duplicados no producen vectores duplicados

## Reglas no negociables

1. El servicio indexa documentos canónicos, no los extrae ni los recibe.
2. Un chunk indexado conserva trazabilidad hasta el documento original.
3. OpenAI y Qdrant están detrás de puertos/adaptadores.
4. Los vectores contienen metadata suficiente para filtrado por tenant.
5. Los Point IDs son deterministas o protegidos por idempotencia.
6. Solo este servicio modifica colecciones y puntos en Qdrant.
7. Todo procesamiento pertenece a un tenant.
8. Los eventos contienen referencias, no contenido completo.
