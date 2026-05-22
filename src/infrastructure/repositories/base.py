"""
Base repository with common async CRUD operations for SQLModel entities.

Proporciona operaciones genéricas:
  - get_by_id, get_all, create, update, delete
  - Cada repositorio específico extiende esta clase.

Usa Session (async) de SQLModel/SQLAlchemy.
"""

from __future__ import annotations

from typing import Generic, Optional, Sequence, TypeVar

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """Base repository with generic async CRUD operations."""

    def __init__(self, session: AsyncSession, model_class: type[ModelT]) -> None:
        self._session = session
        self._model = model_class

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        """Obtiene una entidad por su ID."""
        return await self._session.get(self._model, entity_id)

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        order_field: Optional[str] = None,
        descending: bool = False,
    ) -> Sequence[ModelT]:
        """Obtiene todas las entidades con paginación."""
        stmt = select(self._model)

        if order_field and hasattr(self._model, order_field):
            order_col = getattr(self._model, order_field)
            stmt = stmt.order_by(order_col.desc() if descending else order_col)

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.exec(stmt)
        return result.all()

    async def create(self, entity: ModelT) -> ModelT:
        """Crea una nueva entidad en la base de datos."""
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Actualiza una entidad existente (requiere que el PK esté presente)."""
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Elimina una entidad de la base de datos."""
        await self._session.delete(entity)
        await self._session.commit()

    async def count(self) -> int:
        """Cuenta el total de entidades de este tipo."""
        stmt = select(self._model)
        result = await self._session.exec(stmt)
        return len(result.all())
