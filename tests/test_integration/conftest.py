"""
Fixtures compartidos para tests de integración contra sandbox de Factus.

Todas las fixtures skipean si las credenciales de sandbox no están configuradas,
para que los tests no fallen en entornos sin .env completo.

IMPORTANTE: Las fixtures de clientes usan scope='function' para evitar conflictos
con el event loop scope de pytest-asyncio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from src.core.config import Settings
    from src.infrastructure.factus_client import FactusClient


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Load settings from .env, skip integration tests if missing credentials."""
    from src.core.config import Settings

    try:
        s = Settings(
            _env_file=".env",
            _env_file_encoding="utf-8",
        )
        # Verify at least the required fields are non-empty
        if not s.FACTUS_CLIENT_ID or not s.FACTUS_CLIENT_SECRET:
            pytest.skip("FACTUS_CLIENT_ID or FACTUS_CLIENT_SECRET not set in .env")
        if not s.FACTUS_USERNAME or not s.FACTUS_PASSWORD:
            pytest.skip("FACTUS_USERNAME or FACTUS_PASSWORD not set in .env")
        if s.ENV != "sandbox":
            pytest.skip("ENV must be 'sandbox' for integration tests")
        return s
    except Exception as e:
        pytest.skip(f"Cannot load settings for integration tests: {e}")


@pytest.fixture
async def factus_client(settings: Settings) -> FactusClient:
    """Create a real FactusClient connected to sandbox.

    Cada test obtiene su propio cliente para evitar problemas de event loop
    scope con pytest-asyncio.
    """
    from src.infrastructure.factus_client import FactusClient

    async with FactusClient(settings) as client:
        yield client


@pytest.fixture
async def unauth_client(settings: Settings) -> httpx.AsyncClient:
    """Create a raw httpx client (without FactusAuth) for direct API access.

    Useful for testing the auth flow independently.
    """
    from src.infrastructure.factus_client import _BASE_URLS

    base_url = _BASE_URLS.get(settings.ENV, _BASE_URLS["sandbox"])
    async with httpx.AsyncClient(base_url=base_url) as client:
        yield client
