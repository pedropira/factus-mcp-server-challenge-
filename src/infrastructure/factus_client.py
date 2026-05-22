"""
Cliente HTTP asíncrono para la API de Factus.

Implementa autenticación OAuth2 transparente con:
  - Login on-demand (grant_type=password) en la primera request
  - Cache de token en memoria
  - Refresh automático cuando el token expira (grant_type=refresh_token)
  - Double-checked lock pattern con asyncio.Lock para seguridad concurrente

El flujo de auth usa el mecanismo nativo de httpx.Auth: yield de requests
intermedias que httpx envía por el mismo transport, sin crear clients internos.
"""

from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator

import httpx

from src.core.config import Settings


__all__ = [
    "FactusAuth",
    "FactusAuthError",
    "FactusClient",
]


# ─── URLs base por entorno ──────────────────────────────────────────────────

_BASE_URLS: dict[str, str] = {
    "sandbox": "https://api-sandbox.factus.com.co",
    "production": "https://api.factus.com.co",
}


# ─── Excepciones ────────────────────────────────────────────────────────────


class FactusAuthError(Exception):
    """Error durante el flujo de autenticación con la API de Factus.

    Se eleva cuando el login o refresh de token falla (credenciales inválidas,
    token revocado, error de red no recuperable, etc.).
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


# ─── Auth transparente ──────────────────────────────────────────────────────


class FactusAuth(httpx.Auth):
    """
    Autenticación transparente OAuth2 para httpx.

    Intercepta cada request saliente y:
      1. Si no hay token → login con grant_type=password
      2. Si el token está expirado → refresh con grant_type=refresh_token
      3. Si el token es válido → inyecta el header Authorization: Bearer

    Usa double-checked lock pattern para evitar que múltiples requests
    concurrentes disparen logins simultáneos.

    El mecanismo funciona con yield: cuando el auth flow necesita un token,
    yield-ea una request de token a httpx, que la envía por el mismo transport
    y devuelve la response. Así evitamos recursión infinita y no necesitamos
    un client separado.

    Ejemplo:
        auth = FactusAuth(settings)
        async with httpx.AsyncClient(auth=auth, base_url=auth.base_url) as client:
            response = await client.get("/api/invoices")
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = _BASE_URLS.get(settings.ENV, _BASE_URLS["sandbox"])

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    # ── Token state management ───────────────────────────────────────────

    @property
    def _token_is_valid(self) -> bool:
        """Verifica si el token actual es válido y no ha expirado."""
        return (
            self._access_token is not None
            and time.monotonic() < self._expires_at
        )

    def _store_token(self, data: dict) -> None:
        """Almacena el token y calcula el tiempo de expiración.

        El refresh_token se conserva si la respuesta no incluye uno nuevo
        (comportamiento común en muchos OAuth2 providers).
        """
        self._access_token = data["access_token"]
        if "refresh_token" in data and data["refresh_token"] is not None:
            self._refresh_token = data["refresh_token"]
        # Restamos 30 segundos como margen de seguridad contra clock skew
        expires_in = data.get("expires_in", 3600)
        self._expires_at = time.monotonic() + max(expires_in - 30, 0)

    # ── Request builders ─────────────────────────────────────────────────

    def _build_login_request(self) -> httpx.Request:
        """Construye la request de login (grant_type=password)."""
        return httpx.Request(
            "POST",
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "password",
                "client_id": self.settings.FACTUS_CLIENT_ID,
                "client_secret": self.settings.FACTUS_CLIENT_SECRET,
                "username": self.settings.FACTUS_USERNAME,
                "password": self.settings.FACTUS_PASSWORD,
            },
        )

    def _build_refresh_request(self) -> httpx.Request:
        """Construye la request de refresh (grant_type=refresh_token)."""
        return httpx.Request(
            "POST",
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.settings.FACTUS_CLIENT_ID,
                "client_secret": self.settings.FACTUS_CLIENT_SECRET,
                "refresh_token": self._refresh_token,
            },
        )

    # ── Auth flow ────────────────────────────────────────────────────────

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """
        Flujo de autenticación invocado por httpx antes de cada request.

        Usa double-checked lock pattern:
          1. Check rápido sin lock (fast path para requests con token válido)
          2. Si no hay token válido → acquire lock
          3. Re-check dentro del lock (otro coroutine pudo haberlo resuelto)
          4. Si sigue inválido → yield request de token, recibir response
          5. Inyectar header Authorization en la request original
          6. Yield request original

        NOTA: el yield dentro de este método es parte del protocolo de httpx:
        httpx consume el Request que yield-eamos, lo envía, y nos devuelve la
        Response como valor del yield. Por eso NO podemos extraer esta lógica
        a métodos separados — el yield solo funciona dentro de este generator.
        """
        # Fast path: token válido, no necesitamos lock
        if not self._token_is_valid:
            async with self._lock:
                # Double-check: otro coroutine pudo haber obtenido el token
                if not self._token_is_valid:
                    if self._refresh_token is not None:
                        # Intentar refresh primero
                        token_response = yield self._build_refresh_request()
                        # httpx 0.28+ → streaming, hay que leer el body
                        await token_response.aread()

                        if token_response.status_code == 200:
                            self._store_token(token_response.json())
                        else:
                            # Refresh falló → fallback a login completo
                            token_response = yield self._build_login_request()
                            await token_response.aread()
                            if token_response.status_code != 200:
                                raise FactusAuthError(
                                    f"Login failed with status "
                                    f"{token_response.status_code}: "
                                    f"{token_response.text}",
                                    status_code=token_response.status_code,
                                )
                            self._store_token(token_response.json())
                    else:
                        # Primera vez: login con password
                        token_response = yield self._build_login_request()
                        await token_response.aread()
                        if token_response.status_code != 200:
                            raise FactusAuthError(
                                f"Login failed with status "
                                f"{token_response.status_code}: "
                                f"{token_response.text}",
                                status_code=token_response.status_code,
                            )
                        self._store_token(token_response.json())

        request.headers["Authorization"] = f"Bearer {self._access_token}"
        yield request


# ─── Cliente de alto nivel ─────────────────────────────────────────────────


class FactusClient:
    """
    Cliente HTTP de alto nivel para la API de Factus.

    Envuelve httpx.AsyncClient con FactusAuth integrado.
    Diseñado para usarse como context manager async.

    Ejemplo:
        settings = Settings()
        async with FactusClient(settings) as client:
            invoices = await client.get("/api/invoices")
            invoice = await client.post("/api/invoices", json={...})
    """

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._auth = FactusAuth(settings)
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        """URL base de la API de Factus según el entorno (sandbox/production)."""
        return self._auth.base_url

    @property
    def auth(self) -> FactusAuth:
        """Instancia de FactusAuth utilizada para autenticación."""
        return self._auth

    async def __aenter__(self) -> FactusClient:
        self._client = httpx.AsyncClient(
            base_url=self._auth.base_url,
            auth=self._auth,
            transport=self._transport,
        )
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client is not None:
            await self._client.__aexit__(*args)
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "FactusClient must be used as async context manager: "
                "'async with client: ...'"
            )
        return self._client

    async def get(self, url: str, **kwargs: object) -> httpx.Response:
        """Ejecuta un GET autenticado contra la API de Factus."""
        return await self._ensure_client().get(url, **kwargs)

    async def post(self, url: str, **kwargs: object) -> httpx.Response:
        """Ejecuta un POST autenticado contra la API de Factus."""
        return await self._ensure_client().post(url, **kwargs)

    async def put(self, url: str, **kwargs: object) -> httpx.Response:
        """Ejecuta un PUT autenticado contra la API de Factus."""
        return await self._ensure_client().put(url, **kwargs)

    async def delete(self, url: str, **kwargs: object) -> httpx.Response:
        """Ejecuta un DELETE autenticado contra la API de Factus."""
        return await self._ensure_client().delete(url, **kwargs)
