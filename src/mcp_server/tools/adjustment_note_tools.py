"""
MCP tools for adjustment note (Nota de Ajuste) operations via Factus API.

All tools use FactusClient directly (no local DB).
Adjustment notes use Factus-internal IDs for get/delete/download operations.
"""

from __future__ import annotations

import base64
from decimal import Decimal
from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateAdjustmentNoteParams,
    DeleteAdjustmentNoteParams,
    DownloadAdjustmentNotePdfParams,
    DownloadAdjustmentNoteXmlParams,
    GetAdjustmentNoteParams,
    ListAdjustmentNotesParams,
)
from src.schemas.dto import AdjustmentNoteCreate
from src.services.adjustment_note_service import AdjustmentNoteService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def _json_safe(d: dict) -> dict:
    """Convert Decimal values to strings for JSON serialization."""
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in d.items()}


def _item_to_factus(item: object) -> dict:
    """Convert _InvoiceItemInput to Factus API item dict with taxes array."""
    d = _json_safe(item.model_dump(exclude_none=True))
    d["taxes"] = [{"rate": item.tax_rate}]
    return d


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all adjustment note tools on the MCP server."""
    svc = AdjustmentNoteService(deps.factus)

    @server.tool()
    async def create_adjustment_note(
        params: CreateAdjustmentNoteParams,
    ) -> dict:
        """Create an adjustment note (Nota de Ajuste) via Factus API.

        Adjustment notes (type "04") correct existing support documents.
        The support_document_reference is the Factus-assigned number of
        the document being corrected.
        """
        try:
            data = AdjustmentNoteCreate(
                reference_code=params.reference_code,
                support_document_reference=params.support_document_reference,
                provider=params.provider,
                items=[_item_to_factus(i) for i in params.items],
                observation=params.observation or "",
                send_email=params.send_email,
            )
            result = await svc.create(data)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def list_adjustment_notes(
        params: ListAdjustmentNotesParams,
    ) -> dict:
        """List adjustment notes from Factus API with optional filters.

        Filters: status, reference_code. Pagination via offset/limit (max 100).
        The response includes factus_id values for get/delete/download tools.
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
            return {"success": False, "error": str(e)}

    @server.tool()
    async def get_adjustment_note(params: GetAdjustmentNoteParams) -> dict:
        """Get an adjustment note by its Factus-internal ID.

        Use the factus_id returned by list_adjustment_notes.
        """
        try:
            result = await svc.get_by_id(params.factus_id)
            if result is None:
                return {
                    "success": False,
                    "error": f"Adjustment note with factus_id {params.factus_id} not found",
                }
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def delete_adjustment_note(
        params: DeleteAdjustmentNoteParams,
    ) -> dict:
        """Delete an adjustment note by its Factus-internal ID.

        Permanently removes the adjustment note from Factus. Use with caution.
        """
        try:
            result = await svc.delete(params.factus_id)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def download_adjustment_note_pdf(
        params: DownloadAdjustmentNotePdfParams,
    ) -> dict:
        """Download an adjustment note PDF by its Factus-internal ID.

        Returns base64-encoded PDF content.
        """
        try:
            response = await svc.download_pdf(params.factus_id)
            content = base64.b64encode(response.content).decode()
            return {
                "success": True,
                "data": {
                    "content": content,
                    "content_type": response.headers.get(
                        "content-type", "application/pdf"
                    ),
                    "filename": f"adjustment_note_{params.factus_id}.pdf",
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool()
    async def download_adjustment_note_xml(
        params: DownloadAdjustmentNoteXmlParams,
    ) -> dict:
        """Download an adjustment note XML by its Factus-internal ID.

        Returns base64-encoded XML content.
        """
        try:
            response = await svc.download_xml(params.factus_id)
            content = base64.b64encode(response.content).decode()
            return {
                "success": True,
                "data": {
                    "content": content,
                    "content_type": response.headers.get(
                        "content-type", "application/xml"
                    ),
                    "filename": f"adjustment_note_{params.factus_id}.xml",
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = ["register"]
