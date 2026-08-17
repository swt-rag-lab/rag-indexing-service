"""TenantId value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from indexing_service.domain.exceptions import InvalidTenantIdError

_TENANT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")


@dataclass(frozen=True)
class TenantId:
    """Identifies a tenant. Immutable, validated, compared by value."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidTenantIdError("TenantId must not be empty.")
        if not _TENANT_ID_PATTERN.match(self.value):
            raise InvalidTenantIdError(
                f"TenantId '{self.value}' has invalid format. "
                "Must be alphanumeric with optional hyphens/underscores, max 100 chars."
            )

    def __str__(self) -> str:
        return self.value
