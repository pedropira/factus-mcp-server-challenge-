"""
Integration tests for Factus API read-only endpoints against sandbox.

Verifica que los endpoints GET funcionan con autenticación real.
Los tests usan el cliente autenticado via fixture 'factus_client'.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.infrastructure.factus_client import FactusClient

pytestmark = pytest.mark.integration


class TestReadEndpoints:
    """Pruebas de endpoints GET de solo lectura."""

    async def test_list_companies(self, factus_client: FactusClient) -> None:
        """GET /v2/companies — debe devolver datos de la compañía."""
        response = await factus_client.get("/v2/companies")
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/companies falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        assert "data" in data, f"Respuesta sin campo 'data': {list(data.keys())}"

    async def test_list_numbering_ranges(self, factus_client: FactusClient) -> None:
        """GET /v2/numbering-ranges — debe devolver rangos activos."""
        response = await factus_client.get(
            "/v2/numbering-ranges", params={"filter[is_active]": 1}
        )
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/numbering-ranges falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        # Puede estar vacío si no hay rangos configurados, pero la estructura debe ser válida
        assert "data" in data

    async def test_list_invoices(self, factus_client: FactusClient) -> None:
        """GET /v2/bills — lista de facturas (puede estar vacía)."""
        response = await factus_client.get(
            "/v2/bills", params={"limit": 5, "offset": 0}
        )
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/bills falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        assert "data" in data

    async def test_list_credit_notes(self, factus_client: FactusClient) -> None:
        """GET /v2/credit-notes — lista de notas crédito (puede estar vacía)."""
        response = await factus_client.get(
            "/v2/credit-notes", params={"limit": 5, "offset": 0}
        )
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/credit-notes falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        assert "data" in data

    async def test_list_support_documents(self, factus_client: FactusClient) -> None:
        """GET /v2/support-documents — lista de documentos soporte."""
        response = await factus_client.get(
            "/v2/support-documents", params={"limit": 5, "offset": 0}
        )
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/support-documents falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        assert "data" in data

    async def test_list_adjustment_notes(self, factus_client: FactusClient) -> None:
        """GET /v2/adjustment-notes — lista de notas de ajuste.

        Este es el test CRÍTICO — valida que el fix de endpoints funcione.
        """
        response = await factus_client.get(
            "/v2/adjustment-notes", params={"limit": 5, "offset": 0}
        )
        await response.aread()

        assert response.status_code == 200, (
            f"GET /v2/adjustment-notes falló: {response.status_code} {response.text[:200]}"
        )
        data = response.json()
        assert "data" in data
