"""
MCP tools for customer (purchaser) CRUD operations.

All tools use the local database via CustomerService. Each tool handler
creates its own AsyncSession and disposes of it on completion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateCustomerParams,
    DeleteCustomerParams,
    GetCustomerParams,
    SearchCustomersParams,
    UpdateCustomerParams,
)
from src.schemas.dto import CustomerCreate, CustomerUpdate
from src.services.customer_service import CustomerService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all customer tools on the MCP server."""

    @server.tool()
    async def create_customer(params: CreateCustomerParams) -> dict:
        """Create a new customer (purchaser) in the local database.

        All fields map to the Factus customer model. Use DIAN codes for
        identification_document_id (1-11) and municipality_id (11001, etc.).
        """
        try:
            async with deps.get_session() as session:
                service = CustomerService(session)
                dto = CustomerCreate(
                    **params.model_dump(exclude_none=True)
                )
                customer = await service.create(dto)
                return {"success": True, "data": customer.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_customer(params: GetCustomerParams) -> dict:
        """Get a customer by their local database ID.

        Returns the full customer record or an error if not found.
        """
        try:
            async with deps.get_session() as session:
                service = CustomerService(session)
                customer = await service.get_by_id(params.id)
                if customer is None:
                    return {
                        "success": False,
                        "error": f"Customer with id {params.id} not found",
                    }
                return {"success": True, "data": customer.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def search_customers(params: SearchCustomersParams) -> dict:
        """Search customers by identification, name, company, or email.

        Performs a LIKE-based search across multiple fields. Use '*' for
        wildcards or plain text for partial matches.
        """
        try:
            async with deps.get_session() as session:
                service = CustomerService(session)
                results = await service.search(params.query, params.limit)
                return {
                    "success": True,
                    "data": [c.model_dump() for c in results],
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def update_customer(params: UpdateCustomerParams) -> dict:
        """Update an existing customer. Only provided fields are changed.

        Use this to correct customer data, change email, address, etc.
        The customer ID is required; all other fields are optional.
        """
        try:
            async with deps.get_session() as session:
                service = CustomerService(session)
                update_data = params.model_dump(exclude={"id"}, exclude_none=True)
                dto = CustomerUpdate(**update_data)
                customer = await service.update(params.id, dto)
                return {"success": True, "data": customer.model_dump()}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def delete_customer(params: DeleteCustomerParams) -> dict:
        """Delete a customer by their local database ID.

        This is a hard delete. Invoices referencing this customer may
        prevent deletion depending on referential integrity.
        """
        try:
            async with deps.get_session() as session:
                service = CustomerService(session)
                await service.delete(params.id)
                return {"success": True, "data": {"deleted_id": params.id}}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
