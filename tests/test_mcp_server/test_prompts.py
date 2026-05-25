"""Tests for MCP prompt registration and content.

Covers:
  - All 9 prompts registered with correct names
  - Each prompt returns non-empty string content
  - Content contains expected sections and tool references
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .conftest import EXPECTED_PROMPT_COUNT, EXPECTED_PROMPT_NAMES

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# ═══════════════════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════════════════


class TestPromptRegistration:
    """Verify all prompts are registered on the server."""

    @pytest.mark.asyncio
    async def test_all_prompts_registered(self, server: FastMCP) -> None:
        """Should register exactly 9 prompts."""
        from src.mcp_server.prompts import register_all_prompts

        register_all_prompts(server)
        prompts = await server.list_prompts()
        assert len(prompts) == EXPECTED_PROMPT_COUNT

    @pytest.mark.asyncio
    async def test_prompt_names_match(self, server: FastMCP) -> None:
        """All prompt names should match the expected list."""
        from src.mcp_server.prompts import register_all_prompts

        register_all_prompts(server)
        prompts = await server.list_prompts()
        names = {p.name for p in prompts}
        assert names == set(EXPECTED_PROMPT_NAMES)

    @pytest.mark.asyncio
    async def test_prompt_descriptions_non_empty(self, server: FastMCP) -> None:
        """Each prompt should have a non-empty description."""
        from src.mcp_server.prompts import register_all_prompts

        register_all_prompts(server)
        prompts = await server.list_prompts()
        for p in prompts:
            assert p.description, f"Prompt '{p.name}' has empty description"


# ═══════════════════════════════════════════════════════════════════════════
# Content
# ═══════════════════════════════════════════════════════════════════════════


class TestPromptContent:
    """Verify each prompt returns meaningful content."""

    @pytest.fixture(autouse=True)
    def _register_prompts(self, server: FastMCP) -> None:
        """Register prompts before each test in this class."""
        from src.mcp_server.prompts import register_all_prompts

        register_all_prompts(server)
        self._server = server

    @pytest.mark.asyncio
    async def test_all_prompts_return_content(self) -> None:
        """Every prompt should return non-empty content via get_prompt()."""
        for name in EXPECTED_PROMPT_NAMES:
            result = await self._server.get_prompt(name)
            assert result is not None
            assert result.messages
            for msg in result.messages:
                assert msg.content is not None
                # TextContent should have text, EmbeddedResource should have resource
                if hasattr(msg.content, "text"):
                    assert len(msg.content.text) > 0, f"Prompt '{name}' has empty text"

    @pytest.mark.asyncio
    async def test_creation_guides_contain_paso_a_paso(self) -> None:
        """Each creation guide should contain step-by-step instructions."""
        guide_names = [
            "crear-factura-guia",
            "crear-nota-credito-guia",
            "crear-documento-soporte-guia",
            "crear-nota-ajuste-guia",
        ]
        for name in guide_names:
            result = await self._server.get_prompt(name)
            text = result.messages[0].content.text
            assert text.strip().startswith("#"), (
                f"Prompt '{name}' should start with a heading"
            )
            assert len(text) > 200, f"Prompt '{name}' seems too short"

    @pytest.mark.asyncio
    async def test_creation_guides_reference_tools(self) -> None:
        """Creation guides should reference actual MCP tool names."""
        guide_names = [
            ("crear-factura-guia", "search_customers"),
            ("crear-nota-credito-guia", "correction_concept_code"),
            ("crear-documento-soporte-guia", "create_support_document"),
            ("crear-nota-ajuste-guia", "support_document_number"),
        ]
        for name, expected_reference in guide_names:
            result = await self._server.get_prompt(name)
            text = result.messages[0].content.text
            assert expected_reference in text, (
                f"Prompt '{name}' should reference '{expected_reference}'"
            )

    @pytest.mark.asyncio
    async def test_analyzers_contain_analysis_content(self) -> None:
        """Analytical prompts should contain substantial content."""
        analyzer_names = [
            "analizar-obligaciones-tributarias",
            "analizar-factura-antes-enviar",
            "comparar-tipos-documento",
            "analizar-codigos-dian",
            "simular-retenciones",
        ]
        for name in analyzer_names:
            result = await self._server.get_prompt(name)
            text = result.messages[0].content.text
            assert len(text) > 150, f"Analytical prompt '{name}' seems too short"

    @pytest.mark.asyncio
    async def test_analizadores_reference_resources(self) -> None:
        """Analytical prompts should reference factus:// resources."""
        result = await self._server.get_prompt("analizar-obligaciones-tributarias")
        text = result.messages[0].content.text
        assert "factus://" in text
        assert "get_company_info" in text

    @pytest.mark.asyncio
    async def test_comparar_tipos_documento_has_table(self) -> None:
        """The comparison prompt should include a markdown table."""
        result = await self._server.get_prompt("comparar-tipos-documento")
        text = result.messages[0].content.text
        assert "|" in text  # markdown table separator
        assert "Factura" in text
        assert "Nota Crédito" in text
        assert "Documento Soporte" in text
