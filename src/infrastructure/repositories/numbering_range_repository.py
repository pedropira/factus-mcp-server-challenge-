"""
Repository for NumberingRange entity.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories.base import BaseRepository
from src.schemas.models import NumberingRange


class NumberingRangeRepository(BaseRepository[NumberingRange]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, NumberingRange)

    async def get_active(
        self,
        document_type_id: Optional[str] = None,
    ) -> Sequence[NumberingRange]:
        """Obtiene rangos activos, opcionalmente filtrados por tipo de documento."""
        stmt = select(NumberingRange).where(NumberingRange.is_active == True)
        if document_type_id is not None:
            stmt = stmt.where(
                NumberingRange.document_type_id == document_type_id
            )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_by_prefix(self, prefix: str) -> Optional[NumberingRange]:
        """Busca un rango por su prefijo."""
        stmt = select(NumberingRange).where(
            NumberingRange.prefix == prefix
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_by_factus_id(self, factus_id: int) -> Optional[NumberingRange]:
        """Busca un rango por su ID en la API de Factus."""
        stmt = select(NumberingRange).where(
            NumberingRange.factus_id == factus_id
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_by_prefix_and_doc_type(
        self, prefix: str, document_type_id: str
    ) -> Optional[NumberingRange]:
        """Busca un rango por prefijo + tipo de documento."""
        stmt = select(NumberingRange).where(
            NumberingRange.prefix == prefix,
            NumberingRange.document_type_id == document_type_id,
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_default_for_document_type(
        self, document_type_id: str
    ) -> Optional[NumberingRange]:
        """Obtiene el primer rango activo para un tipo de documento."""
        stmt = (
            select(NumberingRange)
            .where(
                NumberingRange.is_active == True,
                NumberingRange.document_type_id == document_type_id,
            )
            .limit(1)
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()
