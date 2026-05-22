"""
AdjustmentNoteService — nota de ajuste de documento soporte vía Factus API.

Endpoints:
  - POST /v2/support-document-adjustment-notes/validate   — crear nota de ajuste
  - GET  /v2/support-document-adjustment-notes            — listar notas de ajuste
  - GET  /v2/support-document-adjustment-notes/{id}       — obtener por ID de Factus
  - DELETE /v2/support-document-adjustment-notes/{id}     — eliminar
  - GET  /v2/support-document-adjustment-notes/{id}/pdf   — descargar PDF
  - GET  /v2/support-document-adjustment-notes/{id}/xml   — descargar XML
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import AdjustmentNoteCreate
from src.services.invoice_service import FactusApiError


class AdjustmentNoteService:
    """Business logic for support document adjustment notes (type 04) via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    # ──────────────────────────────────────────────────────────────────────────
    # CREATE — POST /v2/support-document-adjustment-notes/validate
    # ──────────────────────────────────────────────────────────────────────────

    async def create(self, data: AdjustmentNoteCreate) -> dict:
        """Create and validate an adjustment note via POST /v2/.../validate.

        Args:
            data: DTO con datos de la nota de ajuste.

        Returns:
            Respuesta completa de Factus.

        Raises:
            FactusApiError: Si la API devuelve error.
        """
        payload = {
            "reference_code": data.reference_code,
            "document": data.document or "04",
            "support_document_reference": data.support_document_reference,
            "provider": data.provider,
            "items": data.items,
            "observation": data.observation or "",
            "send_email": data.send_email,
        }

        response = await self._factus.post(
            "/v2/support-document-adjustment-notes/validate", json=payload
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
    # QUERY — GET /v2/support-document-adjustment-notes
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
            "/v2/support-document-adjustment-notes", params=params
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to list adjustment notes: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response.json()

    async def get_by_id(self, factus_id: int) -> Optional[dict]:
        """Get an adjustment note by its Factus-internal ID.

        Args:
            factus_id: ID interno de Factus.

        Returns:
            La nota de ajuste si existe, None si no.
        """
        response = await self._factus.get(
            f"/v2/support-document-adjustment-notes/{factus_id}"
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
    # DELETE — DELETE /v2/support-document-adjustment-notes/{id}
    # ──────────────────────────────────────────────────────────────────────────

    async def delete(self, factus_id: int) -> dict:
        """Delete an adjustment note by its Factus-internal ID.

        Args:
            factus_id: ID interno de Factus de la nota a eliminar.

        Returns:
            Respuesta de Factus confirmando la eliminación.
        """
        response = await self._factus.delete(
            f"/v2/support-document-adjustment-notes/{factus_id}"
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

    async def download_pdf(self, factus_id: int) -> httpx.Response:
        """Download the PDF representation of an adjustment note.

        Args:
            factus_id: ID interno de Factus.

        Returns:
            La respuesta HTTP con el contenido binario del PDF.
        """
        response = await self._factus.get(
            f"/v2/support-document-adjustment-notes/{factus_id}/pdf"
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download PDF: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response

    async def download_xml(self, factus_id: int) -> httpx.Response:
        """Download the XML representation of an adjustment note.

        Args:
            factus_id: ID interno de Factus.

        Returns:
            La respuesta HTTP con el contenido XML.
        """
        response = await self._factus.get(
            f"/v2/support-document-adjustment-notes/{factus_id}/xml"
        )
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to download XML: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        return response

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_body(response: Any) -> Any:
        try:
            return response.json()
        except Exception:
            return response.text
