# Spec 7 — Consumidor RabbitMQ

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** Spec 6

## Objetivo

Implementar el consumidor que escucha `document.ready_for_indexing.v1` desde
RabbitMQ y lanza la indexación del documento vía `IndexDocumentUseCase`.

## Entregables

### Consumer (`infrastructure/messaging/rabbitmq_consumer.py`)

#### `RabbitMQConsumer`

```python
class RabbitMQConsumer:
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str,
        queue_name: str,
        routing_key: str,
        prefetch_count: int,
        use_case_factory: Callable[[], IndexDocumentUseCase],
    ) -> None:
        ...

    async def start(self) -> None:
        """Connect and start consuming messages."""
        ...

    async def stop(self) -> None:
        """Stop consuming and close connection gracefully."""
        ...

    async def _handle_message(self, message: AbstractIncomingMessage) -> None:
        """Process a single message."""
        ...
```

Comportamiento por mensaje:

1. **Deserializar** payload JSON del body
2. **Validar** campos requeridos:
   - `tenant_id` (str, no vacío)
   - `document_id` (UUID válido)
   - `version_id` (UUID válido)
   - `canonical_location` (str, no vacío)
   - `content_hash` (str)
   - `content_type` (str)
   - `extractor_type` (str)
   - `extractor_version` (str)
   - `page_count` (int)
   - `word_count` (int)
   - `correlation_id` (str, usar message_id si no viene)
3. **Crear** `IndexDocumentCommand` mapeando todos los campos del evento:
   - tenant_id ← payload.tenant_id
   - document_id ← UUID(payload.document_id)
   - version_id ← UUID(payload.version_id)
   - canonical_location ← payload.canonical_location
   - content_hash ← payload.content_hash
   - content_type ← payload.content_type
   - extractor_type ← payload.extractor_type
   - extractor_version ← payload.extractor_version
   - page_count ← payload.page_count
   - word_count ← payload.word_count
   - correlation_id ← payload.correlation_id
4. **Ejecutar** `IndexDocumentUseCase.execute(command)`
5. **ACK** si éxito (use case retorna resultado)
6. **ACK** si el use case marca FAILED (fallo de negocio persistido, no reintentar)
7. **NACK + requeue** si fallo transitorio (conexión, timeout) Y `delivery_count < max_retries`
8. **NACK + no requeue** (→ DLQ) si:
   - Fallo permanente (payload inválido, validación)
   - Max reintentos superados

### Configuración

| Variable | Default | Descripción |
|---|---|---|
| RABBITMQ_CONSUMER_QUEUE | indexing.document.ready_for_indexing | Nombre de la cola |
| RABBITMQ_CONSUMER_ROUTING_KEY | document.ready_for_indexing.v1 | Routing key |
| RABBITMQ_PREFETCH_COUNT | 5 | Prefetch para backpressure |
| RABBITMQ_MAX_RETRIES | 3 | Reintentos antes de DLQ |

### Declaraciones en startup

Al iniciar, el consumer declara:
- Queue: `indexing.document.ready_for_indexing` (durable)
- Binding: exchange `rag.documents.events` → queue con routing key `document.ready_for_indexing.v1`
- Arguments: `x-dead-letter-exchange: rag.documents.events.dlx`

### Integración en lifecycle (`bootstrap/lifecycle.py`)

- Consumer se inicia como `asyncio.Task` en startup
- Se detiene con graceful shutdown (await pending messages, then close)
- Si el consumer se desconecta, intenta reconexión con backoff

### Logging

Cada mensaje procesado log con:
- `tenant_id`
- `document_id`
- `version_id`
- `correlation_id`
- `delivery_tag`
- Resultado: `acked`, `nacked_requeue`, `nacked_dlq`

### Idempotencia

El consumer no implementa idempotencia propia — delega al use case.
El `IndexDocumentUseCase` ya maneja reindexación idempotente si el job
existe como COMPLETED.

Si un job está en progreso (PENDING/CHUNKING/EMBEDDING/STORING):
- Log warning
- ACK el mensaje (evitar procesamiento paralelo del mismo documento)
- Alternativa: NACK + requeue con delay (si se quiere retry después)

### Fakes

#### `tests/fakes/fake_message_consumer.py`

- Simula consumo de mensajes sin RabbitMQ
- Acepta mensajes via `inject_message(payload: dict)`
- Ejecuta handler y permite verificar resultado

## Pruebas

### Tests unitarios (`tests/unit/infrastructure/messaging/`)

#### `test_consumer_message_handling.py`

- Payload válido → crea command correcto
- Payload sin tenant_id → NACK (permanente)
- Payload con document_id inválido (no UUID) → NACK (permanente)
- Payload sin canonical_location → NACK (permanente)
- JSON inválido (no parseable) → NACK (permanente)
- correlation_id extraído del payload o generado

### Tests de integración (`tests/integration/messaging/`)

#### `test_rabbitmq_consumer_integration.py`

- Consumer se conecta a RabbitMQ correctamente
- Publica mensaje → consumer lo procesa y ejecuta use case
- Mensaje con payload inválido → termina en DLQ
- Consumer reconnect tras desconexión
- Graceful shutdown no pierde mensajes en vuelo

## Criterios de Aceptación

- [ ] Consumer escucha `document.ready_for_indexing.v1` del exchange `rag.documents.events`
- [ ] Crea `IndexDocumentCommand` y ejecuta use case por cada mensaje
- [ ] ACK manual tras éxito o fallo de negocio persistido
- [ ] NACK + DLQ tras fallo permanente (payload inválido, max retries)
- [ ] NACK + requeue para fallos transitorios (con límite)
- [ ] Declara queue y binding en startup
- [ ] Se integra en lifecycle (startup/shutdown)
- [ ] Logging con correlation_id y tenant_id
- [ ] Tests unitarios de parsing/validación pasan
- [ ] Tests de integración pasan contra RabbitMQ
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run ruff check .` pasa
