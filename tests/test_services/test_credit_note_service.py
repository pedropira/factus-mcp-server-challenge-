"""
Tests for CreditNoteService — notas crédito vía Factus API.

Verifica:
- Construcción correcta del payload para POST /v2/credit-notes
- Parseo de respuestas de Factus
- Listado con filtros
- Búsqueda por ID y reference_code
- Eliminación por ID
- Descarga de PDF/XML
- Manejo de errores HTTP
"""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import CreditNoteCreate
from src.services.credit_note_service import CreditNoteService
from src.services.invoice_service import FactusApiError


@pytest.fixture
def mock_factus() -> MagicMock:
    factus = MagicMock(spec=FactusClient)
    factus.post = AsyncMock()
    factus.get = AsyncMock()
    factus.delete = AsyncMock()
    return factus


@pytest.fixture
def service(mock_factus: MagicMock) -> CreditNoteService:
    return CreditNoteService(mock_factus)


@pytest.fixture
def sample_create_data() -> CreditNoteCreate:
    return CreditNoteCreate(
        reference_code="CN-TEST-001",
        correction_concept_code="1",
        invoice_reference="SETP990003793",
        payment_details=[
            {
                "payment_form": "1",
                "payment_method_code": "10",
                "reference_code": "PAY-CN-001",
                "amount": "0.00",
            }
        ],
        customer={
            "identification_document_code": "13",
            "identification": "222222222222",
            "names": "Cliente de prueba",
            "address": "Calle 123 # 45-67",
            "email": "cliente@example.com",
            "phone": "3001234567",
            "legal_organization_code": "2",
            "tribute_code": "ZZ",
            "municipality_code": "11001",
        },
        items=[
            {
                "code_reference": "PROD-001",
                "name": "Producto A",
                "quantity": "1.00",
                "discount_rate": "0.00",
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
            "message": "Nota credito registrada y validada con exito",
            "data": {
                "reference_code": "CN-TEST-001",
                "id": 67890,
                "document_type": {"code": "02", "name": "Nota Credito"},
                "is_validated": True,
                "validated_at": "21-05-2026 07:32:15 PM",
            },
        },
    )


# ─── CREATE ──────────────────────────────────────────────────────────────


class TestCreditNoteCreate:
    async def test_creates_credit_note_successfully(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
        sample_create_data: CreditNoteCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """Happy path: envia a Factus, parsea respuesta, retorna dict."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create(sample_create_data)

        # Verify endpoint and payload
        mock_factus.post.assert_awaited_once_with(
            "/v2/credit-notes",
            json={
                "reference_code": "CN-TEST-001",
                "document": "02",
                "operation_type": "20",
                "correction_concept_code": "1",
                "observation": "",
                "send_email": False,
                "invoice_reference": "SETP990003793",
                "payment_details": sample_create_data.payment_details,
                "customer": sample_create_data.customer,
                "items": sample_create_data.items,
            },
        )

        # Verify response
        assert result["status"] == "Created"
        assert result["data"]["id"] == 67890
        assert result["data"]["is_validated"] is True

    async def test_send_email_defaults_to_false(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
        sample_create_data: CreditNoteCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """send_email debe ser False por defecto."""
        mock_factus.post.return_value = factus_success_response
        await service.create(sample_create_data)

        call_kwargs = mock_factus.post.await_args.kwargs
        assert call_kwargs["json"]["send_email"] is False

    async def test_raises_on_factus_error(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
        sample_create_data: CreditNoteCreate,
    ) -> None:
        """HTTP error de Factus -> FactusApiError."""
        mock_factus.post.return_value = httpx.Response(
            422,
            json={
                "message": "La factura referenciada no existe",
                "errors": [{"field": "invoice_reference", "detail": "Not found"}],
            },
        )

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 422
        assert "factura" in str(exc.value.body).lower()

    async def test_handles_http_error_without_json_body(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
        sample_create_data: CreditNoteCreate,
    ) -> None:
        """Error sin JSON body -> no crash."""
        mock_factus.post.return_value = httpx.Response(500, text="Internal Server Error")

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 500


# ─── QUERY ───────────────────────────────────────────────────────────────


class TestCreditNoteQueries:
    async def test_list_credit_notes(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/credit-notes con parametros."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "data": [
                        {"id": 67890, "reference_code": "CN-TEST-001"},
                        {"id": 67891, "reference_code": "CN-TEST-002"},
                    ]
                },
            },
        )

        result = await service.list(limit=10, status="1")

        mock_factus.get.assert_awaited_once_with(
            "/v2/credit-notes",
            params={"limit": 10, "offset": 0, "filter[status]": "1"},
        )
        assert len(result["data"]["data"]) == 2

    async def test_get_by_id_found(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por ID -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "id": 67890,
                    "reference_code": "CN-TEST-001",
                    "is_validated": True,
                },
            },
        )

        result = await service.get_by_id(67890)
        assert result is not None
        assert result["data"]["id"] == 67890
        assert result["data"]["reference_code"] == "CN-TEST-001"

    async def test_get_by_id_not_found(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por ID -> 404 -> None."""
        mock_factus.get.return_value = httpx.Response(404, json={"message": "Not found"})

        result = await service.get_by_id(99999)
        assert result is None

    async def test_get_by_reference_code_found(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {"data": [{"id": 67890, "reference_code": "CN-TEST-001"}]},
            },
        )

        result = await service.get_by_reference_code("CN-TEST-001")
        assert result is not None
        assert result["reference_code"] == "CN-TEST-001"

    async def test_get_by_reference_code_not_found(
        self,
        service: CreditNoteService,
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


class TestCreditNoteDelete:
    async def test_deletes_successfully(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE /v2/credit-notes/{id} -> success."""
        mock_factus.delete.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Nota credito eliminada con exito",
                "data": {"id": 67890},
            },
        )

        result = await service.delete(67890)

        mock_factus.delete.assert_awaited_once_with("/v2/credit-notes/67890")
        assert result["status"] == "OK"
        assert result["data"]["id"] == 67890

    async def test_delete_raises_on_error(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE error -> FactusApiError."""
        mock_factus.delete.return_value = httpx.Response(404, json={"message": "Not found"})

        with pytest.raises(FactusApiError) as exc:
            await service.delete(99999)

        assert exc.value.status_code == 404


# ─── DOWNLOAD ────────────────────────────────────────────────────────────


class TestCreditNoteDownload:
    async def test_download_pdf(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/credit-notes/{number}/download-pdf -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "pdf_base_64_encoded": "JVBERi0xLjQgbW9jayBwZGY=",
                "name": "NC-67890.pdf",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_pdf("67890")

        mock_factus.get.assert_awaited_once_with(
            "/v2/credit-notes/67890/download-pdf"
        )
        assert data["pdf_base_64_encoded"] == "JVBERi0xLjQgbW9jayBwZGY="
        assert data["name"] == "NC-67890.pdf"

    async def test_download_xml(
        self,
        service: CreditNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/credit-notes/{number}/download-xml -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "xml_base_64_encoded": "PD94bWwgdmVyc2lvbj0iMS4wIj8+",
                "name": "NC-67890.xml",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_xml("67890")

        mock_factus.get.assert_awaited_once_with(
            "/v2/credit-notes/67890/download-xml"
        )
        assert "xml_base_64_encoded" in data
        assert data["name"] == "NC-67890.xml"
