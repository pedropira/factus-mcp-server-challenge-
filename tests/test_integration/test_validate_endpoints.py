"""
Integration tests for Factus POST validate endpoints against sandbox.

Verifica que los endpoints POST existen (no devuelven 404), incluso si
el payload es inválido. Esto confirma que las rutas son correctas.
El sandbox debe devolver 422 (payload inválido) en lugar de 404 (ruta
inexistente), lo que valida la corrección de rutas que hicimos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.infrastructure.factus_client import FactusClient

pytestmark = pytest.mark.integration


class TestValidateEndpoints:
    """Pruebas de endpoints POST validate.

    Enviamos payload mínimo (seguramente inválido) para verificar que
    la RUTA existe (responde 422) vs no existe (404).
    """

    MINIMAL_PAYLOAD: dict = {
        "reference_code": "TEST-000000",
        "provider": {"identification": "0000000000"},
        "items": [{"code_reference": "X", "name": "Test", "quantity": "1", "price": "0"}],
    }

    async def test_invoice_validate(self, factus_client: FactusClient) -> None:
        """POST /v2/bills/validate — debe existir (no 404)."""
        response = await factus_client.post(
            "/v2/bills/validate", json=self.MINIMAL_PAYLOAD
        )
        await response.aread()

        # Si la ruta es correcta → 422 (payload inválido)
        # Si la ruta es incorrecta → 404
        assert response.status_code != 404, (
            f"POST /v2/bills/validate devolvió 404 — ruta incorrecta: "
            f"{response.text[:200]}"
        )

    async def test_credit_note_validate(self, factus_client: FactusClient) -> None:
        """POST /v2/credit-notes — debe existir (no 404)."""
        response = await factus_client.post(
            "/v2/credit-notes", json=self.MINIMAL_PAYLOAD
        )
        await response.aread()

        assert response.status_code != 404, (
            f"POST /v2/credit-notes devolvió 404 — ruta incorrecta: "
            f"{response.text[:200]}"
        )

    async def test_support_document_validate(self, factus_client: FactusClient) -> None:
        """POST /v2/support-documents/validate — debe existir (no 404)."""
        response = await factus_client.post(
            "/v2/support-documents/validate", json=self.MINIMAL_PAYLOAD
        )
        await response.aread()

        assert response.status_code != 404, (
            f"POST /v2/support-documents/validate devolvió 404 — ruta incorrecta: "
            f"{response.text[:200]}"
        )

    async def test_adjustment_note_validate(self, factus_client: FactusClient) -> None:
        """POST /v2/adjustment-notes/validate — ENDPOINT CRÍTICO.

        Este es el endpoint que acabamos de corregir. Debe existir.
        """
        response = await factus_client.post(
            "/v2/adjustment-notes/validate", json={
                "reference_code": "TEST-AN-000000",
                "support_document_number": "XXXXX",
                "correction_concept_code": "1",
                "payment_details": [{"payment_form": "1", "payment_method_code": "10", "amount": "0"}],
                "provider": {"identification": "0000000000"},
                "items": [{"code_reference": "X", "name": "Test", "quantity": "1", "price": "0"}],
            }
        )
        await response.aread()

        assert response.status_code != 404, (
            f"POST /v2/adjustment-notes/validate devolvió 404 — "
            f"la ruta corregida sigue siendo incorrecta: {response.text[:200]}"
        )

    async def test_old_adjustment_note_path_returns_404(
        self, factus_client: FactusClient
    ) -> None:
        """POST /v2/support-document-adjustment-notes/validate — RUTA ANTIGUA.

        Verifica que la ruta antigua (incorrecta) SÍ devuelve 404,
        confirmando que el fix era necesario.
        """
        response = await factus_client.post(
            "/v2/support-document-adjustment-notes/validate",
            json=self.MINIMAL_PAYLOAD,
        )
        await response.aread()

        assert response.status_code == 404, (
            f"La ruta antigua NO devolvió 404 (status {response.status_code}) — "
            f"quizás Factus mantiene ambas rutas"
        )
