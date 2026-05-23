"""Tests for MCP resource registration and content (DIAN codes + tax config).

Covers:
  - Resource registration (static + template)
  - All 9 DIAN categories return valid JSON
  - All 4 config resources return valid JSON with expected keys
  - Unknown category returns error response
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from .conftest import (
    EXPECTED_CONFIG_URIS,
    EXPECTED_DIAN_CATEGORIES,
    EXPECTED_RESOURCE_COUNT,
    EXPECTED_RESOURCE_TEMPLATE_COUNT,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# ═══════════════════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════════════════


class TestResourceRegistration:
    """Verify resources are registered correctly on the server."""

    @pytest.mark.asyncio
    async def test_static_resource_count(self, server: FastMCP) -> None:
        """Should register exactly 4 static config resources."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        resources = await server.list_resources()
        assert len(resources) == EXPECTED_RESOURCE_COUNT

    @pytest.mark.asyncio
    async def test_resource_template_count(self, server: FastMCP) -> None:
        """Should register exactly 1 URI template (factus://dian/{category})."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        templates = await server.list_resource_templates()
        assert len(templates) == EXPECTED_RESOURCE_TEMPLATE_COUNT

    @pytest.mark.asyncio
    async def test_dian_template_uri(self, server: FastMCP) -> None:
        """The URI template should be factus://dian/{category}."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        templates = await server.list_resource_templates()
        assert templates[0].uriTemplate == "factus://dian/{category}"

    @pytest.mark.asyncio
    async def test_static_resource_uris(self, server: FastMCP) -> None:
        """Static config resources should have correct URIs."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        resources = await server.list_resources()
        uris = sorted(str(r.uri) for r in resources)
        assert uris == sorted(EXPECTED_CONFIG_URIS)


# ═══════════════════════════════════════════════════════════════════════════
# DIAN code content
# ═══════════════════════════════════════════════════════════════════════════


class TestDianCodeContent:
    """Verify DIAN code resources return accurate data."""

    @pytest.fixture(autouse=True)
    def _register_resources(self, server: FastMCP) -> None:
        """Register resources before each test in this class."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        self._server = server

    @pytest.mark.asyncio
    async def test_all_dian_categories_return_content(self) -> None:
        """Every DIAN category should return valid non-empty JSON."""
        for category in EXPECTED_DIAN_CATEGORIES:
            uri = f"factus://dian/{category}"
            contents = await self._server.read_resource(uri)
            assert len(contents) == 1
            data = json.loads(contents[0].content)
            assert isinstance(data, dict)
            assert len(data) > 0, f"Empty data for category '{category}'"

    @pytest.mark.asyncio
    async def test_document_types_has_expected_keys(self) -> None:
        """document-types should contain known DIAN document types.

        The data is a name-to-code mapping, e.g. {"cédula": "13", "nit": "31"}.
        """
        contents = await self._server.read_resource("factus://dian/document-types")
        data = json.loads(contents[0].content)
        # DIAN document types include 'nit' and 'cédula de ciudadanía'
        keys_lower = {k.lower() for k in data}
        assert "nit" in keys_lower

    @pytest.mark.asyncio
    async def test_payment_forms_contado_credito(self) -> None:
        """payment-forms should include contado (1) and crédito (2).

        The data is a name-to-code mapping, e.g. {"contado": "1", "crédito": "2"}.
        """
        contents = await self._server.read_resource("factus://dian/payment-forms")
        data = json.loads(contents[0].content)
        keys_lower = {k.lower() for k in data}
        assert "contado" in keys_lower
        assert "crédito" in keys_lower or "credito" in keys_lower

    @pytest.mark.asyncio
    async def test_unknown_category_returns_error(self) -> None:
        """An unknown DIAN category should return an error with available list."""
        contents = await self._server.read_resource("factus://dian/unknown-category")
        data = json.loads(contents[0].content)
        assert "error" in data
        assert "available_categories" in data

    @pytest.mark.asyncio
    async def test_all_categories_are_json(self) -> None:
        """All DIAN resource responses must be valid JSON."""
        for category in EXPECTED_DIAN_CATEGORIES:
            contents = await self._server.read_resource(f"factus://dian/{category}")
            raw = contents[0].content
            # Should parse as JSON without error
            parsed = json.loads(raw)
            assert isinstance(parsed, dict)


# ═══════════════════════════════════════════════════════════════════════════
# Tax config content
# ═══════════════════════════════════════════════════════════════════════════


class TestTaxConfigContent:
    """Verify tax configuration resources return correct data."""

    @pytest.fixture(autouse=True)
    def _register_resources(self, server: FastMCP) -> None:
        """Register resources before each test in this class."""
        from src.mcp_server.resources import register_all_resources

        register_all_resources(server)
        self._server = server

    @pytest.mark.asyncio
    async def test_uvt_resource_has_uvt_field(self) -> None:
        """factus://config/uvt should contain a 'uvt' field."""
        contents = await self._server.read_resource("factus://config/uvt")
        data = json.loads(contents[0].content)
        assert "uvt" in data
        assert isinstance(data["uvt"], float) or isinstance(data["uvt"], int)

    @pytest.mark.asyncio
    async def test_tax_rates_has_iva_and_rete_renta(self) -> None:
        """factus://config/tax-rates should include IVA and ReteRenta."""
        contents = await self._server.read_resource("factus://config/tax-rates")
        data = json.loads(contents[0].content)
        assert "iva" in data
        assert "rete_renta" in data

    @pytest.mark.asyncio
    async def test_reteica_rates_has_rates(self) -> None:
        """factus://config/reteica-rates should contain a 'rates' dict."""
        contents = await self._server.read_resource("factus://config/reteica-rates")
        data = json.loads(contents[0].content)
        assert "rates" in data
        assert isinstance(data["rates"], dict)
        assert len(data["rates"]) > 0

    @pytest.mark.asyncio
    async def test_withholding_rules_has_all_types(self) -> None:
        """factus://config/withholding-rules should cover all 4 types."""
        contents = await self._server.read_resource("factus://config/withholding-rules")
        data = json.loads(contents[0].content)
        for key in ("reterenta", "reteiva", "reteica", "rete_gmf"):
            assert key in data, f"Missing '{key}' in withholding rules"

    @pytest.mark.asyncio
    async def test_all_config_resources_are_valid_json(self) -> None:
        """All config resources must return valid JSON."""
        for uri in EXPECTED_CONFIG_URIS:
            contents = await self._server.read_resource(uri)
            raw = contents[0].content
            parsed = json.loads(raw)
            assert isinstance(parsed, dict), f"Resource {uri} is not valid JSON"
