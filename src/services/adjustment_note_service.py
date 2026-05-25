"""
AdjustmentNoteService — nota de ajuste de documento soporte vía Factus API.

Endpoints:
  - POST /v2/adjustment-notes/validate                  — crear nota de ajuste
  - GET  /v2/adjustment-notes                           — listar notas de ajuste
  - GET  /v2/adjustment-notes/{number}                  — obtener por número de documento
  - DELETE /v1/adjustment-notes/reference/{code}        — eliminar por reference_code
  - GET  /v2/adjustment-notes/{number}/download-pdf     — descargar PDF
  - GET  /v2/adjustment-notes/{number}/download-xml     — descargar XML
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import AdjustmentNoteCreate
from src.services.invoice_service import FactusApiError
from src.services.mappers import provider_to_factus_dict


class AdjustmentNoteService:
    """Business logic for support document adjustment notes (type 04) via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE — POST /v2/adjustment-notes/validate
    # ──────────────────────────────────────────────────────────────────────────

    async def create(self, data: AdjustmentNoteCreate) -> dict:
        """Create and validate an adjustment note via POST /v2/adjustment-notes/validate.

        Args:
            data: DTO con datos de la nota de ajuste.

        Returns:
            Respuesta completa de Factus.

        Raises:
            FactusApiError: Si la API devuelve error.
        """
        payload: dict[str, Any] = {
            "reference_code": data.reference_code,
            "support_document_number": data.support_document_number,
            "correction_concept_code": data.correction_concept_code,
            "payment_details": data.payment_details,
            "provider": provider_to_factus_dict(data.provider),
            "items": data.items,
            "observation": data.observation or "",
        }
        if data.created_time is not None:
            payload["created_time"] = data.created_time
        if data.numbering_range_id is not None:
            payload["numbering_range_id"] = data.numbering_range_id
        if data.cash_rounding_amount is not None:
            payload["cash_rounding_amount"] = data.cash_rounding_amount

        response = await self._factus.post(
            "/v2/adjustment-notes/validate", json=payload
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Adjustment note creation failed: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # QUERY — GET /v2/adjustment-notes
    # ──────────────────────────────────────────────────────────────────────────

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        **filters: str,
    ) -> dict:
        """List adjustment notes from Factus API.

        Args:
            limit: Máximo de resultados.
            offset: Desplazamiento para paginación.
            **filters: Filtros: status, reference_code, document_number,
                       from_date, to_date.

        Returns:
            Respuesta paginada de Factus.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for key, val in filters.items():
            params[f"filter[{key}]"] = val

        response = await self._factus.get(
            "/v2/adjustment-notes", params=params
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to list adjustment notes: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_number(self, number: str) -> Optional[dict]:
        """Get an adjustment note by its document number.

        Args:
            number: Número de documento de Factus.

        Returns:
            La nota de ajuste si existe, None si no.
        """
        response = await self._factus.get(
            f"/v2/adjustment-notes/{number}"
        )
        await response.aread()

        if response.status_code == 404:
            return None
        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to get adjustment note: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_reference_code(self, code: str) -> Optional[dict]:
        """Find an adjustment note by its reference code."""
        result = await self.list(reference_code=code, limit=1)
        try:
            items = result["data"]["data"]
            return items[0] if items else None
        except (KeyError, IndexError):
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # DELETE — DELETE /v1/adjustment-notes/reference/{reference_code}
    # ──────────────────────────────────────────────────────────────────────────

    async def delete(self, reference_code: str) -> dict:
        """Delete an adjustment note by its reference code.

        Args:
            reference_code: Código de referencia de la nota a eliminar.

        Returns:
            Respuesta de Factus confirmando la eliminación.
        """
        response = await self._factus.delete(
            f"/v1/adjustment-notes/reference/{reference_code}"
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to delete adjustment note: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DOWNLOAD — PDF / XML
    # ──────────────────────────────────────────────────────────────────────────

    async def download_pdf(self, number: str) -> dict:
        """Download the PDF representation of an adjustment note.

        Args:
            number: Número de documento de Factus.

        Returns:
            Dict con pdf_base_64_encoded y filename.
        """
        response = await self._factus.get(
            f"/v2/adjustment-notes/{number}/download-pdf"
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download PDF: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def download_xml(self, number: str) -> dict:
        """Download the XML representation of an adjustment note.

        Args:
            number: Número de documento de Factus.

        Returns:
            Dict con xml_base_64_encoded y filename.
        """
        response = await self._factus.get(
            f"/v2/adjustment-notes/{number}/download-xml"
        )
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
