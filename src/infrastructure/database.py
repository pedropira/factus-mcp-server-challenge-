"""
Conexion a base de datos SQLite async via SQLModel/SQLAlchemy.

Proporciona:
  - engine global (perezoso, singleton)
  - create_db_and_tables() para inicializar el schema en startup
  - get_session() como async generator para FastAPI/MCP dependency injection
  - get_async_session() como context manager para uso directo

La DB se crea automaticamente la primera vez que se arranca el server
(archivo factus.db en el directorio de trabajo).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import Settings

_engine: Optional[AsyncEngine] = None


def get_engine(settings: Optional[Settings] = None) -> AsyncEngine:
    """Retorna el engine global (singleton con inicializacion perezosa).

    Crea el engine la primera vez que se llama usando la URL de la DB.
    Reusa el engine en llamadas posteriores.
    """
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL if settings else Settings().DATABASE_URL
        _engine = create_async_engine(
            db_url,
            echo=False,  # Cambiar a True para debug SQL
        )
    return _engine


async def create_db_and_tables(settings: Optional[Settings] = None) -> None:
    """Crea todas las tablas definidas con SQLModel (table=True).

    Ejecuta SQLModel.metadata.create_all(engine) que crea las tablas
    si no existen (idempotente — seguro llamarlo siempre en startup).

    Args:
        settings: Instancia de Settings (opcional, se carga si no se pasa).
    """
    engine = get_engine(settings)

    # SQLModel.metadata.create_all funciona con async engines
    # usando run_sync() para ejecutar el DDL en el event loop correcto
    async with engine.begin() as conn:
        from src.schemas import models  # noqa: F401 — import necesario para registrar modelos en metadata

        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator que produce sesiones de base de datos.

    Disenado para usar como dependencia en FastAPI/MCP:
        async def my_endpoint(session: Annotated[AsyncSession, Depends(get_session)]):
            ...
    """
    engine = get_engine()
    async with AsyncSession(engine) as session:
        yield session


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager para uso directo de sesion async.

    Uso:
        async with get_async_session() as session:
            repo = CustomerRepository(session)
            customer = await repo.get_by_id(1)
    """
    engine = get_engine()
    async with AsyncSession(engine) as session:
        yield session
