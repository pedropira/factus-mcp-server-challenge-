"""
MCP tools for product catalog CRUD operations.

All tools use the local database via ProductService. Each tool handler
creates its own AsyncSession and disposes of it on completion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateProductParams,
    DeleteProductParams,
    GetProductByCodeParams,
    GetProductParams,
    SearchProductsParams,
    UpdateProductParams,
)
from src.schemas.dto import ProductCreate, ProductUpdate
from src.services.product_service import ProductService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all product catalog tools on the MCP server."""

    @server.tool()
    async def create_product(params: CreateProductParams) -> dict:
        """Create a new product in the local catalog.

        Products are used as invoice line items. Key fields:
        - code_reference: unique product code
        - tax_rate: IVA rate as string (e.g. "19.00")
        - unit_measure_id: Factus unit measure ID (70=unidad)
        - standard_code_id: 1=contribuyente, 2=UNSPSC
        - tribute_id: 1=IVA, 2=INC
        """
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                dto = ProductCreate(**params.model_dump(exclude_none=True))
                product = await service.create(dto)
                return {"success": True, "data": product.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_product(params: GetProductParams) -> dict:
        """Get a product by its local database ID."""
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                product = await service.get_by_id(params.id)
                if product is None:
                    return {
                        "success": False,
                        "error": f"Product with id {params.id} not found",
                    }
                return {"success": True, "data": product.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_product_by_code(params: GetProductByCodeParams) -> dict:
        """Get a product by its unique reference code.

        The code_reference is the same value used in invoice items.
        """
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                product = await service.get_by_code(params.code_reference)
                if product is None:
                    return {
                        "success": False,
                        "error": (
                            f"Product with code '{params.code_reference}' not found"
                        ),
                    }
                return {"success": True, "data": product.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def search_products(params: SearchProductsParams) -> dict:
        """Search products by name or code reference.

        Use for finding products to add to invoices. Returns matching
        products sorted by relevance.
        """
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                results = await service.search(params.query, params.limit)
                return {
                    "success": True,
                    "data": [p.model_dump() for p in results],
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def update_product(params: UpdateProductParams) -> dict:
        """Update an existing product. Only provided fields are changed.

        Use this to fix pricing, tax rates, or product names.
        """
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                update_data = params.model_dump(exclude={"id"}, exclude_none=True)
                dto = ProductUpdate(**update_data)
                product = await service.update(params.id, dto)
                return {"success": True, "data": product.model_dump()}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def delete_product(params: DeleteProductParams) -> dict:
        """Delete a product by its local database ID."""
        try:
            async with deps.get_session() as session:
                service = ProductService(session)
                await service.delete(params.id)
                return {"success": True, "data": {"deleted_id": params.id}}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
