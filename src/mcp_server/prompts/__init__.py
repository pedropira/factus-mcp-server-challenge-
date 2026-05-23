"""
MCP prompt registrations for the Factus server.

Each submodule exports a `register(server)` function that registers
its prompt templates on the MCP server.

Usage in main.py:
    from src.mcp_server.prompts import register_all_prompts
    register_all_prompts(server)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all_prompts(server: FastMCP) -> None:
    """Register all MCP prompts on the server instance.

    Import and call each prompt module's register() function here as they
    are implemented. This function is called once during server startup.
    """
    from src.mcp_server.prompts.creation_guides import register as register_guides
    from src.mcp_server.prompts.analyzers import register as register_analyzers

    register_guides(server)
    register_analyzers(server)


__all__ = ["register_all_prompts"]
