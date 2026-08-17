# Spec 0 — Proyecto Base: Bootstrap, Configuración, Health Checks + Qdrant en local-platform

**Estado:** Pendiente  
**Prioridad:** Alta  
**Dependencias:** local-platform (ya existe)

## Objetivo

Crear la estructura del proyecto indexing-service, configuración tipada,
aplicación FastAPI con health checks, logging estructurado, pipeline de calidad,
y agregar Qdrant al Docker Compose de local-platform.

## Entregables

### Proyecto

- `pyproject.toml` con dependencias pinneadas, build-system (hatchling), ruff, mypy, pytest markers
- `uv.lock` generado
- `.env.example` con todas las variables
- `.gitignore`

### Dependencias de ejecución

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
structlog==24.4.0
sqlalchemy[asyncio]==2.0.36
alembic==1.14.1
asyncpg==0.30.0
minio==7.2.12
aio-pika==9.5.4
tenacity==9.0.0
openai==1.58.1
qdrant-client==1.12.1
tiktoken==0.8.0
semchunk==2.2.0
```

### Dependencias de desarrollo

```text
pytest==8.3.4
pytest-asyncio==0.25.0
pytest-cov==6.0.0
httpx==0.28.1
ruff==0.8.6
mypy==1.14.1
```

### Estructura de paquetes

```text
src/indexing_service/
├── __init__.py
├── main.py
├── domain/__init__.py
├── application/__init__.py
├── infrastructure/
│   ├── __init__.py
│   └── observability/
│       ├── __init__.py
│       └── logging.py
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── health.py
│   └── middleware.py
├── bootstrap/
│   ├── __init__.py
│   ├── container.py
│   └── lifecycle.py
└── config/
    ├── __init__.py
    └── settings.py
```

### Configuración (`config/settings.py`)

Usar `pydantic-settings` con `BaseSettings`:

| Variable | Default | Descripción |
|---|---|---|
| APP_NAME | indexing-service | Nombre del servicio |
| APP_VERSION | 0.1.0 | Versión |
| APP_ENV | development | Entorno |
| PORT | 8003 | Puerto HTTP |
| DATABASE_URL | postgresql+asyncpg://postgres:postgres@localhost:5432/indexing | PostgreSQL |
| QDRANT_HOST | localhost | Host de Qdrant |
| QDRANT_PORT | 6333 | Puerto gRPC de Qdrant |
| QDRANT_API_KEY | (vacío) | API key (opcional, para producción) |
| QDRANT_COLLECTION | documents | Nombre de la colección |
| OPENAI_API_KEY | (requerido) | Clave de API de OpenAI |
| OPENAI_EMBEDDING_MODEL | text-embedding-3-small | Modelo de embeddings |
| OPENAI_EMBEDDING_DIMENSIONS | 1536 | Dimensiones del vector |
| OPENAI_EMBEDDING_BATCH_SIZE | 100 | Batch size para embeddings |
| EMBEDDING_PROVIDER | openai | Proveedor de embeddings (openai, futuro: cohere, local, bedrock) |
| MINIO_ENDPOINT | localhost:9000 | Endpoint de MinIO |
| MINIO_ACCESS_KEY | minioadmin | Access key |
| MINIO_SECRET_KEY | minioadmin | Secret key |
| MINIO_BUCKET_READ | processed-documents | Bucket de lectura |
| MINIO_SECURE | false | TLS |
| RABBITMQ_URL | amqp://rabbitmq:rabbitmq@localhost:5672/rag-lab | URL de RabbitMQ |
| RABBITMQ_EXCHANGE | rag.documents.events | Exchange de eventos |
| CHUNKING_MAX_TOKENS | 1024 | Tamaño máximo de chunk en tokens (optimizado para RFP) |
| CHUNKING_HARD_MAX_TOKENS | 2048 | Límite absoluto (para tablas/bloques atómicos muy grandes) |
| CHUNKING_OVERLAP_TOKENS | 200 | Overlap entre chunks |
| CHUNKING_VERSION | semantic-v1 | Versión de la estrategia de chunking (se almacena en metadata) |
| OUTBOX_POLL_INTERVAL | 1.0 | Segundos entre polls del outbox publisher |
| OUTBOX_BATCH_SIZE | 50 | Eventos por ciclo de poll |
| OUTBOX_MAX_ATTEMPTS | 5 | Reintentos antes de marcar evento como failed |
| LOG_LEVEL | INFO | Nivel de log |
| LOG_FORMAT | json | Formato (json/console) |

### `main.py`

```python
def create_app() -> FastAPI:
    # Load settings
    # Init container
    # Configure structlog
    # Add middleware
    # Include routers
    # Add lifespan (startup/shutdown)
    ...
```

### Health Checks (`api/routes/health.py`)

- `GET /health/live` → 200 `{"status": "alive"}`
- `GET /health/ready` → verifica PostgreSQL, RabbitMQ y Qdrant
  - Respuesta: `{"status": "ready", "checks": {"postgres": "ok", "rabbitmq": "ok", "qdrant": "ok"}}`
  - Si alguno falla: 503 con detalle

### Middleware (`api/middleware.py`)

- Request ID (generado si no viene en header `X-Request-ID`)
- Correlation ID (propagado desde header `X-Correlation-ID`)
- Logging con contexto (request_id, correlation_id, method, path)

### Bootstrap (`bootstrap/container.py`)

- Container con settings, db_engine, health check utilities
- `init_container()`, `get_container()`

### Bootstrap (`bootstrap/lifecycle.py`)

- Lifespan handler: startup (init container, verify connections) y shutdown (dispose resources)

### Logging (`infrastructure/observability/logging.py`)

- Configuración de structlog con processors
- JSON en producción, consola coloreada en desarrollo
- Bind automático de service_name

### Infraestructura local (local-platform)

#### Agregar Qdrant al Docker Compose

```yaml
qdrant:
  image: qdrant/qdrant:v1.12.4
  container_name: rag-lab-qdrant
  ports:
    - "${QDRANT_HTTP_PORT:-6333}:6333"
    - "${QDRANT_GRPC_PORT:-6334}:6334"
  volumes:
    - qdrant_data:/qdrant/storage
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:6333/readyz"]
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 10s
  restart: unless-stopped
```

- Agregar volumen `qdrant_data` a la sección volumes
- Agregar variables `QDRANT_HTTP_PORT` y `QDRANT_GRPC_PORT` al `.env` y `.env.example`

#### Agregar base de datos `indexing` a PostgreSQL

Opción: crear script de init o usar `POSTGRES_MULTIPLE_DATABASES`.
Recomendación: agregar un servicio `postgres-init-indexing` que ejecute:

```sql
SELECT 'CREATE DATABASE indexing' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'indexing')\gexec
```

O actualizar el healthcheck para que el PostgreSQL siga con la DB principal
y crear la DB `indexing` via un init container.

#### Agregar bucket `processed-documents` a MinIO init

Agregar al servicio `minio-init` existente:

```bash
mc mb local/processed-documents --ignore-existing;
```

### Tests

- `tests/__init__.py`
- `tests/conftest.py` con fixture HTTPX (`async_client`)
- `tests/api/__init__.py`
- `tests/api/test_health.py`

## Criterios de Aceptación

- [ ] `uv run uvicorn indexing_service.main:create_app --factory --port 8003` arranca sin error
- [ ] `GET /health/live` retorna 200
- [ ] `GET /health/ready` retorna 200 (con servicios de local-platform corriendo)
- [ ] Qdrant aparece en Docker Compose y responde en puerto 6333
- [ ] Base de datos `indexing` existe en PostgreSQL de local-platform
- [ ] Bucket `processed-documents` existe en MinIO
- [ ] `uv run ruff format --check .` pasa
- [ ] `uv run ruff check .` pasa
- [ ] `uv run mypy src/indexing_service` pasa
- [ ] `uv run pytest` pasa
