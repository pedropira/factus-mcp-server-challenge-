"""
Tests for SupportDocumentService — documentos soporte vía Factus API.

Verifica:
- Construcción correcta del payload para POST /v2/support-documents/validate
- Parseo de respuestas de Factus
- Listado con filtros
- Búsqueda por número y reference_code
- Eliminación por reference_code
- Descarga de PDF/XML
- Manejo de errores HTTP
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import SupportDocumentCreate
from src.services.invoice_service import FactusApiError
from src.services.support_document_service import SupportDocumentService


@pytest.fixture
def mock_factus() -> MagicMock:
    factus = MagicMock(spec=FactusClient)
    factus.post = AsyncMock()
    factus.get = AsyncMock()
    factus.delete = AsyncMock()
    return factus


@pytest.fixture
def service(mock_factus: MagicMock) -> SupportDocumentService:
    return SupportDocumentService(mock_factus)


@pytest.fixture
def sample_create_data() -> SupportDocumentCreate:
    return SupportDocumentCreate(
        reference_code="SD-TEST-001",
        payment_details=[
            {
                "payment_method_code": "10",
                "payment_form": "1",
            },
        ],
        provider={
            "identification_document_code": "31",
            "identification": "900123456",
            "dv": "8",
            "company": "Proveedor de prueba S.A.S.",
            "names": "Proveedor de prueba S.A.S.",
            "address": "Calle 123 # 45-67",
            "email": "proveedor@example.com",
            "phone": "3001234567",
            "legal_organization_code": "1",
            "tribute_code": "01",
            "municipality_code": "11001",
            "country_code": "Co",
        },
        items=[
            {
                "code_reference": "ITEM-001",
                "name": "Item de prueba A",
                "quantity": "2.00",
                "price": "25000.00",
                "unit_measure_code": "94",
                "standard_code": "999",
                "taxes": [{"code": "01", "rate": "19.00"}],
            },
        ],
    )


@pytest.fixture
def factus_success_response() -> httpx.Response:
    return httpx.Response(
        201,
        json={
            "status": "Created",
            "message": "Documento soporte registrado y validado con exito",
            "data": {
                "reference_code": "SD-TEST-001",
                "number": "SETP990003795",
                "document_type": {"code": "03", "name": "Documento Soporte"},
                "is_validated": True,
                "validated_at": "21-05-2026 07:32:15 PM",
            },
        },
    )


# ─── CREATE ──────────────────────────────────────────────────────────────


class TestSupportDocumentCreate:
    async def test_creates_support_document_successfully(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
        sample_create_data: SupportDocumentCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """Happy path: envia a Factus, parsea respuesta, retorna dict."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create(sample_create_data)

        # Verify endpoint and payload
        mock_factus.post.assert_awaited_once()
        mock_factus.post.assert_awaited_once_with(
            "/v2/support-documents/validate", json={
                "reference_code": "SD-TEST-001",
                "document": "03",
                "payment_details": sample_create_data.payment_details,
                "provider": sample_create_data.provider,
                "items": sample_create_data.items,
                "observation": "",
                "send_email": False,
            },
        )

        # Verify response
        assert result["status"] == "Created"
        assert result["data"]["number"] == "SETP990003795"
        assert result["data"]["is_validated"] is True

    async def test_send_email_defaults_to_false(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
        sample_create_data: SupportDocumentCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """send_email debe ser False por defecto."""
        mock_factus.post.return_value = factus_success_response
        await service.create(sample_create_data)

        call_kwargs = mock_factus.post.await_args.kwargs
        assert call_kwargs["json"]["send_email"] is False

    async def test_raises_on_factus_error(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
        sample_create_data: SupportDocumentCreate,
    ) -> None:
        """HTTP error de Factus -> FactusApiError."""
        mock_factus.post.return_value = httpx.Response(
            422,
            json={
                "message": "El proveedor no es valido",
                "errors": [{"field": "provider", "detail": "Invalid identification"}],
            },
        )

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 422
        assert "proveedor" in str(exc.value.body).lower()

    async def test_handles_http_error_without_json_body(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
        sample_create_data: SupportDocumentCreate,
    ) -> None:
        """Error sin JSON body -> no crash."""
        mock_factus.post.return_value = httpx.Response(500, text="Internal Server Error")

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 500


# ─── QUERY ───────────────────────────────────────────────────────────────


class TestSupportDocumentQueries:
    async def test_list_support_documents(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/support-documents con parametros."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "data": [
                        {"number": "SETP990003795", "reference_code": "SD-TEST-001"},
                        {"number": "SETP990003796", "reference_code": "SD-TEST-002"},
                    ]
                },
            },
        )

        result = await service.list(limit=10, status="1")

        mock_factus.get.assert_awaited_once_with(
            "/v2/support-documents", params={"limit": 10, "offset": 0, "filter[status]": "1"}
        )
        assert len(result["data"]["data"]) == 2

    async def test_get_by_number_found(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por numero -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "number": "SETP990003795",
                    "reference_code": "SD-TEST-001",
                    "is_validated": True,
                },
            },
        )

        result = await service.get_by_number("SETP990003795")
        assert result is not None
        assert result["data"]["number"] == "SETP990003795"
        assert result["data"]["reference_code"] == "SD-TEST-001"

    async def test_get_by_number_not_found(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por numero -> 404 -> None."""
        mock_factus.get.return_value = httpx.Response(404, json={"message": "Not found"})

        result = await service.get_by_number("NO-EXISTE")
        assert result is None

    async def test_get_by_reference_code_found(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {"data": [{"number": "SETP990003795", "reference_code": "SD-TEST-001"}]},
            },
        )

        result = await service.get_by_reference_code("SD-TEST-001")
        assert result is not None
        assert result["reference_code"] == "SD-TEST-001"

    async def test_get_by_reference_code_not_found(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code -> no encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={"status": "OK", "message": "Solicitud exitosa", "data": {"data": []}},
        )

        result = await service.get_by_reference_code("NO-EXISTE")
        assert result is None


# ─── DELETE ──────────────────────────────────────────────────────────────


class TestSupportDocumentDelete:
    async def test_deletes_successfully(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE /v2/support-documents/{reference_code} -> success."""
        mock_factus.delete.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Documento soporte eliminado con exito",
                "data": {"reference_code": "SD-TEST-001"},
            },
        )

        result = await service.delete("SD-TEST-001")

        mock_factus.delete.assert_awaited_once_with(
            "/v2/support-documents/SD-TEST-001"
        )
        assert result["status"] == "OK"
        assert result["data"]["reference_code"] == "SD-TEST-001"

    async def test_delete_raises_on_error(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE error -> FactusApiError."""
        mock_factus.delete.return_value = httpx.Response(404, json={"message": "Not found"})

        with pytest.raises(FactusApiError) as exc:
            await service.delete("NO-EXISTE")

        assert exc.value.status_code == 404


# ─── DOWNLOAD ────────────────────────────────────────────────────────────


class TestSupportDocumentDownload:
    async def test_download_pdf(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/support-documents/{number}/download-pdf -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "pdf_base_64_encoded": "JVBERi0xLjQgbW9jayBwZGY=",
                "name": "SETP990003795.pdf",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_pdf("SETP990003795")

        mock_factus.get.assert_awaited_once_with(
            "/v2/support-documents/SETP990003795/download-pdf"
        )
        assert data["pdf_base_64_encoded"] == "JVBERi0xLjQgbW9jayBwZGY="
        assert data["name"] == "SETP990003795.pdf"

    async def test_download_xml(
        self,
        service: SupportDocumentService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/support-documents/{number}/download-xml -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "xml_base_64_encoded": "PD94bWwgdmVyc2lvbj0iMS4wIj8+",
                "name": "SETP990003795.xml",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_xml("SETP990003795")

        mock_factus.get.assert_awaited_once_with(
            "/v2/support-documents/SETP990003795/download-xml"
        )
        assert "xml_base_64_encoded" in data
        assert data["name"] == "SETP990003795.xml"
