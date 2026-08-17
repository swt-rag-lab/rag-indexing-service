"""Unit tests for TenantId value object."""

import pytest

from indexing_service.domain.exceptions import InvalidTenantIdError
from indexing_service.domain.value_objects.tenant_id import TenantId

pytestmark = pytest.mark.unit


class TestTenantId:
    def test_valid_tenant_id_creation(self) -> None:
        tenant = TenantId(value="acme-corp")
        assert tenant.value == "acme-corp"

    def test_empty_tenant_id_raises(self) -> None:
        with pytest.raises(InvalidTenantIdError):
            TenantId(value="")

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "has space",
            "special!char",
            "dots.not.allowed",
            " leading-space",
            "-starts-with-hyphen",
        ],
    )
    def test_invalid_format_raises(self, invalid_value: str) -> None:
        with pytest.raises(InvalidTenantIdError):
            TenantId(value=invalid_value)

    def test_equality_by_value(self) -> None:
        t1 = TenantId(value="tenant-1")
        t2 = TenantId(value="tenant-1")
        assert t1 == t2

    def test_str_returns_value(self) -> None:
        tenant = TenantId(value="my-tenant")
        assert str(tenant) == "my-tenant"
