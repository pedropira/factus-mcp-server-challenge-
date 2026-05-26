"""
MCP server factory for the Factus electronic invoicing system.

Creates and configures a FastMCP server instance with:
  - Lifespan-based startup/shutdown (DB, FactusClient)
  - Dependency injection via ServerDeps dataclass
  - All tools, resources, and prompts registered on startup
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.config import Settings
from src.infrastructure.database import (
    create_db_and_tables,
    dispose_engine,
    get_async_session,
)
from src.infrastructure.factus_client import FactusClient
from src.mcp_server.prompts import register_all_prompts
from src.mcp_server.resources import register_all_resources
from src.mcp_server.tools import register_all_tools

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from mcp.server.fastmcp import FastMCP
    from sqlmodel.ext.asyncio.session import AsyncSession


# ── Dependencies ──────────────────────────────────────────────────────────


@dataclass
class ServerDeps:
    """Shared dependencies for all MCP tool handlers.

    Attributes:
        factus: Authenticated Factus HTTP client for API calls.
        get_session: Async context manager factory for database sessions.
            Usage: async with deps.get_session() as session: ...
    """

    factus: FactusClient
    get_session: callable  # () -> AsyncGenerator[AsyncSession, None]


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle for the Factus MCP server.

    On startup:
        1. Load settings from environment / .env
        2. Create database tables if they don't exist
        3. Create Factus HTTP client with transparent OAuth2 auth
        4. Register all tools, resources, and prompts on the server

    On shutdown:
        1. Close the Factus HTTP client
    """
    settings = Settings()
    await create_db_and_tables(settings)

    factus_client = FactusClient(settings)
    await factus_client.__aenter__()

    deps = ServerDeps(factus=factus_client, get_session=get_async_session)

    register_all_tools(server, deps)
    register_all_resources(server)
    register_all_prompts(server)

    try:
        yield
    finally:
        await factus_client.__aexit__(None, None, None)
        await dispose_engine()  # Liberar la DB para que otros procesos puedan usarla


# ── Server factory ────────────────────────────────────────────────────────


def create_server() -> FastMCP:
    """Create a fully configured Factus MCP server instance.

    The server has all tools, resources, and prompts registered via the
    lifespan hook. This function is called once from the entry point.

    Returns:
        A ready-to-run FastMCP server with stdio transport support.
    """
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "Factus MCP Server",
        instructions="""
        Factus MCP Server para facturación electrónica colombiana (DIAN).

        Proporciona herramientas para crear y gestionar facturas electrónicas,
        notas crédito, documentos soporte y notas de ajuste a través de la API
        de Factus. También incluye recursos con códigos DIAN y prompts guiados.
        """,
        lifespan=_lifespan,
        host="0.0.0.0",
        streamable_http_path="/api",
        json_response=True,
    )
    return server


__all__ = ["ServerDeps", "create_server"]
