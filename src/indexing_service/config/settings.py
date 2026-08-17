"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration via pydantic-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "indexing-service"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development")
    port: int = 8003

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/indexing"
    )

    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="documents")

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_embedding_dimensions: int = Field(default=1536)
    openai_embedding_batch_size: int = Field(default=100)
    embedding_provider: str = Field(default="openai")

    # MinIO
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_bucket_read: str = Field(default="processed-documents")
    minio_secure: bool = False

    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://rabbitmq:rabbitmq@localhost:5672/rag-lab")
    rabbitmq_exchange: str = Field(default="rag.documents.events")
    rabbitmq_consumer_queue: str = Field(default="indexing.document.ready_for_indexing")
    rabbitmq_consumer_routing_key: str = Field(default="document.ready_for_indexing.v1")
    rabbitmq_prefetch_count: int = Field(default=5)
    rabbitmq_max_retries: int = Field(default=3)

    # Chunking
    chunking_max_tokens: int = Field(default=1024)
    chunking_hard_max_tokens: int = Field(default=2048)
    chunking_overlap_tokens: int = Field(default=200)
    chunking_version: str = Field(default="semantic-v1")

    # Outbox
    outbox_poll_interval: float = Field(default=1.0)
    outbox_batch_size: int = Field(default=50)
    outbox_max_attempts: int = Field(default=5)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    service_name: str = Field(default="indexing-service")


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
