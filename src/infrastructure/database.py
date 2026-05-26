"""
Conexion a base de datos async via SQLModel/SQLAlchemy.

Soporta SQLite (aiosqlite) y PostgreSQL (asyncpg).
Detecta automaticamente el tipo de DB desde la URL.

Proporciona:
  - engine global (perezoso, singleton)
  - create_db_and_tables() para inicializar el schema en startup
  - get_session() como async generator para FastAPI/MCP dependency injection
  - get_async_session() como context manager para uso directo
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import Settings

_engine: Optional[AsyncEngine] = None


def _is_sqlite_url(url: str) -> bool:
    """Detecta si la URL de base de datos es SQLite.

    SQLite URLs pueden ser:
      - sqlite+aiosqlite:///path
      - sqlite:///path
      - sqlite+pysqlite:///path
    """
    return url.startswith("sqlite")


def _ensure_async_driver(url: str) -> str:
    """Agrega el driver async si la URL no lo incluye.

    SQLite:  sqlite:///path -> sqlite+aiosqlite:///path
    PostgreSQL: postgresql://user:pass@host/db -> postgresql+asyncpg://user:pass@host/db
    """
    if "+" in url.split("://")[0]:
        return url  # ya tiene driver explícito

    if url.startswith("sqlite"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    if url.startswith("postgresql"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def _resolve_db_url(settings: Optional[Settings] = None) -> str:
    """Obtiene y normaliza la URL de base de datos."""
    db_url = settings.DATABASE_URL if settings else Settings().DATABASE_URL
    return _ensure_async_driver(db_url)


def get_engine(settings: Optional[Settings] = None) -> AsyncEngine:
    """Retorna el engine global (singleton con inicializacion perezosa).

    Crea el engine la primera vez que se llama usando la URL de la DB.
    Reusa el engine en llamadas posteriores.
    """
    global _engine
    if _engine is None:
        db_url = _resolve_db_url(settings)
        is_sqlite = _is_sqlite_url(db_url)

        engine_kwargs: dict = {
            "echo": False,
            "pool_pre_ping": True,
        }

        if is_sqlite:
            engine_kwargs["connect_args"] = {
                "timeout": 60,
                "check_same_thread": False,
            }
        else:
            # PostgreSQL: pool settings + SSL requerido (Supabase, Render, etc.)
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
            engine_kwargs["connect_args"] = {
                "ssl": "require",
            }

        _engine = create_async_engine(db_url, **engine_kwargs)

        if is_sqlite:
            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragmas(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


async def create_db_and_tables(settings: Optional[Settings] = None) -> None:
    """Crea todas las tablas definidas con SQLModel (table=True).

    Ejecuta SQLModel.metadata.create_all(engine) que crea las tablas
    si no existen (idempotente — seguro llamarlo siempre en startup).

    Args:
        settings: Instancia de Settings (opcional, se carga si no se pasa).
    """
    engine = get_engine(settings)

    async with engine.begin() as conn:
        from src.schemas import models  # noqa: F401 — necesario para registrar modelos en metadata

        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    """Libera el engine global y cierra todas las conexiones.

    Debe llamarse durante el shutdown del servidor para evitar locks
    en la base de datos entre procesos.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


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
