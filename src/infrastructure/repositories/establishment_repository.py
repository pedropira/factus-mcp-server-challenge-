"""
Repository for Establishment entity.
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories.base import BaseRepository
from src.schemas.models import Establishment


class EstablishmentRepository(BaseRepository[Establishment]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Establishment)

    async def get_by_name(self, name: str) -> Optional[Establishment]:
        """Busca un establecimiento por nombre."""
        stmt = select(Establishment).where(Establishment.name == name)
        result = await self._session.exec(stmt)
        return result.one_or_none()
