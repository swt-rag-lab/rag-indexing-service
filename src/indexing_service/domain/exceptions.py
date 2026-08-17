"""Domain exceptions for indexing-service."""


class DomainError(Exception):
    """Base class for all domain errors."""


class InvalidStatusTransitionError(DomainError):
    """Raised when an invalid state transition is attempted on an IndexingJob."""


class InvalidTenantIdError(DomainError):
    """Raised when a TenantId has invalid format."""


class ChunkingError(DomainError):
    """Raised when chunking fails."""


class EmbeddingError(DomainError):
    """Raised when embedding generation fails."""


class VectorStoreError(DomainError):
    """Raised when vector store operations fail."""


class DocumentNotFoundError(DomainError):
    """Raised when a document cannot be found."""


class CanonicalReadError(DomainError):
    """Raised when reading the canonical text fails."""
