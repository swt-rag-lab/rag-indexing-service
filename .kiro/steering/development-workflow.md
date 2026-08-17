---
inclusion: always
---

# Development Workflow — indexing-service

## Package Manager

Use `uv` exclusively. Never use `pip`, `poetry`, or `pipenv`.

```bash
uv sync                     # Install all dependencies from lockfile
uv add <pkg>                # Add runtime dependency
uv add --dev <pkg>          # Add dev dependency
uv run <cmd>                # Execute command in managed environment
```

Always commit `pyproject.toml` and `uv.lock` together after dependency changes.

## Local Execution

```bash
uv run uvicorn indexing_service.main:create_app --factory --reload --port 8003
```

External services (PostgreSQL, MinIO, RabbitMQ, Qdrant) are provided via Docker Compose in `local-platform/`.

## Quality Commands

Run before every commit:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src/indexing_service
uv run pytest -m "not integration and not e2e and not slow"
```

## Running Tests

```bash
# Fast (no infrastructure required)
uv run pytest -m "not integration and not e2e and not slow"

# With coverage
uv run pytest --cov=indexing_service --cov-report=term-missing

# Integration (requires Docker services running)
uv run pytest -m integration
```

Minimum coverage target: 80%. Domain and use cases: aim for 90%+.

## Migrations

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Always review auto-generated migrations before committing.

## Code Conventions

- Python >= 3.12 with type hints on all public interfaces.
- Async-first: use `async/await` for all I/O operations.
- Absolute imports from package root: `from indexing_service.domain...`
- Never import via `src.` or `app.` prefix.
- `snake_case` for files, functions, variables. `PascalCase` for classes.
- Ports named by capability: `Embedder`, `VectorStore`, `ChunkingStrategy`.
- Adapters include technology: `OpenAIEmbedder`, `QdrantVectorStore`, `SemanticChunker`.
- Use cases named as verb + object: `IndexDocumentUseCase`.
- Structured logging with `structlog`. Include `tenant_id`, `document_id`, `correlation_id` where relevant.
- No mutable global state. Configuration loaded once at startup via `pydantic-settings`.

## Layer Dependency Rules

When creating or modifying code, respect the inward dependency direction:

| Layer | May depend on | Must NOT depend on |
|---|---|---|
| Domain | Nothing external | FastAPI, SQLAlchemy, MinIO, OpenAI, Qdrant, tiktoken, Pydantic, env vars |
| Application | Domain | FastAPI, SQLAlchemy, MinIO, OpenAI, Qdrant, infrastructure |
| Infrastructure | Domain (ports) | API layer |
| API / Consumers | Application (use cases, DTOs) | Domain directly, Infrastructure directly |
| Bootstrap | All layers (composition root) | — |

## Checklist for New Features

1. Define or extend domain entities and value objects with invariants.
2. Define port interfaces required by the use case.
3. Implement use case in `application/use_cases/`.
4. Implement infrastructure adapters against ports.
5. Wire dependencies in `bootstrap/container.py`.
6. Write unit tests for domain logic (no infrastructure).
7. Write application tests with fakes for ports.
8. Write integration tests for new adapters.
9. Run full quality pipeline (format, lint, type-check, test).

## Environment Variables

Defined in `.env` for local development (never committed). Use `.env.example` as template. Configuration loaded via `pydantic-settings` in `config/settings.py`.

## Git Conventions

- Branch from `main` for each feature or fix.
- Concise commit messages in imperative mood (e.g., "Add semantic chunking strategy").
- Stage specific files; avoid `git add .`.
- Never commit `.env`, `.venv/`, `__pycache__/`, or coverage artifacts.
