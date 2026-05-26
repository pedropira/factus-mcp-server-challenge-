"""
MCP tools for electronic credit note operations via Factus API.

All tools use FactusClient directly (no local DB).
Credit notes use Factus-internal IDs for get/delete/download operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateCreditNoteParams,
    DeleteCreditNoteParams,
    DownloadCreditNotePdfParams,
    DownloadCreditNoteXmlParams,
    GetCreditNoteParams,
    ListCreditNotesParams,
)
from src.mcp_server.tools._shared import error_body, json_safe, item_to_factus
from src.schemas.dto import CreditNoteCreate
from src.services.credit_note_service import CreditNoteService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all credit note tools on the MCP server."""
    svc = CreditNoteService(deps.factus)

    @server.tool()
    async def create_credit_note(params: CreateCreditNoteParams) -> dict:
        """Create a credit note via Factus API (POST /v2/credit-notes).

        Credit notes correct existing invoices. The bill_number is
        the Factus-assigned number of the invoice being corrected.
        correction_concept_code: 1=devolución, 2=anulación, etc.

        The numbering_range_id is your LOCAL database ID — the tool
        automatically resolves it to the Factus API ID before sending.
        """
        try:
            # Resolver numbering_range_id local → Factus API ID
            factus_range_id: int = params.numbering_range_id
            async with deps.get_session() as session:
                from src.services.numbering_range_service import (
                    NumberingRangeService,
                )
                numbering_svc = NumberingRangeService(session=session)
                factus_range_id = await numbering_svc.get_factus_id(
                    params.numbering_range_id
                )

            data = CreditNoteCreate(
                reference_code=params.reference_code,
                correction_concept_code=params.correction_concept_code,
                observation=params.observation or "",
                send_email=params.send_email,
                bill_number=params.bill_number,
                numbering_range_id=factus_range_id,
                payment_details=[
                    json_safe(pd.model_dump()) for pd in params.payment_details
                ],
                customer=params.customer,
                items=[item_to_factus(i) for i in params.items],
            )
            result = await svc.create(data)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def list_credit_notes(params: ListCreditNotesParams) -> dict:
        """List credit notes from Factus API with optional filters.

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
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def get_credit_note(params: GetCreditNoteParams) -> dict:
        """Get a credit note by its Factus-internal ID.

        Use the factus_id returned by list_credit_notes or search via
        get_credit_note_by_reference instead.
        """
        try:
            result = await svc.get_by_id(params.factus_id)
            if result is None:
                return {
                    "success": False,
                    "error": f"Credit note with factus_id {params.factus_id} not found",
                }
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def delete_credit_note(params: DeleteCreditNoteParams) -> dict:
        """Delete a credit note by its Factus-internal ID.

        Permanently removes the credit note from Factus. Use with caution.
        """
        try:
            result = await svc.delete(params.factus_id)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_credit_note_pdf(
        params: DownloadCreditNotePdfParams,
    ) -> dict:
        """Download a credit note PDF by its Factus-assigned number.

        Returns base64-encoded PDF content.
        """
        try:
            data = await svc.download_pdf(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("pdf_base_64_encoded", ""),
                    "filename": data.get("name", f"credit_note_{params.number}.pdf"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_credit_note_xml(
        params: DownloadCreditNoteXmlParams,
    ) -> dict:
        """Download a credit note XML by its Factus-assigned number.

        Returns base64-encoded XML content.
        """
        try:
            data = await svc.download_xml(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("xml_base_64_encoded", ""),
                    "filename": data.get("name", f"credit_note_{params.number}.xml"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}


__all__ = ["register"]
