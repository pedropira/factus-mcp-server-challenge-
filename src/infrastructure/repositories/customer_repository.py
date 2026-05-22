"""
Repository for Customer entity.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories.base import BaseRepository
from src.schemas.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Customer)

    async def get_by_identification(self, identification: str) -> Optional[Customer]:
        """Busca un cliente por su número de identificación."""
        stmt = select(Customer).where(
            Customer.identification == identification
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Busca un cliente por su email."""
        stmt = select(Customer).where(Customer.email == email)
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> Sequence[Customer]:
        """Busca clientes por nombre, identificación o email."""
        pattern = f"%{query}%"
        stmt = (
            select(Customer)
            .where(
                Customer.names.ilike(pattern)
                | Customer.company.ilike(pattern)
                | Customer.identification.ilike(pattern)
                | Customer.email.ilike(pattern)
            )
            .limit(limit)
        )
        result = await self._session.exec(stmt)
        return result.all()
