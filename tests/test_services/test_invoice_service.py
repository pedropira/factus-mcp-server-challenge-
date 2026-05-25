"""
Tests for InvoiceService (rewritten for Factus API v2 integration).

Verifica:
- Construcción correcta del payload para POST /v2/bills/validate
- Cálculo automático de totales
- Parseo de respuestas de Factus
- Manejo de errores HTTP
"""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.factus_client import FactusClient
from src.schemas.dto import InvoiceCreate
from src.schemas.models import Customer, Establishment, Product
from src.services.invoice_service import FactusApiError, InvoiceService


@pytest.fixture
def mock_factus() -> MagicMock:
    factus = MagicMock(spec=FactusClient)
    factus.post = AsyncMock()
    factus.get = AsyncMock()
    factus.delete = AsyncMock()
    return factus


@pytest.fixture
def service(mock_factus: MagicMock) -> InvoiceService:
    return InvoiceService(mock_factus)


@pytest.fixture
def sample_create_data() -> InvoiceCreate:
    return InvoiceCreate(
        reference_code="TEST-REF-001",
        payment_details=[
            {
                "payment_form": "1",
                "payment_method_code": "10",
                "reference_code": "PAY-TEST-REF-001",
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
                "quantity": "2.00",
                "discount_rate": "0.00",
                "price": "25000.00",
                "unit_measure_code": "94",
                "standard_code": "999",
                "taxes": [{"code": "01", "rate": "19.00"}],
            },
            {
                "code_reference": "PROD-002",
                "name": "Producto B",
                "quantity": "1.00",
                "discount_rate": "10.00",
                "price": "50000.00",
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
            "message": "Documento registrado y validado con exito",
            "data": {
                "reference_code": "TEST-REF-001",
                "number": "SETP990003793",
                "document_type": {"code": "01", "name": "Factura electronica de Venta"},
                "is_validated": True,
                "validated_at": "21-05-2026 07:32:15 PM",
                "cufe": "CUFE-ABC-123-XYZ",
                "errors": {
                    "RUT01": "La validacion del estado del RUT proximamente estara disponible",
                },
                "numbering_range": {
                    "prefix": "SETP",
                    "from": 990000000,
                    "to": 995000000,
                    "resolution_number": "18760000001",
                },
                "customer": {
                    "identification": "222222222222",
                    "names": "Consumidor final",
                },
                "items": [
                    {
                        "code_reference": "PROD-001",
                        "name": "Producto A",
                        "gross_value": "50000.00",
                        "taxes": [{"tribute": {"code": "01"}, "rates": [{"tax_amount": "9500.00"}]}],
                    },
                    {
                        "code_reference": "PROD-002",
                        "name": "Producto B",
                        "gross_value": "45000.00",
                        "taxes": [{"tribute": {"code": "01"}, "rates": [{"tax_amount": "8550.00"}]}],
                    },
                ],
            },
        },
    )


# ─── CREATE ──────────────────────────────────────────────────────────────


class TestInvoiceServiceCreate:
    async def test_creates_invoice_successfully(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """Happy path: envia a Factus, parsea respuesta, retorna dict."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create(sample_create_data)

        # Verify endpoint and payload
        mock_factus.post.assert_awaited_once()
        mock_factus.post.assert_awaited_once_with(
            "/v2/bills/validate", json=ANY
        )
        call_kwargs = mock_factus.post.await_args.kwargs
        payload = call_kwargs["json"]
        assert payload["reference_code"] == "TEST-REF-001"
        assert payload["document"] == "01"
        assert payload["operation_type"] == "10"
        assert payload["customer"]["identification"] == "222222222222"
        assert len(payload["items"]) == 2

        # Verify totals calculated
        total = float(payload["payment_details"][0]["amount"])
        # Item A: 2 x 25000 = 50000 gross, tax = 50000*(19/119) = 7983.19
        # Item B: 1 x 50000 x 0.9 = 45000 gross, tax = 45000*(19/119) = 7184.87
        # Gross = 95000, Tax = 15168.06, Total = 110168.06
        assert total == 110168.06, f"Expected 110168.06, got {total}"

        # Verify response
        assert result["status"] == "Created"
        assert result["data"]["number"] == "SETP990003793"
        assert result["data"]["cufe"] == "CUFE-ABC-123-XYZ"
        assert result["data"]["is_validated"] is True

    async def test_send_email_defaults_to_false(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        factus_success_response: httpx.Response,
    ) -> None:
        """send_email debe ser False por defecto."""
        mock_factus.post.return_value = factus_success_response
        await service.create(sample_create_data)

        payload = mock_factus.post.await_args.kwargs["json"]
        assert payload["send_email"] is False

    async def test_raises_on_factus_error(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
    ) -> None:
        """HTTP error de Factus → FactusApiError."""
        mock_factus.post.return_value = httpx.Response(
            422,
            json={
                "message": "El total del pago no coincide con la suma de los items",
                "errors": [{"field": "payment_details", "detail": "Amount mismatch"}],
            },
        )

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 422
        assert "payment" in str(exc.value.body).lower()

    async def test_handles_http_error_without_json_body(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
    ) -> None:
        """Error sin JSON body → no crash."""
        mock_factus.post.return_value = httpx.Response(500, text="Internal Server Error")

        with pytest.raises(FactusApiError) as exc:
            await service.create(sample_create_data)

        assert exc.value.status_code == 500


# ─── QUERY ───────────────────────────────────────────────────────────────


class TestInvoiceServiceQueries:
    async def test_list_invoices(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/bills con parametros."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "data": [
                        {"number": "SETP990003793", "reference_code": "REF-001"},
                        {"number": "SETP990003794", "reference_code": "REF-002"},
                    ]
                },
            },
        )

        result = await service.list(limit=10, status="1")

        mock_factus.get.assert_awaited_once_with(
            "/v2/bills", params={"limit": 10, "offset": 0, "filter[status]": "1"}
        )
        assert len(result["data"]["data"]) == 2

    async def test_get_by_reference_code_found(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code → encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "data": [
                        {
                            "number": "SETP990003793",
                            "reference_code": "REF-001",
                            "cufe": "CUFE-123",
                        }
                    ]
                },
            },
        )

        result = await service.get_by_reference_code("REF-001")
        assert result is not None
        assert result["reference_code"] == "REF-001"
        assert result["cufe"] == "CUFE-123"

    async def test_get_by_reference_code_not_found(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """Buscar por reference_code → no encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {"data": []},
            },
        )

        result = await service.get_by_reference_code("NO-EXISTE")
        assert result is None


# ─── GET BY NUMBER ───────────────────────────────────────────────────────


class TestInvoiceGetByNumber:
    async def test_get_by_number_found(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/bills/{number} -> encuentra."""
        mock_factus.get.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Solicitud exitosa",
                "data": {
                    "number": "SETP990003793",
                    "reference_code": "REF-001",
                    "cufe": "CUFE-123",
                },
            },
        )

        result = await service.get_by_number("SETP990003793")
        assert result is not None
        assert result["data"]["number"] == "SETP990003793"

    async def test_get_by_number_not_found(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/bills/{number} -> 404 -> None."""
        mock_factus.get.return_value = httpx.Response(404, json={"message": "Not found"})

        result = await service.get_by_number("NO-EXISTE")
        assert result is None


# ─── DELETE ──────────────────────────────────────────────────────────────


class TestInvoiceDelete:
    async def test_deletes_successfully(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE /v2/bills/{reference_code} -> success."""
        mock_factus.delete.return_value = httpx.Response(
            200,
            json={
                "status": "OK",
                "message": "Factura eliminada con exito",
                "data": {"reference_code": "REF-001"},
            },
        )

        result = await service.delete("REF-001")

        mock_factus.delete.assert_awaited_once_with("/v2/bills/REF-001")
        assert result["status"] == "OK"
        assert result["data"]["reference_code"] == "REF-001"

    async def test_delete_raises_on_error(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """DELETE error -> FactusApiError."""
        mock_factus.delete.return_value = httpx.Response(404, json={"message": "Not found"})

        with pytest.raises(FactusApiError) as exc:
            await service.delete("NO-EXISTE")

        assert exc.value.status_code == 404


# ─── DOWNLOAD ────────────────────────────────────────────────────────────


class TestInvoiceDownload:
    async def test_download_pdf(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/bills/{number}/download-pdf -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "pdf_base_64_encoded": "JVBERi0xLjQgbW9jayBwZGY=",
                "name": "SETP990003793.pdf",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_pdf("SETP990003793")

        mock_factus.get.assert_awaited_once_with(
            "/v2/bills/SETP990003793/download-pdf"
        )
        assert data["pdf_base_64_encoded"] == "JVBERi0xLjQgbW9jayBwZGY="
        assert data["name"] == "SETP990003793.pdf"

    async def test_download_xml(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
    ) -> None:
        """GET /v2/bills/{number}/download-xml -> JSON con base64."""
        mock_factus.get.return_value = httpx.Response(
            200,
            content=json.dumps({
                "xml_base_64_encoded": "PD94bWwgdmVyc2lvbj0iMS4wIj8+",
                "name": "SETP990003793.xml",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )

        data = await service.download_xml("SETP990003793")

        mock_factus.get.assert_awaited_once_with(
            "/v2/bills/SETP990003793/download-xml"
        )
        assert "xml_base_64_encoded" in data
        assert data["name"] == "SETP990003793.xml"


# ─── ENRICH WITH TOTALS ─────────────────────────────────────────────────


class TestEnrichWithTotals:
    def test_calculates_single_item(self) -> None:
        from src.services.enrich import enrich_with_totals

        payload = {
            "items": [
                {
                    "quantity": "1.00",
                    "price": "10000.00",
                    "discount_rate": "0.00",
                    "taxes": [{"code": "01", "rate": "19.00"}],
                }
            ],
            "payment_details": [{"amount": "0.00"}],
        }
        result = enrich_with_totals(payload)
        total = float(result["payment_details"][0]["amount"])
        # gross=10000, tax=10000*(19/119)=1596.64, total=11596.64
        assert total == 11596.64

    def test_calculates_multi_item_with_discount(self) -> None:
        from src.services.enrich import enrich_with_totals

        payload = {
            "items": [
                {
                    "quantity": "2.00",
                    "price": "25000.00",
                    "discount_rate": "0.00",
                    "taxes": [{"code": "01", "rate": "19.00"}],
                },
                {
                    "quantity": "1.00",
                    "price": "50000.00",
                    "discount_rate": "10.00",
                    "taxes": [{"code": "01", "rate": "19.00"}],
                },
            ],
            "payment_details": [{"amount": "0.00"}],
        }
        result = enrich_with_totals(payload)
        total = float(result["payment_details"][0]["amount"])
        # Item A: 2 x 25000 = 50000 gross, tax=50000*(19/119)=7983.19
        # Item B: 1 x 50000 x 0.90 = 45000 gross, tax=45000*(19/119)=7184.87
        # Gross = 95000, Tax = 15168.06, Total = 110168.06
        assert total == 110168.06

    def test_no_items(self) -> None:
        from src.services.enrich import enrich_with_totals

        payload = {
            "items": [],
            "payment_details": [{"amount": "0.00"}],
        }
        result = enrich_with_totals(payload)
        assert float(result["payment_details"][0]["amount"]) == 0.00

    def test_with_allowance_charges_discounts_and_surcharges(self) -> None:
        from src.services.enrich import enrich_with_totals

        """Allowance charges: discount rest, surcharge suma."""
        payload = {
            "items": [
                {
                    "quantity": "1.00",
                    "price": "100000.00",
                    "discount_rate": "0.00",
                    "taxes": [{"code": "01", "rate": "19.00"}],
                }
            ],
            "allowance_charges": [
                {"is_surcharge": False, "reason": "Flete", "base_amount": "100000.00", "amount": "5000.00"},
                {"is_surcharge": True, "reason": "Descuento pronto pago", "base_amount": "100000.00", "amount": "3000.00"},
            ],
            "payment_details": [{"amount": "0.00"}],
        }
        result = enrich_with_totals(payload)
        total = float(result["payment_details"][0]["amount"])
        # gross=100000, tax=100000*(19/119)=15966.39, disc=-5000, surch=+3000
        # total = 100000 + 15966.39 - 5000 + 3000 = 113966.39
        assert total == 113966.39

    def test_multiple_tax_rates(self) -> None:
        from src.services.enrich import enrich_with_totals

        """Item with two tax rates (IVA 19% + INC 8%) → both calculated."""
        payload = {
            "items": [
                {
                    "quantity": "1.00",
                    "price": "100000.00",
                    "discount_rate": "0.00",
                    "taxes": [
                        {"code": "01", "rate": "19.00"},
                        {"code": "04", "rate": "8.00"},
                    ],
                }
            ],
            "payment_details": [{"amount": "0.00"}],
        }
        result = enrich_with_totals(payload)
        total = float(result["payment_details"][0]["amount"])
        # gross=100000, tax_iva=100000*(19/119)=15966.39, tax_inc=100000*(8/108)=7407.41
        # total = 100000 + 15966.39 + 7407.41 = 123373.80
        assert total == 123373.80


# ─── CREATE WITH NUMBERING ───────────────────────────────────────────────


class TestInvoiceServiceCreateWithNumbering:
    """Tests for create_with_numbering() — full Colombian business flow."""

    @pytest.fixture
    def sample_customer(self) -> Customer:
        return Customer(
            id=1,
            identification_document_id=6,  # NIT
            identification="900123456",
            dv="5",
            company="Empresa SAS",
            names="",
            email="factura@empresa.com",
            address="Calle 100 # 20-30",
            municipality_id="11001",
            tribute_id="22",  # Gran Contribuyente
            legal_organization_id="1",  # Persona jurídica
        )

    @pytest.fixture
    def sample_products(self) -> list[Product]:
        return [
            Product(
                id=1,
                code_reference="PROD-001",
                name="Producto A",
                price=Decimal("25000.00"),
                tax_rate="19.00",
                unit_measure_id=70,
                standard_code_id=1,
                tribute_id=1,
                is_excluded=False,
            ),
            Product(
                id=2,
                code_reference="PROD-002",
                name="Producto B",
                price=Decimal("50000.00"),
                tax_rate="19.00",
                unit_measure_id=70,
                standard_code_id=1,
                tribute_id=1,
                is_excluded=False,
            ),
        ]

    @pytest.fixture
    def mock_numbering_service(self) -> MagicMock:
        mock = MagicMock()
        mock.next_available = AsyncMock(return_value=990000001)
        return mock

    async def test_create_with_numbering_happy_path(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        sample_customer: Customer,
        sample_products: list[Product],
        mock_numbering_service: MagicMock,
        factus_success_response: httpx.Response,
    ) -> None:
        """Happy path: maps models, validates, calculates taxes, sends."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create_with_numbering(
            data=sample_create_data,
            numbering_range_id=1,
            numbering_service=mock_numbering_service,
            customer=sample_customer,
            products=sample_products,
        )

        # Verify validation was called
        mock_numbering_service.next_available.assert_awaited_once_with(1)

        # Verify Factus API was called
        mock_factus.post.assert_awaited_once()
        call_kwargs = mock_factus.post.await_args.kwargs
        payload = call_kwargs["json"]

        # Customer should be mapped from models
        assert payload["customer"]["identification_document_code"] == "31"  # NIT
        assert payload["customer"]["identification"] == "900123456"
        assert payload["customer"]["tribute_code"] == "22"

        # Items mapped from products
        assert len(payload["items"]) == 2
        assert payload["items"][0]["code_reference"] == "PROD-001"
        assert payload["items"][1]["code_reference"] == "PROD-002"

        # Totals calculated
        total = float(payload["payment_details"][0]["amount"])
        assert total == 110168.06

        # Withholding taxes should be present (Gran Contribuyente + transfer payment)
        # ReteIVA triggers because Gran Contribuyente (tribute "22")
        assert "withholding_taxes" in payload["items"][0]
        assert "withholding_taxes" in payload["items"][1]

        # Response returned correctly
        assert result["status"] == "Created"
        assert result["data"]["number"] == "SETP990003793"

    async def test_create_with_numbering_validation_failure(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        mock_numbering_service: MagicMock,
    ) -> None:
        """Validation failure → raises ValueError."""
        # Remove required customer field to trigger validation
        sample_create_data.customer = {}  # type: ignore[assignment]

        with pytest.raises(ValueError, match="Invoice validation failed"):
            await service.create_with_numbering(
                data=sample_create_data,
                numbering_range_id=1,
                numbering_service=mock_numbering_service,
            )

        # Factus API should NOT have been called
        mock_factus.post.assert_not_awaited()

    async def test_create_with_numbering_factus_error(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        mock_numbering_service: MagicMock,
    ) -> None:
        """Factus API error → FactusApiError."""
        mock_factus.post.return_value = httpx.Response(
            422,
            json={"message": "Validation error from Factus"},
        )

        with pytest.raises(FactusApiError) as exc:
            await service.create_with_numbering(
                data=sample_create_data,
                numbering_range_id=1,
                numbering_service=mock_numbering_service,
            )

        assert exc.value.status_code == 422

    async def test_create_with_numbering_no_models_raw_dicts(
        self,
        service: InvoiceService,
        mock_factus: MagicMock,
        sample_create_data: InvoiceCreate,
        mock_numbering_service: MagicMock,
        factus_success_response: httpx.Response,
    ) -> None:
        """Without Customer/Product models → uses raw dicts from DTO."""
        mock_factus.post.return_value = factus_success_response

        result = await service.create_with_numbering(
            data=sample_create_data,
            numbering_range_id=1,
            numbering_service=mock_numbering_service,
        )

        # Customer should be the raw dict from DTO (not mapped)
        call_kwargs = mock_factus.post.await_args.kwargs
        payload = call_kwargs["json"]
        assert payload["customer"]["identification_document_code"] == "13"
        assert payload["customer"]["names"] == "Cliente de prueba"

        assert result["status"] == "Created"

