"""
EstablishmentService — CRUD for issuer branches (establishments).
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories import EstablishmentRepository
from src.schemas.dto import EstablishmentCreate, EstablishmentUpdate
from src.schemas.models import Establishment


class EstablishmentService:
    """Business logic for establishment (issuer branch) management."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = EstablishmentRepository(session)

    async def create(self, data: EstablishmentCreate) -> Establishment:
        """Register a new establishment."""
        establishment = Establishment.model_validate(data)
        return await self._repo.create(establishment)

    async def get_by_id(self, id: int) -> Optional[Establishment]:
        """Return an establishment by primary key, or None."""
        return await self._repo.get_by_id(id)

    async def get_by_name(self, name: str) -> Optional[Establishment]:
        """Find an establishment by name."""
        return await self._repo.get_by_name(name)

    async def list(
        self, offset: int = 0, limit: int = 20
    ) -> Sequence[Establishment]:
        """Return paginated establishments sorted by name."""
        return await self._repo.get_all(
            offset=offset, limit=limit, order_field="name"
        )

    async def update(
        self, id: int, data: EstablishmentUpdate
    ) -> Establishment:
        """Update an establishment. Raises ValueError if not found."""
        establishment = await self._repo.get_by_id(id)
        if establishment is None:
            raise ValueError(f"Establishment with id {id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(establishment, field, value)
        return await self._repo.update(establishment)

    async def delete(self, id: int) -> None:
        """Delete an establishment. Raises ValueError if not found."""
        establishment = await self._repo.get_by_id(id)
        if establishment is None:
            raise ValueError(f"Establishment with id {id} not found")
        await self._repo.delete(establishment)
