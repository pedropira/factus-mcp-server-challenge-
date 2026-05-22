"""
Tests para FactusAuth y FactusClient.

Usa httpx.MockTransport para simular las respuestas del endpoint /oauth/token
y verificar:
  1. Primera request → login automático (POST /oauth/token con grant_type=password)
  2. Segunda request → reutiliza token cacheado (sin llamar a /oauth/token)
  3. Token expirado → refresh automático (POST /oauth/token con grant_type=refresh_token)
  4. Concurrencia → solo un login simultáneo (asyncio.Lock / double-checked lock)
"""

import asyncio
import json
import time

import httpx
import pytest

from src.core.config import Settings
from src.infrastructure.factus_client import FactusAuth, FactusClient


# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_settings(**overrides) -> Settings:
    """Crea un Settings válido para testing."""
    defaults = {
        "ENV": "sandbox",
        "FACTUS_CLIENT_ID": "test-client-id",
        "FACTUS_CLIENT_SECRET": "test-client-secret",
        "FACTUS_USERNAME": "test@example.com",
        "FACTUS_PASSWORD": "test-password",
        "MCP_EVALUATION_KEY": "test-key",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _token_response(
    access_token: str = "access-123",
    refresh_token: str = "refresh-456",
    expires_in: int = 3600,
) -> httpx.Response:
    """Genera una respuesta mock de /oauth/token."""
    return httpx.Response(
        200,
        json={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "token_type": "Bearer",
        },
    )


# ─── Tests ──────────────────────────────────────────────────────────────────


class TestFactusAuth:
    """Tests para el flujo de autenticación transparente."""

    @pytest.fixture
    def settings(self):
        return _make_settings()

    async def test_first_request_triggers_login(self, settings):
        """
        La PRIMERA request a la API debe disparar un POST /oauth/token
        con grant_type=password para obtener un token inicial.
        """
        token_requests = []

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                # Capturamos el body del login para verificar grant_type
                body = dict(
                    item.split("=")
                    for item in request.content.decode().split("&")
                )
                token_requests.append(body)
                return _token_response()
            # Request normal de la API
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(mock_handler)
        auth = FactusAuth(settings)

        async with httpx.AsyncClient(
            transport=transport, base_url=auth.base_url, auth=auth
        ) as client:
            response = await client.get("/api/test")

        assert response.status_code == 200
        assert len(token_requests) == 1
        assert token_requests[0]["grant_type"] == "password"
        assert token_requests[0]["username"] == "test%40example.com"

    async def test_cached_token_reused_on_second_request(self, settings):
        """
        La SEGUNDA request debe reutilizar el token cacheado
        y NO disparar otro POST /oauth/token.
        """
        token_call_count = 0

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal token_call_count
            if request.url.path == "/oauth/token":
                token_call_count += 1
                return _token_response()
            # Verificamos que el header Authorization tiene el token
            assert request.headers.get("Authorization") == "Bearer access-123"
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(mock_handler)
        auth = FactusAuth(settings)

        async with httpx.AsyncClient(
            transport=transport, base_url=auth.base_url, auth=auth
        ) as client:
            await client.get("/api/test1")
            await client.get("/api/test2")

        # Solo una llamada a /oauth/token (el login inicial)
        assert token_call_count == 1

    async def test_expired_token_triggers_refresh(self, settings):
        """
        Si el token está expirado, la siguiente request debe disparar
        un POST /oauth/token con grant_type=refresh_token.
        """
        token_requests = []

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                body = dict(
                    item.split("=")
                    for item in request.content.decode().split("&")
                )
                token_requests.append(body)
                # Primer login: token que expira en 1 segundo
                if len(token_requests) == 1:
                    return _token_response(
                        access_token="access-first",
                        expires_in=1,
                    )
                # Refresh: token nuevo
                return _token_response(
                    access_token="access-refreshed",
                    refresh_token="refresh-new",
                )
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(mock_handler)
        auth = FactusAuth(settings)

        async with httpx.AsyncClient(
            transport=transport, base_url=auth.base_url, auth=auth
        ) as client:
            # Primera request: login
            await client.get("/api/test1")
            assert len(token_requests) == 1
            assert token_requests[0]["grant_type"] == "password"

            # Esperamos a que expire el token
            await asyncio.sleep(1.1)

            # Segunda request: debe hacer refresh
            await client.get("/api/test2")
            assert len(token_requests) == 2
            assert token_requests[1]["grant_type"] == "refresh_token"
            assert token_requests[1]["refresh_token"] == "refresh-456"

    async def test_concurrent_requests_single_login(self, settings):
        """
        Si múltiples requests concurrentes encuentran el token expirado,
        solo UNA debe disparar el login. Las demás deben esperar y reutilizar
        el token obtenido (double-checked lock pattern).
        """
        token_call_count = 0
        login_delay = 0.2  # Simular latencia de red en /oauth/token

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal token_call_count
            if request.url.path == "/oauth/token":
                token_call_count += 1
                await asyncio.sleep(login_delay)
                return _token_response()
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(mock_handler)
        auth = FactusAuth(settings)

        async with httpx.AsyncClient(
            transport=transport, base_url=auth.base_url, auth=auth
        ) as client:
            # Lanzamos 5 requests concurrentes — todas deberían ver token vacío
            tasks = [client.get(f"/api/test{i}") for i in range(5)]
            responses = await asyncio.gather(*tasks)

        # TODAS las responses deben ser 200
        for r in responses:
            assert r.status_code == 200

        # Pero solo UNA llamada a /oauth/token (el lock protege el rest)
        assert token_call_count == 1

    async def test_auth_header_injected_correctly(self, settings):
        """
        Verificar que el header Authorization: Bearer <token> se inyecta
        correctamente en cada request saliente.
        """
        captured_headers = []

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                return _token_response(access_token="my-token-abc")
            captured_headers.append(request.headers.get("Authorization"))
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(mock_handler)
        auth = FactusAuth(settings)

        async with httpx.AsyncClient(
            transport=transport, base_url=auth.base_url, auth=auth
        ) as client:
            await client.get("/api/invoices")

        assert captured_headers == ["Bearer my-token-abc"]

    async def test_sandbox_vs_production_base_url(self):
        """
        Verificar que la base_url cambia según ENV=sandbox o ENV=production.
        """
        sandbox_settings = _make_settings(ENV="sandbox")
        prod_settings = _make_settings(ENV="production")

        sandbox_auth = FactusAuth(sandbox_settings)
        prod_auth = FactusAuth(prod_settings)

        assert "sandbox" in sandbox_auth.base_url
        assert "sandbox" not in prod_auth.base_url


class TestFactusClient:
    """Tests para el wrapper de alto nivel FactusClient."""

    @pytest.fixture
    def settings(self):
        return _make_settings()

    async def test_client_makes_authenticated_requests(self, settings):
        """
        FactusClient debe enviar requests autenticadas usando FactusAuth.
        """
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                return _token_response()
            assert "Authorization" in request.headers
            return httpx.Response(200, json={"data": [1, 2, 3]})

        transport = httpx.MockTransport(mock_handler)
        client = FactusClient(settings, transport=transport)

        async with client:
            response = await client.get("/api/invoices")

        assert response.status_code == 200
        assert response.json() == {"data": [1, 2, 3]}

    async def test_client_post_with_json_body(self, settings):
        """
        FactusClient.post() debe enviar JSON body correctamente.
        """
        captured_body = {}

        async def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_body
            if request.url.path == "/oauth/token":
                return _token_response()
            captured_body = json.loads(request.content.decode())
            return httpx.Response(201, json={"id": "inv-001"})

        transport = httpx.MockTransport(mock_handler)
        client = FactusClient(settings, transport=transport)

        payload = {"customer": "John", "total": 100}
        async with client:
            response = await client.post("/api/invoices", json=payload)

        assert response.status_code == 201
        assert captured_body == payload

    async def test_client_context_manager(self, settings):
        """
        FactusClient debe funcionar como context manager async.
        """
        async def mock_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                return _token_response()
            return httpx.Response(200)

        transport = httpx.MockTransport(mock_handler)
        client = FactusClient(settings, transport=transport)

        async with client as c:
            assert c is client
            response = await c.get("/api/health")
            assert response.status_code == 200
