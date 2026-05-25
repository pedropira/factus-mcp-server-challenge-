"""
InvoiceService — electronic invoice (bill) operations via Factus API v2.

Coordina con FactusClient para llamar a los endpoints reales de Factus:
  - POST /v2/bills/validate               — crear y validar factura ante DIAN
  - GET  /v2/bills                        — listar facturas
  - GET  /v2/bills/{number}               — obtener factura por número
  - DELETE /v2/bills/{reference_code}     — eliminar factura
  - GET  /v2/bills/{number}/pdf           — descargar PDF
  - GET  /v2/bills/{number}/xml           — descargar XML

NO persiste en DB local — la fuente de verdad es la API de Factus.
El caller (MCP tool) decide si quiere cachear localmente.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from decimal import Decimal
from typing import Any, Optional

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import InvoiceCreate
from src.schemas.models import Customer, Establishment, Product
from src.services.mappers import customer_to_factus_dict, product_to_factus_dict
from src.services.numbering_range_service import NumberingRangeService
from src.services.tax.withholding import calculate as calculate_withholdings
from src.services.validators import InvoiceValidator


class FactusApiError(Exception):
    """Error devuelto por la API de Factus.

    Attributes:
        message: Mensaje de error legible.
        status_code: Código HTTP de la respuesta.
        body: Cuerpo completo de la respuesta (útil para debug).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class InvoiceService:
    """Business logic for electronic invoice operations via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE — POST /v2/bills/validate
    # ──────────────────────────────────────────────────────────────────────────

    async def create(self, data: InvoiceCreate) -> dict:
        """Create and validate an electronic invoice via POST /v2/bills/validate.

        Steps:
          1. Build the Factus-compliant JSON payload from the DTO
          2. Auto-calculate totals (gross, tax, total) from items
          3. Send to Factus API
          4. Parse response and return the full API result

        Returns:
            El dict completo de la respuesta de Factus (status, message, data).

        Raises:
            FactusApiError: Si la API devuelve error HTTP.
        """
        payload = self._build_request(data)
        payload = self._enrich_with_totals(payload)

        response = await self._factus.post("/v2/bills/validate", json=payload)
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE WITH NUMBERING — Full Colombian business flow
    # ──────────────────────────────────────────────────────────────────────────

    async def create_with_numbering(
        self,
        data: InvoiceCreate,
        numbering_range_id: int,
        numbering_service: NumberingRangeService,
        customer: Optional[Customer] = None,
        establishment: Optional[Establishment] = None,
        products: Optional[list[Product]] = None,
    ) -> dict:
        """Create invoice with DIAN numbering, mapping, and tax calculation.

        Full Colombian business flow:
          1. Pre-validate payload
          2. Map Customer/Product models → Factus API dicts
          3. Get next available number from numbering range
          4. Auto-calculate withholding taxes (ReteRenta, ReteIVA, ReteICA, etc.)
          5. Calculate totals per item using actual tax rates
          6. Send to Factus API
          7. Return response

        Args:
            data: Invoice creation data.
            numbering_range_id: ID of the DIAN numbering range to use.
            numbering_service: NumberingRangeService instance.
            customer: Optional Customer model (if provided, maps to Factus dict).
            establishment: Optional Establishment model for customer mapping.
            products: Optional Product models list (if provided, maps to items dicts).

        Returns:
            Factus API response dict.

        Raises:
            ValueError: If validation fails or numbering range is exhausted.
            FactusApiError: If Factus API returns an error.
        """
        # 1. Build base payload
        payload = self._build_request(data)

        # 2. Map models if provided
        if customer is not None:
            payload["customer"] = customer_to_factus_dict(customer, establishment)

        if products is not None:
            mapped_items = []
            for i, prod in enumerate(products):
                qty = data.items[i].get("quantity", "1") if i < len(data.items) else "1"
                disc = data.items[i].get("discount_rate", "0.00") if i < len(data.items) else "0.00"
                mapped_items.append(product_to_factus_dict(prod, qty, disc))
            payload["items"] = mapped_items

        # 3. Validate before proceeding
        validation_errors = InvoiceValidator.validate(payload)
        if validation_errors:
            raise ValueError(
                "Invoice validation failed:\n  - "
                + "\n  - ".join(validation_errors)
            )

        # 4. Get next available number (validates range exists and is not exhausted)
        _ = await numbering_service.next_available(numbering_range_id)

        # 5. Calculate withholding taxes
        items = payload.get("items", [])
        gross_total = sum(
            Decimal(str(item.get("price", "0"))) * Decimal(str(item.get("quantity", "1")))
            * (Decimal("1") - Decimal(str(item.get("discount_rate", "0"))) / Decimal("100"))
            for item in items
        )
        withholding_map = calculate_withholdings(
            customer=payload.get("customer", {}),
            items=items,
            gross_total=gross_total,
            payment_details=payload.get("payment_details"),
        )

        # Embed withholding_taxes into each item
        for idx, wt_list in withholding_map.items():
            if idx < len(items) and wt_list:
                items[idx]["withholding_taxes"] = wt_list

        # 7. Calculate totals with per-item tax rates
        payload = self._enrich_with_totals(payload)

        # 8. Send to Factus
        response = await self._factus.post("/v2/bills/validate", json=payload)
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # QUERY — GET /v2/bills
    # ──────────────────────────────────────────────────────────────────────────

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        **filters: str,
    ) -> dict:
        """List invoices from Factus API.

        Args:
            limit: Máximo de resultados.
            offset: Desplazamiento para paginación.
            **filters: Filtros adicionales ej: reference_code=..., status=...

        Returns:
            La respuesta paginada de Factus.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for key, val in filters.items():
            params[f"filter[{key}]"] = val

        response = await self._factus.get("/v2/bills", params=params)
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    async def get_by_reference_code(self, code: str) -> Optional[dict]:
        """Find an invoice by its unique reference code.

        Returns:
            El invoice si existe, None si no.
        """
        result = await self.list(reference_code=code, limit=1)
        data = self._extract_list(result)
        return data[0] if data else None

    async def get_by_number(self, number: str) -> Optional[dict]:
        """Get an invoice by its Factus-issued number.

        Args:
            number: Número asignado por Factus (e.g. "SETP990003793").

        Returns:
            La factura si existe, None si no.
        """
        response = await self._factus.get(f"/v2/bills/{number}")
        await response.aread()

        if response.status_code == 404:
            return None
        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DELETE — DELETE /v2/bills/{reference_code}
    # ──────────────────────────────────────────────────────────────────────────

    async def delete(self, reference_code: str) -> dict:
        """Delete an invoice by its reference code.

        Args:
            reference_code: Código de referencia único de la factura.

        Returns:
            Respuesta de Factus confirmando la eliminación.
        """
        response = await self._factus.delete(f"/v2/bills/{reference_code}")
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DOWNLOAD — PDF / XML
    # ──────────────────────────────────────────────────────────────────────────

    async def download_pdf(self, number: str) -> dict:
        """Download the PDF representation of an invoice.

        Args:
            number: Número de la factura asignado por Factus.

        Returns:
            Dict con pdf_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/bills/{number}/download-pdf")
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    async def download_xml(self, number: str) -> dict:
        """Download the XML representation of an invoice.

        Args:
            number: Número de la factura asignado por Factus.

        Returns:
            Dict con xml_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/bills/{number}/download-xml")
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE — request builders
    # ──────────────────────────────────────────────────────────────────────────

    def _build_request(self, data: InvoiceCreate) -> dict:
        """Construye el body exacto que espera POST /v2/bills/validate.

        Basado en pruebas reales contra el sandbox (explore_factus_api.py).
        Incluye allowance_charges si están presentes en el DTO.
        """
        payload: dict[str, Any] = {
            "reference_code": data.reference_code,
            "document": data.document or "01",
            "operation_type": data.operation_type or "10",
            "observation": data.observation or "",
            "send_email": data.send_email,
            "payment_details": data.payment_details,
            "customer": data.customer,
            "items": data.items,
        }

        if data.allowance_charges:
            payload["allowance_charges"] = data.allowance_charges

        return payload

    def _enrich_with_totals(self, payload: dict) -> dict:
        """Delegates to shared enrich_with_totals."""
        from src.services.enrich import enrich_with_totals as _enrich
        return _enrich(payload)

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE — response helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_list(response: dict) -> list[dict]:
        """Extrae la lista de resultados de una respuesta paginada de Factus.

        La API envuelve los resultados en: data → data → [...]
        """
        try:
            return response["data"]["data"]
        except (KeyError, TypeError):
            return []

    @staticmethod
    def _build_error(response: Any) -> FactusApiError:
        """Construye un FactusApiError a partir de una respuesta HTTP fallida."""
        try:
            body = response.json()
            msg = body.get("message", response.reason_phrase)
        except Exception:
            body = response.text
            msg = response.reason_phrase
        return FactusApiError(
            message=str(msg),
            status_code=response.status_code,
            body=body,
        )
