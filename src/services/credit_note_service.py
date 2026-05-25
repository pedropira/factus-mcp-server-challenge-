"""
CreditNoteService — notas crédito electrónicas vía Factus API.

Endpoints:
  - POST /v2/credit-notes                        — crear nota crédito
  - GET  /v2/credit-notes                        — listar notas crédito
  - GET  /v2/credit-notes/{id}                   — obtener nota crédito por ID
  - DELETE /v2/credit-notes/{id}                 — eliminar nota crédito
  - GET  /v2/credit-notes/{id}/pdf               — descargar PDF
  - GET  /v2/credit-notes/{id}/xml               — descargar XML
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import CreditNoteCreate
from src.services.invoice_service import FactusApiError


class CreditNoteService:
    """Business logic for electronic credit notes via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE — POST /v2/credit-notes
    # ──────────────────────────────────────────────────────────────────────────

    async def create(self, data: CreditNoteCreate) -> dict:
        """Create a credit note via POST /v2/credit-notes.

        Args:
            data: DTO con datos de la nota crédito.

        Returns:
            Respuesta completa de Factus.

        Raises:
            FactusApiError: Si la API devuelve error.
        """
        payload = {
            "reference_code": data.reference_code,
            "document": data.document or "02",
            "operation_type": data.operation_type or "20",
            "correction_concept_code": data.correction_concept_code,
            "observation": data.observation or "",
            "send_email": data.send_email,
            "invoice_reference": data.invoice_reference,
            "payment_details": data.payment_details,
            "customer": data.customer,
            "items": data.items,
        }

        response = await self._factus.post("/v2/credit-notes", json=payload)
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Credit note creation failed: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # QUERY — GET /v2/credit-notes
    # ──────────────────────────────────────────────────────────────────────────

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        **filters: str,
    ) -> dict:
        """List credit notes from Factus API.

        Args:
            limit: Máximo de resultados.
            offset: Desplazamiento.
            **filters: Filtros adicionales.

        Returns:
            Respuesta paginada de Factus.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for key, val in filters.items():
            params[f"filter[{key}]"] = val

        response = await self._factus.get("/v2/credit-notes", params=params)
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to list credit notes: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_reference_code(self, code: str) -> Optional[dict]:
        """Find a credit note by reference code."""
        result = await self.list(reference_code=code, limit=1)
        try:
            items = result["data"]["data"]
            return items[0] if items else None
        except (KeyError, IndexError):
            return None

    async def get_by_id(self, factus_id: str) -> Optional[dict]:
        """Get a credit note by its Factus-internal ID.

        Args:
            factus_id: ID interno de Factus.

        Returns:
            La nota crédito si existe, None si no.
        """
        response = await self._factus.get(f"/v2/credit-notes/{factus_id}")
        await response.aread()

        if response.status_code == 404:
            return None
        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to get credit note: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DELETE — DELETE /v2/credit-notes/{id}
    # ──────────────────────────────────────────────────────────────────────────

    async def delete(self, factus_id: str) -> dict:
        """Delete a credit note by its Factus-internal ID.

        Args:
            factus_id: ID interno de Factus de la nota a eliminar.

        Returns:
            Respuesta de Factus confirmando la eliminación.
        """
        response = await self._factus.delete(f"/v2/credit-notes/{factus_id}")
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to delete credit note: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DOWNLOAD — PDF / XML
    # ──────────────────────────────────────────────────────────────────────────

    async def download_pdf(self, number: str) -> dict:
        """Download the PDF representation of a credit note.

        Args:
            number: Número de la nota crédito asignado por Factus.

        Returns:
            Dict con pdf_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/credit-notes/{number}/download-pdf")
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download PDF: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def download_xml(self, number: str) -> dict:
        """Download the XML representation of a credit note.

        Args:
            number: Número de la nota crédito asignado por Factus.

        Returns:
            Dict con xml_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/credit-notes/{number}/download-xml")
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download XML: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_body(response: Any) -> Any:
        try:
            return response.json()
        except Exception:
            return response.text
