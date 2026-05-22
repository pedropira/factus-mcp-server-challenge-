"""
Repository for Product entity (catalog).
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories.base import BaseRepository
from src.schemas.models import Product


class ProductRepository(BaseRepository[Product]):
    """Repository for Product CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def get_by_code(self, code_reference: str) -> Optional[Product]:
        """Busca un producto por su código de referencia único."""
        stmt = select(Product).where(
            Product.code_reference == code_reference
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> Sequence[Product]:
        """Busca productos por nombre o código de referencia."""
        pattern = f"%{query}%"
        stmt = (
            select(Product)
            .where(
                Product.name.ilike(pattern)
                | Product.code_reference.ilike(pattern)
            )
            .limit(limit)
        )
        result = await self._session.exec(stmt)
        return result.all()
