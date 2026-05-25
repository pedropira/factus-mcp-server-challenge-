"""
MCP tools for electronic invoice operations via Factus API.

All tools use FactusClient directly (no local DB) except
create_invoice_with_numbering which coordinates DB models + Factus API
for the full Colombian business flow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcp_server.schemas.tool_params import (
    CreateInvoiceParams,
    CreateInvoiceWithNumberingParams,
    DeleteInvoiceParams,
    DownloadInvoicePdfParams,
    DownloadInvoiceXmlParams,
    GetInvoiceByNumberParams,
    GetInvoiceByReferenceParams,
    ListInvoicesParams,
)
from src.mcp_server.tools._shared import error_body, json_safe, item_to_factus as _item_to_factus
from src.schemas.dto import InvoiceCreate
from src.services.invoice_service import InvoiceService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from src.mcp_server.main import ServerDeps


def register(server: FastMCP, deps: ServerDeps) -> None:
    """Register all invoice tools on the MCP server."""
    invoice_svc = InvoiceService(deps.factus)

    @server.tool()
    async def create_invoice(params: CreateInvoiceParams) -> dict:
        """Create an electronic invoice via Factus API (POST /v2/bills/validate).

        The customer and items are passed as raw dicts. Use this when you
        already have the Factus-format customer and item data. For the full
        Colombian flow with numbering ranges, use create_invoice_with_numbering.
        """
        try:
            data = InvoiceCreate(
                reference_code=params.reference_code,
                document=params.document,
                operation_type=params.operation_type,
                observation=params.observation or "",
                send_email=params.send_email,
                payment_details=[
                    json_safe(pd.model_dump()) for pd in params.payment_details
                ],
                customer=params.customer,
                items=[_item_to_factus(i) for i in params.items],
                allowance_charges=[
                    json_safe(ac.model_dump()) for ac in params.allowance_charges
                ]
                if params.allowance_charges
                else None,
            )
            result = await invoice_svc.create(data)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def create_invoice_with_numbering(
        params: CreateInvoiceWithNumberingParams,
    ) -> dict:
        """Create an electronic invoice with the full Colombian business flow.

        This tool:
        1. Fetches customer (and optional establishment) from local DB
        2. Maps them to Factus API format via mappers
        3. Gets the next available number from the numbering range
        4. Calculates withholding taxes automatically
        5. Sends the invoice to Factus for DIAN validation

        Use this when you have local customer and numbering range setup.
        """
        try:
            async with deps.get_session() as session:
                from src.services.customer_service import CustomerService

                customer_svc = CustomerService(session)
                customer = await customer_svc.get_by_id(params.customer_id)
                if customer is None:
                    return {
                        "success": False,
                        "error": f"Customer with id {params.customer_id} not found",
                    }

                establishment = None
                if params.establishment_id is not None:
                    from src.services.establishment_service import (
                        EstablishmentService,
                    )

                    est_svc = EstablishmentService(session)
                    establishment = await est_svc.get_by_id(
                        params.establishment_id
                    )

                from src.services.numbering_range_service import (
                    NumberingRangeService,
                )

                data = InvoiceCreate(
                    reference_code=params.reference_code,
                    observation=params.observation or "",
                    send_email=params.send_email,
                    payment_details=[
                        json_safe(pd.model_dump())
                        for pd in params.payment_details
                    ],
                    customer={},
                    items=[_item_to_factus(i) for i in params.items],
                    allowance_charges=[
                        json_safe(ac.model_dump())
                        for ac in params.allowance_charges
                    ]
                    if params.allowance_charges
                    else None,
                )

                numbering_svc = NumberingRangeService(session)
                result = await invoice_svc.create_with_numbering(
                    data=data,
                    numbering_range_id=params.numbering_range_id,
                    numbering_service=numbering_svc,
                    customer=customer,
                    establishment=establishment,
                )
                return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def list_invoices(params: ListInvoicesParams) -> dict:
        """List electronic invoices from Factus API with optional filters.

        Filters: status, reference_code. Pagination via offset/limit (max 100).
        """
        try:
            filters: dict[str, str] = {}
            if params.status is not None:
                filters["status"] = params.status
            if params.reference_code is not None:
                filters["reference_code"] = params.reference_code
            result = await invoice_svc.list(
                limit=params.limit,
                offset=params.offset,
                **filters,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def get_invoice_by_number(params: GetInvoiceByNumberParams) -> dict:
        """Get an electronic invoice by its Factus-assigned number.

        The number includes the prefix + consecutive (e.g. "SETP990003793").
        Use get_invoice_by_reference if you know your own reference code.
        """
        try:
            result = await invoice_svc.get_by_number(params.number)
            if result is None:
                return {
                    "success": False,
                    "error": f"Invoice '{params.number}' not found",
                }
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def get_invoice_by_reference(
        params: GetInvoiceByReferenceParams,
    ) -> dict:
        """Get an electronic invoice by its unique reference code.

        The reference code is what you set when creating the invoice.
        """
        try:
            result = await invoice_svc.get_by_reference_code(
                params.reference_code
            )
            if result is None:
                return {
                    "success": False,
                    "error": f"Invoice with reference '{params.reference_code}' not found",
                }
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def delete_invoice(params: DeleteInvoiceParams) -> dict:
        """Delete an electronic invoice by its reference code.

        Permanently removes the invoice from Factus. Use with caution.
        """
        try:
            result = await invoice_svc.delete(params.reference_code)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_invoice_pdf(params: DownloadInvoicePdfParams) -> dict:
        """Download an invoice PDF by its Factus-assigned number.

        Returns base64-encoded PDF content.
        """
        try:
            data = await invoice_svc.download_pdf(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("pdf_base_64_encoded", ""),
                    "filename": data.get("name", f"invoice_{params.number}.pdf"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}

    @server.tool()
    async def download_invoice_xml(params: DownloadInvoiceXmlParams) -> dict:
        """Download an invoice XML by its Factus-assigned number.

        Returns base64-encoded XML content.
        """
        try:
            data = await invoice_svc.download_xml(params.number)
            return {
                "success": True,
                "data": {
                    "content": data.get("xml_base_64_encoded", ""),
                    "filename": data.get("name", f"invoice_{params.number}.xml"),
                },
            }
        except Exception as e:
            return {"success": False, "error": error_body(e)}


__all__ = ["register"]
