"""
Tests for CustomerService.

Mocks CustomerRepository to verify CRUD + search behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.schemas.dto import CustomerCreate, CustomerUpdate
from src.schemas.models import Customer
from src.services.customer_service import CustomerService


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def service(mock_session: AsyncMock) -> CustomerService:
    return CustomerService(mock_session)


@pytest.fixture
def sample_customer() -> Customer:
    return Customer(
        id=1,
        identification_document_id=1,
        identification="123456789",
        dv="0",
        company="Test Corp",
        names="Juan Pérez",
        email="juan@test.com",
    )


# ─── CREATE ──────────────────────────────────────────────────────────────────


class TestCustomerServiceCreate:
    async def test_creates_customer_successfully(
        self, service: CustomerService, mock_session: AsyncMock
    ) -> None:
        data = CustomerCreate(
            identification_document_id=1,
            identification="123456789",
            company="Test Corp",
        )
        expected = Customer(id=1, **data.model_dump())

        with patch.object(
            service, "_repo", spec=True
        ) as mock_repo:
            mock_repo.create = AsyncMock(return_value=expected)
            result = await service.create(data)

            assert result.id == 1
            assert result.identification == "123456789"
            mock_repo.create.assert_awaited_once()


# ─── GET BY ID ───────────────────────────────────────────────────────────────


class TestCustomerServiceGetById:
    async def test_returns_customer_when_found(
        self,
        service: CustomerService,
        sample_customer: Customer,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_customer)
            result = await service.get_by_id(1)

            assert result is not None
            assert result.id == 1
            mock_repo.get_by_id.assert_awaited_once_with(1)

    async def test_returns_none_when_not_found(
        self, service: CustomerService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await service.get_by_id(999)

            assert result is None
            mock_repo.get_by_id.assert_awaited_once_with(999)


# ─── SEARCH ──────────────────────────────────────────────────────────────────


class TestCustomerServiceSearch:
    async def test_returns_matching_customers(
        self,
        service: CustomerService,
        sample_customer: Customer,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.search = AsyncMock(return_value=[sample_customer])
            results = await service.search("Pérez")

            assert len(results) == 1
            assert results[0].names == "Juan Pérez"
            mock_repo.search.assert_awaited_once_with("Pérez", 20)

    async def test_returns_empty_when_no_match(
        self, service: CustomerService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.search = AsyncMock(return_value=[])
            results = await service.search("NoExiste")

            assert len(results) == 0
            mock_repo.search.assert_awaited_once_with("NoExiste", 20)


# ─── UPDATE ──────────────────────────────────────────────────────────────────


class TestCustomerServiceUpdate:
    async def test_updates_customer_successfully(
        self,
        service: CustomerService,
        sample_customer: Customer,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_customer)
            updated = Customer(id=1, identification_document_id=1, identification="123456789", company="Updated Corp")
            mock_repo.update = AsyncMock(return_value=updated)

            result = await service.update(
                1, CustomerUpdate(company="Updated Corp")
            )

            assert result.company == "Updated Corp"
            mock_repo.get_by_id.assert_awaited_once_with(1)
            mock_repo.update.assert_awaited_once()

    async def test_raises_when_not_found(
        self, service: CustomerService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Customer with id 999 not found"):
                await service.update(999, CustomerUpdate(company="X"))

            mock_repo.get_by_id.assert_awaited_once_with(999)


# ─── DELETE ──────────────────────────────────────────────────────────────────


class TestCustomerServiceDelete:
    async def test_deletes_customer_successfully(
        self,
        service: CustomerService,
        sample_customer: Customer,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_customer)
            mock_repo.delete = AsyncMock()

            await service.delete(1)

            mock_repo.get_by_id.assert_awaited_once_with(1)
            mock_repo.delete.assert_awaited_once_with(sample_customer)

    async def test_raises_when_not_found(
        self, service: CustomerService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Customer with id 999 not found"):
                await service.delete(999)

            mock_repo.get_by_id.assert_awaited_once_with(999)
