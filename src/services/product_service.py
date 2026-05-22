"""
ProductService — CRUD + search for the product catalog.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories import ProductRepository
from src.schemas.dto import ProductCreate, ProductUpdate
from src.schemas.models import Product


class ProductService:
    """Business logic for product catalog management."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProductRepository(session)

    async def create(self, data: ProductCreate) -> Product:
        """Create a new product from validated input data."""
        product = Product.model_validate(data)
        return await self._repo.create(product)

    async def get_by_id(self, id: int) -> Optional[Product]:
        """Return a product by primary key, or None."""
        return await self._repo.get_by_id(id)

    async def get_by_code(
        self, code_reference: str
    ) -> Optional[Product]:
        """Find a product by its unique code reference."""
        return await self._repo.get_by_code(code_reference)

    async def search(
        self, query: str, limit: int = 20
    ) -> Sequence[Product]:
        """Search products by name or code reference."""
        return await self._repo.search(query, limit)

    async def update(self, id: int, data: ProductUpdate) -> Product:
        """Update a product. Raises ValueError if not found."""
        product = await self._repo.get_by_id(id)
        if product is None:
            raise ValueError(f"Product with id {id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        return await self._repo.update(product)

    async def delete(self, id: int) -> None:
        """Delete a product. Raises ValueError if not found."""
        product = await self._repo.get_by_id(id)
        if product is None:
            raise ValueError(f"Product with id {id} not found")
        await self._repo.delete(product)
