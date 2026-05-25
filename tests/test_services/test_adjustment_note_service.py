"""
Tests for AdjustmentNoteService — notas de ajuste vía Factus API.

Verifica:
- Construcción correcta del payload para POST /v2/adjustment-notes/validate
- Parseo de respuestas de Factus
- Listado con filtros
- Búsqueda por número de documento y reference_code
- Eliminación por reference_code
- Descarga de PDF/XML por número de documento
- Manejo de errores HTTP
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import AdjustmentNoteCreate
from src.services.adjustment_note_service import AdjustmentNoteService
from src.services.invoice_service import FactusApiError


@pytest.fixture
def mock_factus() -> MagicMock:
    factus = MagicMock(spec=FactusClient)
    factus.post = AsyncMock()
    factus.get = AsyncMock()
    factus.delete = AsyncMock()
    return factus


@pytest.fixture
def service(mock_factus: MagicMock) -> AdjustmentNoteService:
    return AdjustmentNoteService(mock_factus)


@pytest.fixture
def sample_create_data() -> AdjustmentNoteCreate:
    return AdjustmentNoteCreate(
        reference_code="AN-TEST-001",
        support_document_number="SD-TEST-001",
        correction_concept_code="2",
        payment_details=[
            {
                "payment_form": "1",
                "payment_method_code": "42",
                "reference_code": "pago-001",
                "amount": "60000.00",
                "due_date": "2025-01-01",
            },
        ],
        provider={
            "identification_document_code": "13",
            "identification": "222222222222",
            "names": "Proveedor de prueba",
            "address": "Calle 123 # 45-67",
            "email": "proveedor@example.com",
            "phone": "3001234567",
            "legal_organization_code": "2",
            "tribute_code": "ZZ",
            "municipality_code": "11001",
        },
        items=[
            {
                "code_reference": "ITEM-001",
                "name": "Item corregido A",
                "quantity": "1.00",
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
            "message": "Nota de ajuste registrada y validada con exito",
            "data": {
                "reference_code": "AN-TEST-001",
                "number": "SEDS984000129",
                "document_type": {"code": "04", "name": "Nota de Ajuste"},
                "is_validated": True,
                "validated_at": "21-05-2026 07:32:15 PM",
            },
        },
    )


# ─── CREATE ──────────────────────────────────────────────────────────────


class TestAdjustmentNoteCreate:
    async def test_creates_adjustment_note_successfully(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        sample_create_data: AdjustmentNoteCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """Happy path: envia a Factus, parsea respuesta, retorna dict."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create(sample_create_data)

        # Verify endpoint and payload
        mock_factus.post.assert_awaited_once()
        mock_factus.post.assert_awaited_once_with(
            "/v2/adjustment-notes/validate",
            json={
                "reference_code": "AN-TEST-001",
                "support_document_number": "SD-TEST-001",
                "correction_concept_code": "2",
                "payment_details": [
                    {
                        "payment_form": "1",
                        "payment_method_code": "42",
                        "reference_code": "pago-001",
                        "amount": "60000.00",
                        "due_date": "2025-01-01",
                    },
                ],
                "provider": sample_create_data.provider,
                "items": sample_create_data.items,
                "observation": "",
            },
        )

        # Verify response
        assert result["status"] == "Created"
        assert result["data"]["number"] == "SEDS984000129"
        assert result["data"]["is_validated"] is True

    async def test_observacion_defaults_to_empty_string(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        sample_create_data: AdjustmentNoteCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """observation debe ser '' por defecto."""
        mock_factus.post.return_value = factus_success_response
        await service.create(sample_create_data)

        call_kwargs = mock_factus.post.await_args.kwargs
        assert call_kwargs["json"]["observation"] == ""

    async def test_omits_optional_fields_when_none(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        factus_success_response: httpx.Response,
    ) -> None:
        """created_time, numbering_range_id, cash_rounding_amount no se envian si son None."""
        data = AdjustmentNoteCreate(
            reference_code="AN-TEST-002",
            support_document_number="SD-TEST-002",
            correction_concept_code="1",
            payment_details=[{"payment_form": "1", "payment_method_code": "10", "amount": "50000.00"}],
            provider={"name": "test"},
            items=[{"code_reference": "X", "name": "Y", "quantity": "1", "price": "100"}],
        )
        mock_factus.post.return_value = factus_success_response
        await service.create(data)

        payload = mock_factus.post.await_args.kwargs["json"]
        assert "created_time" not in payload
        assert "numbering_range_id" not in payload
        assert "cash_rounding_amount" not in payload

    async def test_includes_optional_fields_when_set(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        factus_success_response: httpx.Response,
    ) -> None:
        """created_time, numbering_range_id, cash_rounding_amount se envian si tienen valor."""
        data = AdjustmentNoteCreate(
            reference_code="AN-TEST-003",
            support_document_number="SD-TEST-003",
            correction_concept_code="1",
            payment_details=[{"payment_form": "1", "payment_method_code": "10", "amount": "50000.00"}],
            provider={"name": "test"},
            items=[{"code_reference": "X", "name": "Y", "quantity": "1", "price": "100"}],
            created_time="15:30:00",
            numbering_range_id=5,
            cash_rounding_amount="0.50",
        )
        mock_factus.post.return_value = factus_success_response
        await service.create(data)

        payload = mock_factus.post.await_args.kwargs["json"]
        assert payload["created_time"] == "15:30:00"
        assert payload["numbering_range_id"] == 5
        assert payload["cash_rounding_amount"] == "0.50"

    async def test_raises_on_factus_error(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        sample_create_data: AdjustmentNoteCreate,
    ) -> None:
        """HTTP error de Factus -> FactusApiError."""
        mock_factus.post.return_value = httpx.Response(
            422,
            json={
                "message": "El documento soporte referenciado no existe",
                "errors": [{"field": "support_document_number", "detail": "Not found"}],
            },
        )

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 422
        assert "documento soporte" in str(exc.value.body).lower()

    async def test_handles_http_error_without_json_body(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
        sample_create_data: AdjustmentNoteCreate,
    ) -> None:
        """Error sin JSON body -> no crash."""
        mock_factus.post.return_value = httpx.Response(500, text="Internal Server Error")

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 500


# ─── QUERY ───────────────────────────────────────────────────────────────


class TestAdjustmentNoteQueries:
    async def test_list_adjustment_notes(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/adjustment-notes con parametros."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "data": [
                        {"id": 12345, "reference_code": "AN-TEST-001"},
                        {"id": 12346, "reference_code": "AN-TEST-002"},
                    ]
                },
            },
        )

        result = await service.list(limit=10, status="1")

        mock_factus.get.assert_awaited_once_with(
            "/v2/adjustment-notes",
            params={"limit": 10, "offset": 0, "filter[status]": "1"},
        )
        assert len(result["data"]["data"]) == 2

    async def test_get_by_number_found(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por número -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "number": "SEDS984000129",
                    "reference_code": "AN-TEST-001",
                    "is_validated": True,
                },
            },
        )

        result = await service.get_by_number("SEDS984000129")
        assert result is not None
        assert result["data"]["number"] == "SEDS984000129"
        assert result["data"]["reference_code"] == "AN-TEST-001"

    async def test_get_by_number_not_found(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por número -> 404 -> None."""
        mock_factus.get.return_value = httpx.Response(404, json={"message": "Not found"})

        result = await service.get_by_number("NO-EXISTE")
        assert result is None

    async def test_get_by_reference_code_found(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {"data": [{"id": 12345, "reference_code": "AN-TEST-001"}]},
            },
        )

        result = await service.get_by_reference_code("AN-TEST-001")
        assert result is not None
        assert result["reference_code"] == "AN-TEST-001"

    async def test_get_by_reference_code_not_found(
        self,
        service: AdjustmentNoteService,
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


class TestAdjustmentNoteDelete:
    async def test_deletes_successfully(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE /v1/adjustment-notes/reference/{code} -> success."""
        mock_factus.delete.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Nota de ajuste eliminada con exito",
                "data": {"id": 12345},
            },
        )

        result = await service.delete("AN-TEST-001")

        mock_factus.delete.assert_awaited_once_with(
            "/v1/adjustment-notes/reference/AN-TEST-001"
        )
        assert result["status"] == "OK"
        assert result["data"]["id"] == 12345

    async def test_delete_raises_on_error(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE error -> FactusApiError."""
        mock_factus.delete.return_value = httpx.Response(404, json={"message": "Not found"})

        with pytest.raises(FactusApiError) as exc:
            await service.delete("NO-EXISTE")

        assert exc.value.status_code == 404


# ─── DOWNLOAD ────────────────────────────────────────────────────────────


class TestAdjustmentNoteDownload:
    async def test_download_pdf(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/adjustment-notes/{number}/download-pdf -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "pdf_base_64_encoded": "JVBERi0xLjQgbW9jayBwZGY=",
                "name": "AN-SEDS984000129.pdf",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_pdf("SEDS984000129")

        mock_factus.get.assert_awaited_once_with(
            "/v2/adjustment-notes/SEDS984000129/download-pdf"
        )
        assert data["pdf_base_64_encoded"] == "JVBERi0xLjQgbW9jayBwZGY="
        assert data["name"] == "AN-SEDS984000129.pdf"

    async def test_download_xml(
        self,
        service: AdjustmentNoteService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/adjustment-notes/{number}/download-xml -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "xml_base_64_encoded": "PD94bWwgdmVyc2lvbj0iMS4wIj8+",
                "name": "AN-SEDS984000129.xml",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_xml("SEDS984000129")

        mock_factus.get.assert_awaited_once_with(
            "/v2/adjustment-notes/SEDS984000129/download-xml"
        )
        assert "xml_base_64_encoded" in data
        assert data["name"] == "AN-SEDS984000129.xml"
