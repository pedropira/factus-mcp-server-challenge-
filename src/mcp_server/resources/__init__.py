"""
MCP resource registrations for the Factus server.

Each submodule exports a `register(server)` function that registers
its resources (static data, DIAN codes, tax config) on the MCP server.

Usage in main.py:
    from src.mcp_server.resources import register_all_resources
    register_all_resources(server)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all_resources(server: FastMCP) -> None:
    """Register all MCP resources on the server instance.

    Import and call each resource module's register() function here as they
    are implemented. This function is called once during server startup.
    """
    from src.mcp_server.resources.dian_codes import register as register_dian_codes

    register_dian_codes(server)


__all__ = ["register_all_resources"]
