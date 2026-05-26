"""
MCP tools for support document (Documento Soporte) operations via Factus API.

All tools use FactusClient directly (no local DB).
Support documents use the Factus-assigned number and reference code for
get/delete/download operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateSupportDocumentParams,
    DeleteSupportDocumentParams,
    DownloadSupportDocumentPdfParams,
    DownloadSupportDocumentXmlParams,
    GetSupportDocumentParams,
    ListSupportDocumentsParams,
)
from src.mcp_server.tools._shared import error_body, item_to_factus
from src.schemas.dto import SupportDocumentCreate
from src.services.support_document_service import SupportDocumentService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all support document tools on the MCP server."""
    svc = SupportDocumentService(deps.factus)

    @server.tool()
    async def create_support_document(
        params: CreateSupportDocumentParams,
    ) -> dict:
        """Create a support document (Documento Soporte) via Factus API.

        Documentos soporte (type "03") are used for transactions with
        suppliers who do not issue electronic invoices. The provider dict
        should use the same structure as a customer in Factus format.
        """
        try:
            data = SupportDocumentCreate(
                reference_code=params.reference_code,
                payment_details=[p.model_dump() for p in params.payment_details],
                provider=params.provider,
                items=[item_to_factus(i) for i in params.items],
                observation=params.observation or "",
                send_email=params.send_email,
            )
            result = await svc.create(data)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def list_support_documents(
        params: ListSupportDocumentsParams,
    ) -> dict:
        """List support documents from Factus API with optional filters.

        Filters: status, reference_code. Pagination via offset/limit (max 100).
        """
        try:
            filters: dict[str, str] = {}
            if params.status is not None:
                filters["status"] = params.status
            if params.reference_code is not None:
                filters["reference_code"] = params.reference_code
            result = await svc.list(
                limit=params.limit,
                offset=params.offset,
                **filters,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def get_support_document(params: GetSupportDocumentParams) -> dict:
        """Get a support document by its Factus-assigned number.

        The number includes prefix + consecutive (e.g. "SETP990003793").
        """
        try:
            result = await svc.get_by_number(params.number)
            if result is None:
                return {
                    "success": False,
                    "error": f"Support document '{params.number}' not found",
                }
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def delete_support_document(
        params: DeleteSupportDocumentParams,
    ) -> dict:
        """Delete a support document by its reference code.

        Permanently removes the document from Factus. Use with caution.
        """
        try:
            result = await svc.delete(params.reference_code)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_support_document_pdf(
        params: DownloadSupportDocumentPdfParams,
    ) -> dict:
        """Download a support document PDF by its Factus-assigned number.

        Returns base64-encoded PDF content.
        """
        try:
            data = await svc.download_pdf(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("pdf_base_64_encoded", ""),
                    "filename": data.get("name", f"support_doc_{params.number}.pdf"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_support_document_xml(
        params: DownloadSupportDocumentXmlParams,
    ) -> dict:
        """Download a support document XML by its Factus-assigned number.

        Returns base64-encoded XML content.
        """
        try:
            data = await svc.download_xml(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("xml_base_64_encoded", ""),
                    "filename": data.get("name", f"support_doc_{params.number}.xml"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}


__all__ = ["register"]
