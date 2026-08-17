# Estándares de Pruebas de Indexing Service

**Proyecto:** RAG Lab  
**Servicio:** `indexing-service`  
**Tipo:** Kiro Steering  
**Estado:** Activo  
**Versión:** 1.0  
**Última actualización:** 2026-08-15

## Estrategia

```text
            ┌──────────────┐
            │ End-to-End   │  Pocas
         ┌──┴──────────────┴──┐
         │ Integración        │
      ┌──┴────────────────────┴──┐
      │ Casos de uso + Fakes     │
   ┌──┴───────────────────────────┴──┐
   │       Dominio unitario          │  Muchas
   └─────────────────────────────────┘
```

## Estructura

```text
tests/
├── unit/
│   └── domain/
│       ├── entities/
│       ├── value_objects/
│       └── policies/
├── application/
│   └── use_cases/
├── integration/
│   ├── persistence/
│   ├── embeddings/
│   ├── vectorstore/
│   ├── chunking/
│   └── messaging/
├── api/
├── fakes/
└── fixtures/
```

## Pruebas unitarias

- No usan infraestructura externa
- Cubren entidades, VOs, políticas, excepciones
- Verifican chunking strategy logic
- Verifican deterministic point ID generation

## Pruebas de aplicación

- Usan fakes para puertos
- Verifican flujo del use case completo (chunk → embed → store)
- Verifican manejo de errores y retries

## Pruebas de integración

- Embedder contra OpenAI API (con mock o real, marcado slow)
- VectorStore contra Qdrant
- Repositorios contra PostgreSQL
- Consumer contra RabbitMQ
- Outbox publisher contra PostgreSQL + RabbitMQ

## Marcadores pytest

```text
unit
application
api
integration
e2e
slow
```

## Cobertura

Mínima global: 80%
Dominio y use cases: aspirar a 90%+

## CI

```bash
uv sync --locked --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src/indexing_service
uv run pytest -m "not integration and not e2e and not slow" \
  --cov=indexing_service \
  --cov-report=term-missing \
  --cov-fail-under=80
```

## Reglas no negociables

1. Tests unitarios sin infraestructura.
2. Casos de uso con fakes.
3. Embedder verificado con tests de integración.
4. VectorStore verificado con tests contra Qdrant.
5. Consumidores con tests de integración.
6. Outbox con tests transaccionales.
7. Tests deterministas e independientes.
8. Cobertura mínima 80%.
