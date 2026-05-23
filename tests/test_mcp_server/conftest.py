"""Shared fixtures for MCP server integration tests.

Usage::

    # Test with fully registered server
    async def test_something(registered_server):
        tools = await registered_server.list_tools()
        assert len(tools) == 47

    # Test with just registration  
    async def test_thing(server, server_deps):
        from src.mcp_server.tools import register_all_tools
        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        assert len(tools) > 0
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.infrastructure.factus_client import FactusClient
    from src.mcp_server.main import ServerDeps


# ═══════════════════════════════════════════════════════════════════════════
# Shared constants
# ═══════════════════════════════════════════════════════════════════════════

EXPECTED_TOOL_COUNT = 47
EXPECTED_PROMPT_COUNT = 9
EXPECTED_RESOURCE_COUNT = 4  # static resources (factus://config/*)
EXPECTED_RESOURCE_TEMPLATE_COUNT = 1  # URI template (factus://dian/{category})

EXPECTED_DIAN_CATEGORIES = [
    "document-types",
    "identification-types",
    "tribute-codes",
    "unit-measures",
    "payment-forms",
    "payment-methods",
    "standard-codes",
    "allowance-charge-concepts",
    "correction-codes",
]

EXPECTED_PROMPT_NAMES = [
    "crear-factura-guia",
    "crear-nota-credito-guia",
    "crear-documento-soporte-guia",
    "crear-nota-ajuste-guia",
    "analizar-obligaciones-tributarias",
    "analizar-factura-antes-enviar",
    "comparar-tipos-documento",
    "analizar-codigos-dian",
    "simular-retenciones",
]

EXPECTED_CONFIG_URIS = [
    "factus://config/uvt",
    "factus://config/tax-rates",
    "factus://config/reteica-rates",
    "factus://config/withholding-rules",
]


# ═══════════════════════════════════════════════════════════════════════════
# Mock dependencies
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_factus_client() -> MagicMock:
    """Create a mock FactusClient for use in tool tests."""
    mock: MagicMock = MagicMock(spec=["get", "post", "put", "delete"])
    mock.get.return_value = MagicMock(status_code=200, json=lambda: {"data": []})
    mock.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {}})
    mock.put.return_value = MagicMock(status_code=200, json=lambda: {"data": {}})
    mock.delete.return_value = MagicMock(status_code=204, json=lambda: {})
    return mock


@pytest.fixture
def mock_get_session() -> type:
    """Create a mock session factory.

    Returns an async context manager factory that yields an AsyncMock session.
    Usage by tools::

        async with deps.get_session() as session:
            session.execute(...)
    """

    @asynccontextmanager
    async def _factory() -> AsyncGenerator[AsyncMock, None]:
        session = AsyncMock()
        session.execute = AsyncMock()
        session.execute.return_value = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        yield session

    return _factory


@pytest.fixture
def server_deps(
    mock_factus_client: MagicMock,
    mock_get_session: type,
) -> ServerDeps:
    """Create a ServerDeps instance with mocked dependencies."""
    from src.mcp_server.main import ServerDeps

    return ServerDeps(factus=mock_factus_client, get_session=mock_get_session)


# ═══════════════════════════════════════════════════════════════════════════
# Server fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def server() -> FastMCP:
    """Create a bare FastMCP server instance for testing.

    This server has NO lifespan and NO registered tools/prompts/resources.
    Call ``register_all_*`` functions directly to populate it.
    """
    from mcp.server.fastmcp import FastMCP

    return FastMCP("test-factus")


@pytest_asyncio.fixture
async def registered_server(
    server: FastMCP,
    server_deps: ServerDeps,
) -> FastMCP:
    """Create a FastMCP server with ALL tools, prompts, and resources
    registered using mocked dependencies.

    This is the main fixture for integration tests.
    """
    from src.mcp_server.prompts import register_all_prompts
    from src.mcp_server.resources import register_all_resources
    from src.mcp_server.tools import register_all_tools

    register_all_tools(server, server_deps)
    register_all_resources(server)
    register_all_prompts(server)
    return server
