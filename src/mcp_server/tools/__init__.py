"""
MCP tool registrations for the Factus server.

Each submodule exports a `register(server, deps)` function that registers
its tools on the MCP server instance.

Usage in main.py:
    from src.mcp_server.tools import register_all_tools
    register_all_tools(server, deps)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register_all_tools(server: FastMCP, deps: ServerDeps) -> None:
    """Register all MCP tools on the server instance.

    Import and call each domain's register() function here as they are
    implemented. This function is called once during server startup.
    """
    from src.mcp_server.tools.customer_tools import register as register_customers
    from src.mcp_server.tools.establishment_tools import (
        register as register_establishments,
    )
    from src.mcp_server.tools.numbering_range_tools import (
        register as register_numbering_ranges,
    )
    from src.mcp_server.tools.product_tools import register as register_products

    from src.mcp_server.tools.adjustment_note_tools import (
        register as register_adjustment_notes,
    )
    from src.mcp_server.tools.company_tool import register as register_company
    from src.mcp_server.tools.credit_note_tools import (
        register as register_credit_notes,
    )
    from src.mcp_server.tools.invoice_tools import register as register_invoices
    from src.mcp_server.tools.support_doc_tools import (
        register as register_support_docs,
    )

    register_customers(server, deps)
    register_products(server, deps)
    register_establishments(server, deps)
    register_numbering_ranges(server, deps)
    register_invoices(server, deps)
    register_credit_notes(server, deps)
    register_support_docs(server, deps)
    register_adjustment_notes(server, deps)
    register_company(server, deps)


__all__ = ["register_all_tools"]
