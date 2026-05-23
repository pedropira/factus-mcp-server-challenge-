"""
MCP tool for company information via Factus API.

Provides read-only access to the company profile associated with the
current Factus credentials (NIT, business name, address, tax info).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import GetCompanyInfoParams
from src.services.company_service import CompanyService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register the company info tool on the MCP server."""

    @server.tool()
    async def get_company_info(params: GetCompanyInfoParams) -> dict:
        """Get company information from Factus API.

        Returns the company profile: NIT, business name, address,
        municipality, fiscal responsibilities, etc. No parameters needed.
        """
        try:
            svc = CompanyService(deps.factus)
            result = await svc.get_info()
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
