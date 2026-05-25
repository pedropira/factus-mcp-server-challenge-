"""
Integration tests for the Factus OAuth2 authentication flow against sandbox.

Verifica que el login con credenciales reales funcione y que el token
se cachee correctamente para requests subsecuentes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.core.config import Settings
    from src.infrastructure.factus_client import FactusClient


pytestmark = pytest.mark.integration


class TestFactusAuth:
    """Pruebas de autenticación contra sandbox real."""

    async def test_login_success(self, factus_client: FactusClient) -> None:
        """El login obtiene un token válido y lo cachea."""
        auth = factus_client.auth

        # Forzar un login haciendo una request autenticada
        response = await factus_client.get("/v2/companies")
        await response.aread()

        assert response.status_code == 200, (
            f"Auth falló: {response.status_code} {response.text[:200]}"
        )
        # Verificar que el token se cacheó
        assert auth._access_token is not None, "No se cacheó el access_token"
        assert auth._refresh_token is not None, "No se cacheó el refresh_token"
        assert auth._token_is_valid, "El token debería ser válido"

    async def test_token_caching(self, factus_client: FactusClient) -> None:
        """La segunda request reusa el token cacheado."""
        auth = factus_client.auth

        # Primera request — hace login y cachea el token
        response1 = await factus_client.get("/v2/companies")
        await response1.aread()
        assert response1.status_code == 200
        cached_token = auth._access_token
        assert cached_token is not None, "El login debería haber cacheado un token"

        # Segunda request — debe reusar el mismo token sin hacer otro login
        response2 = await factus_client.get("/v2/companies")
        await response2.aread()
        assert response2.status_code == 200
        assert auth._access_token == cached_token, (
            "El token cambió — se hizo un login innecesario"
        )

    async def test_reauth_on_token_expiry(self, factus_client: FactusClient) -> None:
        """Cuando el token expira, se refresca automáticamente."""
        auth = factus_client.auth

        # Forzar expiración del token
        auth._expires_at = 0.0
        old_token = auth._access_token

        response = await factus_client.get("/v2/companies")
        await response.aread()

        assert response.status_code == 200
        # Debería tener un token nuevo (refresheado o nuevo login)
        assert auth._access_token is not None
        assert auth._token_is_valid
