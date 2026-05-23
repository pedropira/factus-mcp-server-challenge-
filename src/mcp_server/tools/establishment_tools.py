"""
MCP tools for establishment (issuer branch) CRUD operations.

All tools use the local database via EstablishmentService. Each tool handler
creates its own AsyncSession and disposes of it on completion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateEstablishmentParams,
    DeleteEstablishmentParams,
    GetEstablishmentParams,
    ListEstablishmentsParams,
    UpdateEstablishmentParams,
)
from src.schemas.dto import EstablishmentCreate, EstablishmentUpdate
from src.services.establishment_service import EstablishmentService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all establishment tools on the MCP server."""

    @server.tool()
    async def create_establishment(params: CreateEstablishmentParams) -> dict:
        """Create a new establishment (issuer branch) in the local database.

        Establishments represent the physical or legal branches of the
        company that issue documents. If there's only one establishment,
        it's set as default.
        """
        try:
            async with deps.get_session() as session:
                service = EstablishmentService(session)
                dto = EstablishmentCreate(**params.model_dump(exclude_none=True))
                establishment = await service.create(dto)
                return {"success": True, "data": establishment.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_establishment(params: GetEstablishmentParams) -> dict:
        """Get an establishment by its local database ID."""
        try:
            async with deps.get_session() as session:
                service = EstablishmentService(session)
                establishment = await service.get_by_id(params.id)
                if establishment is None:
                    return {
                        "success": False,
                        "error": f"Establishment with id {params.id} not found",
                    }
                return {"success": True, "data": establishment.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def list_establishments(params: ListEstablishmentsParams) -> dict:
        """List all establishments with pagination, sorted by name."""
        try:
            async with deps.get_session() as session:
                service = EstablishmentService(session)
                results = await service.list(params.offset, params.limit)
                return {
                    "success": True,
                    "data": [e.model_dump() for e in results],
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def update_establishment(params: UpdateEstablishmentParams) -> dict:
        """Update an existing establishment. Only provided fields are changed."""
        try:
            async with deps.get_session() as session:
                service = EstablishmentService(session)
                update_data = params.model_dump(exclude={"id"}, exclude_none=True)
                dto = EstablishmentUpdate(**update_data)
                establishment = await service.update(params.id, dto)
                return {"success": True, "data": establishment.model_dump()}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def delete_establishment(params: DeleteEstablishmentParams) -> dict:
        """Delete an establishment by its local database ID."""
        try:
            async with deps.get_session() as session:
                service = EstablishmentService(session)
                await service.delete(params.id)
                return {"success": True, "data": {"deleted_id": params.id}}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
