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

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import InvoiceCreate


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

    async def download_pdf(self, number: str) -> httpx.Response:
        """Download the PDF representation of an invoice.

        Args:
            number: Número de la factura asignado por Factus.

        Returns:
            La respuesta HTTP con el contenido binario del PDF.
        """
        response = await self._factus.get(f"/v2/bills/{number}/pdf")
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response

    async def download_xml(self, number: str) -> httpx.Response:
        """Download the XML representation of an invoice.

        Args:
            number: Número de la factura asignado por Factus.

        Returns:
            La respuesta HTTP con el contenido XML.
        """
        response = await self._factus.get(f"/v2/bills/{number}/xml")
        await response.aread()

        if not response.is_success:
            raise self._build_error(response)

        return response

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE — request builders
    # ──────────────────────────────────────────────────────────────────────────

    def _build_request(self, data: InvoiceCreate) -> dict:
        """Construye el body exacto que espera POST /v2/bills/validate.

        Basado en pruebas reales contra el sandbox (explore_factus_api.py).
        """
        return {
            "reference_code": data.reference_code,
            "document": data.document or "01",
            "operation_type": data.operation_type or "10",
            "observation": data.observation or "",
            "send_email": data.send_email,
            "payment_details": data.payment_details,
            "customer": data.customer,
            "items": data.items,
        }

    @staticmethod
    def _enrich_with_totals(payload: dict) -> dict:
        """Calcula y asigna el total de paga basado en items.

        Fórmula por item:
            neto = price * quantity * (1 - discount_rate/100)
            iva  = neto * 0.19  (si IVA 19%)
            total_item = neto + iva

        El total del pago es la suma de total_item de todos los items.
        """
        items = payload.get("items", [])
        gross = 0.0
        for item in items:
            qty = float(item.get("quantity", 1))
            price = float(item.get("price", 0))
            disc = float(item.get("discount_rate", 0))
            net = price * qty * (1 - disc / 100)
            gross += net

        tax_rate = 0.19  # asumimos IVA 19% como default
        tax = gross * tax_rate
        total = gross + tax

        details = payload.get("payment_details", [])
        if details:
            details[0]["amount"] = f"{total:.2f}"

        return payload

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
