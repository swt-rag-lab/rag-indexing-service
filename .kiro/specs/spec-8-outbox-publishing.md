# Spec 8 — Outbox + Publicación de Eventos

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 6, Spec 7

## Objetivo

Publicar eventos de indexación de forma confiable usando Transactional Outbox,
siguiendo el mismo patrón ya implementado en ingestion-service y
document-processing-service.

## Entregables

### Outbox Publisher (`infrastructure/messaging/outbox_publisher.py`)

#### `OutboxPublisher`

Background task que poll la tabla `outbox_events` y publica a RabbitMQ:

```python
class OutboxPublisher:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        event_publisher: RabbitMQEventPublisher,
        poll_interval: float = 1.0,
        batch_size: int = 50,
    ) -> None:
        ...

    async def start(self) -> None:
        """Start the polling loop."""
        ...

    async def stop(self) -> None:
        """Stop the polling loop gracefully."""
        ...

    async def _poll_and_publish(self) -> int:
        """Poll pending events, publish, mark as published. Returns count."""
        ...
```

Comportamiento:
1. `SELECT FOR UPDATE SKIP LOCKED` eventos con `status = 'pending'` ordenados por `created_at`
2. Para cada evento:
   - Publicar en RabbitMQ via `RabbitMQEventPublisher`
   - Si éxito → marcar `status = 'published'`, set `published_at`
   - Si fallo transitorio → incrementar `attempts`
   - Si `attempts >= max_attempts` → marcar `status = 'failed'`, guardar error
3. Commit por batch
4. Sleep `poll_interval` si no hay eventos pendientes
5. Loop hasta `stop()` se invoque

`SELECT FOR UPDATE SKIP LOCKED` garantiza que múltiples instancias no procesan
el mismo evento simultáneamente.

### RabbitMQ Event Publisher (`infrastructure/messaging/rabbitmq_event_publisher.py`)

#### `RabbitMQEventPublisher`

Implementa la publicación real a RabbitMQ:

```python
class RabbitMQEventPublisher:
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str,
    ) -> None:
        ...

    async def connect(self) -> None:
        """Establish connection and channel."""
        ...

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish event to exchange with routing_key = event_type.

        Uses publisher confirms. Message is persistent.
        """
        ...

    async def close(self) -> None:
        """Close connection."""
        ...
```

Comportamiento:
- Exchange: `rag.documents.events` (topic, durable)
- Routing key: el `event_type` del evento (e.g., `document.indexed.v1`)
- Message properties:
  - `delivery_mode = 2` (persistent)
  - `content_type = "application/json"`
  - `message_id = event_id` (UUID del outbox event)
  - `timestamp`
- Publisher confirms habilitado (mandatory delivery)
- Serialización: `json.dumps(payload)`

### Eventos publicados

#### `document.indexing.started.v1`

```json
{
  "tenant_id": "tenant-01",
  "document_id": "uuid",
  "version_id": "uuid",
  "job_id": "uuid",
  "correlation_id": "uuid",
  "occurred_at": "2026-08-17T12:00:00Z",
  "schema_version": "1"
}
```

Routing key: `document.indexing.started.v1`

#### `document.indexed.v1`

```json
{
  "tenant_id": "tenant-01",
  "document_id": "uuid",
  "version_id": "uuid",
  "job_id": "uuid",
  "total_chunks": 12,
  "embedding_model": "text-embedding-3-small",
  "chunking_version": "semantic-v1",
  "correlation_id": "uuid",
  "occurred_at": "2026-08-17T12:00:05Z",
  "schema_version": "1"
}
```

Routing key: `document.indexed.v1`

#### `document.indexing.failed.v1`

```json
{
  "tenant_id": "tenant-01",
  "document_id": "uuid",
  "version_id": "uuid",
  "job_id": "uuid",
  "reason": "Embedding generation failed: rate limit exceeded",
  "correlation_id": "uuid",
  "occurred_at": "2026-08-17T12:00:03Z",
  "schema_version": "1"
}
```

Routing key: `document.indexing.failed.v1`

### Configuración

| Variable | Default | Descripción |
|---|---|---|
| OUTBOX_POLL_INTERVAL | 1.0 | Segundos entre polls |
| OUTBOX_BATCH_SIZE | 50 | Eventos por poll |
| OUTBOX_MAX_ATTEMPTS | 5 | Reintentos antes de marcar failed |

### Integración en lifecycle

- `OutboxPublisher` se inicia como `asyncio.Task` en startup (después del consumer)
- Se detiene con graceful shutdown (terminar batch actual, luego parar)
- `RabbitMQEventPublisher` comparte conexión o crea la propia

### Fakes (`tests/fakes/fake_event_publisher.py`)

#### `FakeEventPublisher`

```python
class FakeEventPublisher:
    def __init__(self, should_fail: bool = False) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []
        self._should_fail = should_fail

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._should_fail:
            raise ConnectionError("Fake publish failure")
        self.published.append((event_type, payload))
```

## Pruebas

### Tests de integración (`tests/integration/messaging/`)

#### `test_outbox_publisher.py`

- Outbox event guardado en transacción → publicado en RabbitMQ
- Rollback de transacción → evento NO queda en outbox
- Publisher marca como `published` con `published_at` tras confirmación
- Evento con fallo transitorio → `attempts` incrementado, sigue como `pending`
- Evento con `attempts >= max_attempts` → marcado `failed`
- Múltiples eventos pendientes → procesados en orden (FIFO)
- `SELECT FOR UPDATE SKIP LOCKED` no procesa eventos ya tomados

#### `test_rabbitmq_event_publisher.py`

- Publica evento en exchange con routing key correcto
- Mensaje tiene properties correctas (persistent, content_type, message_id)
- Payload es JSON válido
- Publisher confirms: si exchange no existe → error
- Reconexión tras fallo de conexión

### Tests de aplicación (extender `test_index_document.py`)

- Use case éxito → outbox event `document.indexing.started.v1` con payload correcto
- Use case éxito → outbox event `document.indexed.v1` con payload correcto
- Use case fallo → outbox event `document.indexing.failed.v1` con payload correcto
- Payloads contienen todos los campos requeridos
- `schema_version` siempre es "1"

## Criterios de Aceptación

- [ ] Outbox publisher lee eventos pendientes y publica en RabbitMQ
- [ ] Eventos marcados `published` solo tras confirmación del broker
- [ ] Eventos con max_attempts superado marcados como `failed`
- [ ] `SELECT FOR UPDATE SKIP LOCKED` previene procesamiento duplicado
- [ ] `document.indexing.started.v1` publicado al iniciar indexación
- [ ] `document.indexed.v1` publicado tras indexación exitosa
- [ ] `document.indexing.failed.v1` publicado tras fallo
- [ ] Mensajes son persistentes con publisher confirms
- [ ] Routing keys correctos para cada tipo de evento
- [ ] Integrado en lifecycle (startup/shutdown)
- [ ] Tests de integración pasan contra RabbitMQ + PostgreSQL
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
