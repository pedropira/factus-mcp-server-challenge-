"""Tests for MCP tool module registration.

Covers:
  - All tool modules export a register() function
  - register_all_tools() registers exactly 47 tools
  - Tool names are lowercase_snake_case
  - Each tool has non-empty input schema
  - Each module-level register() adds the expected number of tools
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .conftest import EXPECTED_TOOL_COUNT

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


# ═══════════════════════════════════════════════════════════════════════════
# Module verification
# ═══════════════════════════════════════════════════════════════════════════


class TestToolModules:
    """Verify each tool module exports a register() function."""

    MODULES = [
        "customer_tools",
        "establishment_tools",
        "numbering_range_tools",
        "product_tools",
        "invoice_tools",
        "credit_note_tools",
        "support_doc_tools",
        "adjustment_note_tools",
        "company_tool",
    ]

    # (module_name, expected_tool_count)
    MODULE_COUNTS: list[tuple[str, int]] = [
        ("customer_tools", 5),
        ("establishment_tools", 5),
        ("numbering_range_tools", 4),
        ("product_tools", 6),
        ("invoice_tools", 8),
        ("credit_note_tools", 6),
        ("support_doc_tools", 6),
        ("adjustment_note_tools", 6),
        ("company_tool", 1),
    ]

    def test_all_modules_have_register(self) -> None:
        """Every tool module should export a register() function."""
        import importlib

        for module_name in self.MODULES:
            mod = importlib.import_module(
                f"src.mcp_server.tools.{module_name}"
            )
            assert hasattr(mod, "register"), (
                f"{module_name} is missing register()"
            )
            assert callable(mod.register), (
                f"{module_name}.register is not callable"
            )

    @pytest.mark.parametrize(
        "module_name,expected_count",
        MODULE_COUNTS,
        ids=[m[0] for m in MODULE_COUNTS],
    )
    def test_module_tool_count(
        self,
        module_name: str,
        expected_count: int,
    ) -> None:
        """Each module should have expected number of @server.tool() decorators."""
        import pathlib

        src = (
            pathlib.Path("src")
            / "mcp_server"
            / "tools"
            / f"{module_name}.py"
        )
        content = src.read_text()
        count = content.count("@server.tool()")
        assert count == expected_count, (
            f"{module_name}: expected {expected_count} tools, found {count}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Registration integration
# ═══════════════════════════════════════════════════════════════════════════


class TestToolRegistration:
    """Verify tools register correctly on the server."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """register_all_tools() should register exactly 47 tools."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        assert len(tools) == EXPECTED_TOOL_COUNT

    @pytest.mark.asyncio
    async def test_all_tools_have_names(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """Every registered tool should have a non-empty name."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        for t in tools:
            assert t.name, "Tool has empty name"
            assert t.name.islower(), (
                f"Tool name '{t.name}' should be lowercase"
            )

    @pytest.mark.asyncio
    async def test_all_tools_have_descriptions(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """Every registered tool should have a non-empty description."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        for t in tools:
            assert t.description, f"Tool '{t.name}' has empty description"

    @pytest.mark.asyncio
    async def test_all_tools_have_schemas(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """Every registered tool should have an inputSchema."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        for t in tools:
            assert t.inputSchema is not None, (
                f"Tool '{t.name}' has no inputSchema"
            )
            assert "type" in t.inputSchema, (
                f"Tool '{t.name}' inputSchema missing 'type'"
            )

    @pytest.mark.asyncio
    async def test_tool_names_are_unique(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """All tool names must be unique."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), "Duplicate tool names found"


# ═══════════════════════════════════════════════════════════════════════════
# Schema validation
# ═══════════════════════════════════════════════════════════════════════════


class TestToolSchemas:
    """Verify tool input schemas reference valid Pydantic models."""

    @pytest.mark.asyncio
    async def test_tool_schemas_have_properties(
        self,
        server: FastMCP,
        server_deps: ServerDeps,
    ) -> None:
        """Every tool schema should have at least one property (the params model)."""
        from src.mcp_server.tools import register_all_tools

        register_all_tools(server, server_deps)
        tools = await server.list_tools()
        for t in tools:
            props = t.inputSchema.get("properties", {})
            assert len(props) >= 1, (
                f"Tool '{t.name}' has no input properties"
            )
