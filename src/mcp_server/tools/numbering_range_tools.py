"""
MCP tools for DIAN numbering range operations.

Numbering ranges represent the resolution numbers authorized by DIAN
for each document type. Tools support local CRUD and syncing from Factus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateNumberingRangeParams,
    FetchNumberingRangesFromFactusParams,
    GetActiveNumberingRangesParams,
    GetDefaultNumberingRangeParams,
)
from src.schemas.dto import NumberingRangeCreate
from src.services.numbering_range_service import NumberingRangeService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all numbering range tools on the MCP server."""

    @server.tool()
    async def create_numbering_range(params: CreateNumberingRangeParams) -> dict:
        """Register a new DIAN numbering range in the local database.

        This records the resolution received from DIAN. Each range has:
        - document_type_id: 21=factura, 22=nota crédito, 24=doc. soporte
        - prefix: e.g. "SETP", "FAC"
        - from_number / to_number: the authorized range
        """
        try:
            async with deps.get_session() as session:
                service = NumberingRangeService(session=session)
                dto = NumberingRangeCreate(**params.model_dump(exclude_none=True))
                nr = await service.create(dto)
                return {"success": True, "data": nr.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_active_numbering_ranges(
        params: GetActiveNumberingRangesParams,
    ) -> dict:
        """Get all active numbering ranges, optionally filtered by document type.

        Active ranges are those marked as is_active=True. Use this before
        creating invoices to see which ranges are available.
        """
        try:
            async with deps.get_session() as session:
                service = NumberingRangeService(session=session)
                results = await service.get_active(params.document_type_id)
                return {
                    "success": True,
                    "data": [nr.model_dump() for nr in results],
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_default_numbering_range(
        params: GetDefaultNumberingRangeParams,
    ) -> dict:
        """Get the first active numbering range for a document type.

        This is the recommended range to use when creating invoices
        with the full Colombian flow (create_invoice_with_numbering).
        """
        try:
            async with deps.get_session() as session:
                service = NumberingRangeService(session=session)
                nr = await service.get_default_for_document_type(
                    params.document_type_id
                )
                if nr is None:
                    return {
                        "success": False,
                        "error": (
                            f"No active numbering range found for "
                            f"document type {params.document_type_id}"
                        ),
                    }
                return {"success": True, "data": nr.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def fetch_numbering_ranges_from_factus(
        params: FetchNumberingRangesFromFactusParams,
    ) -> dict:
        """Fetch numbering ranges from Factus API and sync to local database.

        This calls GET /v2/numbering-ranges on Factus API and stores or
        updates each range in the local database. Use this when setting up
        a new environment or after getting a new DIAN resolution.
        """
        try:
            async with deps.get_session() as session:
                service = NumberingRangeService(
                    session=session, factus=deps.factus
                )
                # The fetch_from_factus method syncs ranges from API to DB
                results = await service.fetch_from_factus()
                return {
                    "success": True,
                    "data": {
                        "count": len(results),
                        "ranges": results,
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
