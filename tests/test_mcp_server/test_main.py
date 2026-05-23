"""Tests for the MCP server factory (main.py).

Covers:
  - create_server() returns properly configured FastMCP
  - ServerDeps dataclass shape
  - Lifespan integration (mock Settings/DB/FactusClient)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# create_server()
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateServer:
    """Verify the server factory produces a correct FastMCP instance."""

    def test_returns_fastmcp_instance(self) -> None:
        """create_server() should return a FastMCP instance."""
        from src.mcp_server.main import create_server

        server = create_server()
        assert isinstance(server, FastMCP)

    def test_server_has_correct_name(self) -> None:
        """Server name must match what clients expect."""
        from src.mcp_server.main import create_server

        server = create_server()
        assert server.name == "Factus MCP Server"

    def test_server_has_instructions(self) -> None:
        """Server should have non-empty instructions for LLM context."""
        from src.mcp_server.main import create_server

        server = create_server()
        assert server.instructions
        assert "Factus" in server.instructions
        assert "DIAN" in server.instructions

    def test_server_has_lifespan(self) -> None:
        """Server should be created with a lifespan.

        We verify by checking that the lifespan parameter was passed to
        FastMCP constructor (the custom _lifespan function).
        """
        from src.mcp_server.main import create_server, _lifespan

        with patch.object(FastMCP, "__init__", return_value=None) as mock_init:
            create_server()
            kwargs = mock_init.call_args.kwargs if hasattr(mock_init.call_args, 'kwargs') else mock_init.call_args[1] if len(mock_init.call_args) > 1 else {}
            assert "lifespan" in kwargs
            assert kwargs["lifespan"] is _lifespan


class TestServerDeps:
    """Verify the ServerDeps dependency container."""

    def test_is_dataclass(self) -> None:
        """ServerDeps should be a dataclass with two fields."""
        import dataclasses

        from src.mcp_server.main import ServerDeps

        assert dataclasses.is_dataclass(ServerDeps)
        fields = dataclasses.fields(ServerDeps)
        field_names = {f.name for f in fields}
        assert field_names == {"factus", "get_session"}


# ═══════════════════════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════════════════════


class TestLifespan:
    """Verify lifespan startup/shutdown logic.

    Uses mocks to avoid requiring actual Settings, DB, or Factus credentials.
    """

    @pytest.mark.asyncio
    async def test_lifespan_calls_registration(
        self,
    ) -> None:
        """Lifespan should call all three registration functions."""
        from src.mcp_server.main import _lifespan

        mock_server = MagicMock()

        with (
            patch("src.mcp_server.main.Settings") as mock_settings,
            patch("src.mcp_server.main.create_db_and_tables", AsyncMock()),
            patch("src.mcp_server.main.FactusClient") as mock_factus_cls,
            patch("src.mcp_server.main.register_all_tools") as mock_reg_tools,
            patch("src.mcp_server.main.register_all_resources") as mock_reg_res,
            patch("src.mcp_server.main.register_all_prompts") as mock_reg_prompts,
        ):
            mock_settings.return_value = MagicMock()
            mock_factus_instance = AsyncMock()
            mock_factus_cls.return_value = mock_factus_instance

            async with _lifespan(mock_server):
                pass

            mock_reg_tools.assert_called_once()
            mock_reg_res.assert_called_once()
            mock_reg_prompts.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_creates_factus_client(self) -> None:
        """Lifespan should create and enter FactusClient."""
        from src.mcp_server.main import _lifespan

        mock_server = MagicMock()

        with (
            patch("src.mcp_server.main.Settings") as mock_settings,
            patch("src.mcp_server.main.create_db_and_tables", AsyncMock()),
            patch("src.mcp_server.main.FactusClient") as mock_factus_cls,
        ):
            mock_factus_instance = AsyncMock()
            mock_factus_cls.return_value = mock_factus_instance

            async with _lifespan(mock_server):
                pass

            mock_factus_cls.assert_called_once()
            mock_factus_instance.__aenter__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lifespan_creates_db(self) -> None:
        """Lifespan should call create_db_and_tables with settings."""
        from src.mcp_server.main import _lifespan

        mock_server = MagicMock()

        with (
            patch("src.mcp_server.main.Settings") as mock_settings,
            patch("src.mcp_server.main.create_db_and_tables") as mock_create_db,
            patch("src.mcp_server.main.FactusClient") as mock_factus_cls,
        ):
            mock_settings_instance = MagicMock()
            mock_settings.return_value = mock_settings_instance
            mock_factus_instance = AsyncMock()
            mock_factus_cls.return_value = mock_factus_instance

            async with _lifespan(mock_server):
                pass

            mock_create_db.assert_awaited_once_with(mock_settings_instance)

    @pytest.mark.asyncio
    async def test_lifespan_shuts_down_factus_client(self) -> None:
        """On shutdown, lifespan should close the Factus client."""
        from src.mcp_server.main import _lifespan

        mock_server = MagicMock()

        with (
            patch("src.mcp_server.main.Settings"),
            patch("src.mcp_server.main.create_db_and_tables", AsyncMock()),
            patch("src.mcp_server.main.FactusClient") as mock_factus_cls,
        ):
            mock_factus_instance = AsyncMock()
            mock_factus_cls.return_value = mock_factus_instance

            async with _lifespan(mock_server):
                pass

            mock_factus_instance.__aexit__.assert_awaited_once()
