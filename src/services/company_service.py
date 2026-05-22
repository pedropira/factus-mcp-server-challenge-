"""
CompanyService — información de la empresa emisora vía Factus API.

Endpoint:
  - GET /v2/companies — datos de la compañía asociada a las credenciales
"""

from __future__ import annotations

from src.infrastructure.factus_client import FactusClient
from src.services.invoice_service import FactusApiError


class CompanyService:
    """Business logic for company info via Factus API."""

    def __init__(self, factus: FactusClient) -> None:
        self._factus = factus

    async def get_info(self) -> dict:
        """Obtiene la información de la empresa desde Factus API.

        Returns:
            Dict con datos de la empresa: NIT, razón social, dirección,
            municipio, responsabilidades fiscales, etc.
        """
        response = await self._factus.get("/v2/companies")
        await response.aread()

        if not response.is_success:
            raise FactusApiError(
                message=f"Failed to get company info: {response.reason_phrase}",
                status_code=response.status_code,
                body=self._safe_body(response),
            )

        data = response.json()
        # La API envuelve en { status, message, data: { ... } }
        return data.get("data", data)

    @staticmethod
    def _safe_body(response) -> str | dict:
        try:
            return response.json()
        except Exception:
            return response.text
