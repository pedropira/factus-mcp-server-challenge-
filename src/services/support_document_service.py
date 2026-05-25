"""
SupportDocumentService — documento soporte electrónico vía Factus API.

Endpoints:
  - POST /v2/support-documents/validate         — crear documento soporte
  - GET  /v2/support-documents                  — listar documentos soporte
  - GET  /v2/support-documents/{number}         — obtener por número
  - DELETE /v2/support-documents/{reference_code} — eliminar
  - GET  /v2/support-documents/{number}/pdf     — descargar PDF
  - GET  /v2/support-documents/{number}/xml     — descargar XML
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import SupportDocumentCreate
from src.services.invoice_service import FactusApiError
from src.services.mappers import provider_to_factus_dict


class SupportDocumentService:
    """Business logic for support documents (type 03) via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE — POST /v2/support-documents/validate
    # ──────────────────────────────────────────────────────────────────────────

    async def create(self, data: SupportDocumentCreate) -> dict:
        """Create and validate a support document via POST /v2/support-documents/validate.

        Args:
            data: DTO con datos del documento soporte.

        Returns:
            Respuesta completa de Factus.

        Raises:
            FactusApiError: Si la API devuelve error.
        """
        payload = {
            "reference_code": data.reference_code,
            "document": data.document or "03",
            "provider": provider_to_factus_dict(data.provider),
            "items": data.items,
            "observation": data.observation or "",
            "send_email": data.send_email,
        }

        response = await self._factus.post("/v2/support-documents/validate", json=payload)
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Support document creation failed: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # QUERY — GET /v2/support-documents
    # ──────────────────────────────────────────────────────────────────────────

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        **filters: str,
    ) -> dict:
        """List support documents from Factus API.

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

        response = await self._factus.get("/v2/support-documents", params=params)
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to list support documents: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_number(self, number: str) -> Optional[dict]:
        """Get a support document by its Factus-issued number.

        Args:
            number: Número asignado por Factus (e.g. "SETP990003793").

        Returns:
            El documento si existe, None si no.
        """
        response = await self._factus.get(f"/v2/support-documents/{number}")
        await response.aread()

        if response.status_code == 404:
            return None
        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to get support document: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_reference_code(self, code: str) -> Optional[dict]:
        """Find a support document by its reference code."""
        result = await self.list(reference_code=code, limit=1)
        try:
            items = result["data"]["data"]
            return items[0] if items else None
        except (KeyError, IndexError):
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # DELETE — DELETE /v2/support-documents/{reference_code}
    # ──────────────────────────────────────────────────────────────────────────

    async def delete(self, reference_code: str) -> dict:
        """Delete a support document by its reference code.

        Args:
            reference_code: Código de referencia único del documento.

        Returns:
            Respuesta de Factus confirmando la eliminación.
        """
        response = await self._factus.delete(
            f"/v2/support-documents/{reference_code}"
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to delete support document: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    # ──────────────────────────────────────────────────────────────────────────
    # DOWNLOAD — PDF / XML
    # ──────────────────────────────────────────────────────────────────────────

    async def download_pdf(self, number: str) -> dict:
        """Download the PDF representation of a support document.

        Args:
            number: Número del documento asignado por Factus.

        Returns:
            Dict con pdf_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/support-documents/{number}/download-pdf")
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download PDF: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def download_xml(self, number: str) -> dict:
        """Download the XML representation of a support document.

        Args:
            number: Número del documento asignado por Factus.

        Returns:
            Dict con xml_base_64_encoded y filename.
        """
        response = await self._factus.get(f"/v2/support-documents/{number}/download-xml")
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
