"""
Tests for ProductService.

Mocks ProductRepository to verify CRUD + search + get_by_code behavior.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.schemas.dto import ProductCreate, ProductUpdate
from src.schemas.models import Product
from src.services.product_service import ProductService


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def service(mock_session: AsyncMock) -> ProductService:
    return ProductService(mock_session)


@pytest.fixture
def sample_product() -> Product:
    return Product(
        id=1,
        code_reference="PROD-001",
        name="Laptop",
        price=Decimal("2500.00"),
        tax_rate="19.00",
        unit_measure_id=70,
        standard_code_id=1,
        tribute_id=1,
    )


# ─── CREATE ──────────────────────────────────────────────────────────────────


class TestProductServiceCreate:
    async def test_creates_product_successfully(
        self, service: ProductService
    ) -> None:
        data = ProductCreate(
            code_reference="PROD-001",
            name="Laptop",
            price=Decimal("2500.00"),
            tax_rate="19.00",
            unit_measure_id=70,
            standard_code_id=1,
            tribute_id=1,
        )
        expected = Product(id=1, **data.model_dump())

        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.create = AsyncMock(return_value=expected)
            result = await service.create(data)

            assert result.id == 1
            assert result.code_reference == "PROD-001"
            mock_repo.create.assert_awaited_once()


# ─── GET BY ID ───────────────────────────────────────────────────────────────


class TestProductServiceGetById:
    async def test_returns_product_when_found(
        self,
        service: ProductService,
        sample_product: Product,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_product)
            result = await service.get_by_id(1)

            assert result is not None
            assert result.id == 1
            mock_repo.get_by_id.assert_awaited_once_with(1)

    async def test_returns_none_when_not_found(
        self, service: ProductService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await service.get_by_id(999)

            assert result is None
            mock_repo.get_by_id.assert_awaited_once_with(999)


# ─── GET BY CODE ─────────────────────────────────────────────────────────────


class TestProductServiceGetByCode:
    async def test_returns_product_when_found(
        self,
        service: ProductService,
        sample_product: Product,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_code = AsyncMock(return_value=sample_product)
            result = await service.get_by_code("PROD-001")

            assert result is not None
            assert result.code_reference == "PROD-001"
            mock_repo.get_by_code.assert_awaited_once_with("PROD-001")

    async def test_returns_none_when_not_found(
        self, service: ProductService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_code = AsyncMock(return_value=None)
            result = await service.get_by_code("NONEXISTENT")

            assert result is None


# ─── SEARCH ──────────────────────────────────────────────────────────────────


class TestProductServiceSearch:
    async def test_returns_matching_products(
        self,
        service: ProductService,
        sample_product: Product,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.search = AsyncMock(return_value=[sample_product])
            results = await service.search("Laptop")

            assert len(results) == 1
            assert results[0].name == "Laptop"
            mock_repo.search.assert_awaited_once_with("Laptop", 20)

    async def test_returns_empty_when_no_match(
        self, service: ProductService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.search = AsyncMock(return_value=[])
            results = await service.search("NoExiste")

            assert len(results) == 0


# ─── UPDATE ──────────────────────────────────────────────────────────────────


class TestProductServiceUpdate:
    async def test_updates_product_successfully(
        self,
        service: ProductService,
        sample_product: Product,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_product)
            updated = Product(
                id=1,
                code_reference="PROD-001",
                name="Laptop Pro",
                price=Decimal("3000.00"),
                tax_rate="19.00",
                unit_measure_id=70,
                standard_code_id=1,
                tribute_id=1,
            )
            mock_repo.update = AsyncMock(return_value=updated)

            result = await service.update(
                1, ProductUpdate(name="Laptop Pro", price=Decimal("3000.00"))
            )

            assert result.name == "Laptop Pro"
            assert result.price == Decimal("3000.00")

    async def test_raises_when_not_found(
        self, service: ProductService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Product with id 999 not found"):
                await service.update(999, ProductUpdate(name="X"))


# ─── DELETE ──────────────────────────────────────────────────────────────────


class TestProductServiceDelete:
    async def test_deletes_product_successfully(
        self,
        service: ProductService,
        sample_product: Product,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_product)
            mock_repo.delete = AsyncMock()

            await service.delete(1)

            mock_repo.delete.assert_awaited_once_with(sample_product)

    async def test_raises_when_not_found(
        self, service: ProductService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Product with id 999 not found"):
                await service.delete(999)
