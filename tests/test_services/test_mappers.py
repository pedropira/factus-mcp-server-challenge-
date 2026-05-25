"""
Tests for Factus API v2 payload mappers.

Covers:
  - customer_to_factus_dict()
  - product_to_factus_dict()
  - Individual mapping helpers
  - Fallback behavior for unknown IDs
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.schemas.models import Customer, Establishment, Product
from src.services.mappers import (
    IDENTIFICATION_DOCUMENT_MAP,
    ITEM_TRIBUTE_TAX_CODE_MAP,
    STANDARD_CODE_MAP,
    TRIBUTE_MAP,
    UNIT_MEASURE_MAP,
    _clean_dict,
    _map_identification_document_id,
    _map_item_tribute_to_tax_code,
    _map_legal_organization_id,
    _map_standard_code_id,
    _map_tribute_id,
    _map_unit_measure_id,
    customer_to_factus_dict,
    product_to_factus_dict,
)


# ═══════════════════════════════════════════════════════════════════════════
# customer_to_factus_dict
# ═══════════════════════════════════════════════════════════════════════════


class TestCustomerToFactusDict:
    def test_full_customer(self) -> None:
        """All fields present → correctly mapped."""
        cust = Customer(
            id=1,
            identification_document_id=6,  # NIT
            identification="900123456",
            dv="5",
            company="Empresa SAS",
            trade_name="Empresa",
            names="Contacto",  # Non-empty so it's kept
            email="factura@empresa.com",
            phone="6012345678",
            address="Calle 100 # 20-30",
            municipality_id="11001",
            tribute_id="22",  # Gran Contribuyente
            legal_organization_id="1",  # Persona jurídica
        )
        result = customer_to_factus_dict(cust)

        assert result["identification_document_code"] == "31"  # NIT DIAN code
        assert result["identification"] == "900123456"
        assert result["dv"] == "5"
        assert result["company"] == "Empresa SAS"
        assert result["trade_name"] == "Empresa"
        assert result["names"] == "Contacto"
        assert result["email"] == "factura@empresa.com"
        assert result["phone"] == "6012345678"
        assert result["address"] == "Calle 100 # 20-30"
        assert result["municipality_code"] == "11001"
        assert result["tribute_code"] == "22"  # Gran Contribuyente
        assert result["legal_organization_code"] == "1"  # Persona jurídica

    def test_minimal_customer(self) -> None:
        """Minimal fields only → still valid, empty strings cleaned."""
        cust = Customer(
            id=2,
            identification_document_id=7,  # Pasaporte
            identification="ABC123456",
            dv=None,
            company=None,
            trade_name=None,
            names="John Doe",
            email="john@example.com",
            phone=None,
            address=None,
            municipality_id="11001",
            tribute_id="21",  # No aplica
            legal_organization_id="2",  # Persona natural
        )
        result = customer_to_factus_dict(cust)

        assert result["identification_document_code"] == "41"  # Pasaporte
        assert result["identification"] == "ABC123456"
        assert result["names"] == "John Doe"
        assert result["tribute_code"] == "ZZ"  # No aplica
        assert result["legal_organization_code"] == "2"
        # Empty/None values should be cleaned
        assert "dv" not in result or result.get("dv") == ""
        assert "phone" not in result
        assert "address" not in result

    def test_unknown_identification_document_falls_back(self) -> None:
        """Unknown identification_document_id → fallback to "13" (Cédula)."""
        cust = Customer(
            id=3,
            identification_document_id=999,  # Unknown
            identification="123456789",
            names="Test",
            email="test@test.com",
            municipality_id="11001",
            tribute_id="21",
            legal_organization_id="2",
        )
        result = customer_to_factus_dict(cust)
        assert result["identification_document_code"] == "13"

    def test_none_tribute_id_falls_back(self) -> None:
        """None tribute_id → fallback to "ZZ"."""
        cust = Customer(
            id=4,
            identification_document_id=3,
            identification="123",
            names="Test",
            email="t@t.com",
            municipality_id="11001",
            tribute_id=None,
            legal_organization_id="2",
        )
        result = customer_to_factus_dict(cust)
        assert result["tribute_code"] == "ZZ"


# ═══════════════════════════════════════════════════════════════════════════
# product_to_factus_dict
# ═══════════════════════════════════════════════════════════════════════════


class TestProductToFactusDict:
    def test_standard_product(self) -> None:
        """Standard product → correct mapping."""
        prod = Product(
            id=1,
            code_reference="PROD-001",
            name="Laptop",
            price=Decimal("2500000.00"),
            tax_rate="19.00",
            unit_measure_id=70,  # Unidad
            standard_code_id=1,  # Estándar del contribuyente
            tribute_id=1,  # IVA
            is_excluded=False,
        )
        result = product_to_factus_dict(prod, quantity="2", discount_rate="0.00")

        assert result["code_reference"] == "PROD-001"
        assert result["name"] == "Laptop"
        assert result["quantity"] == "2.00"
        assert result["price"] == "2500000.00"
        assert result["discount_rate"] == "0.00"
        assert result["unit_measure_code"] == "94"  # Unidad DIAN code
        assert result["standard_code"] == "999"
        assert result["is_excluded"] == "false"
        assert result["total_discount"] == "0.00"
        assert result["taxes"] == [{"code": "01", "rate": "19.00"}]

    def test_excluded_product(self) -> None:
        """Excluded product → is_excluded=true."""
        prod = Product(
            id=2,
            code_reference="EXCL-001",
            name="Producto excluido",
            price=Decimal("100000.00"),
            tax_rate="0.00",
            unit_measure_id=70,
            standard_code_id=1,
            tribute_id=4,  # No causa
            is_excluded=True,
        )
        result = product_to_factus_dict(prod, quantity="1", discount_rate="0.00")

        assert result["is_excluded"] == "true"
        assert result["taxes"] == [{"code": "01", "rate": "0.00"}]

    def test_with_discount_calculates_total_discount(self) -> None:
        """Discount → total_discount calculated."""
        prod = Product(
            id=3,
            code_reference="DISC-001",
            name="Con descuento",
            price=Decimal("100000.00"),
            tax_rate="19.00",
            unit_measure_id=70,
            standard_code_id=1,
            tribute_id=1,
            is_excluded=False,
        )
        result = product_to_factus_dict(prod, quantity="5", discount_rate="10.00")

        assert result["quantity"] == "5.00"
        assert result["discount_rate"] == "10.00"
        # total_discount = 100_000 * 5 * 10/100 = 50_000
        assert result["total_discount"] == "50000.00"

    def test_unknown_unit_measure_falls_back(self) -> None:
        """Unknown unit_measure_id → "94" (Unidad)."""
        prod = Product(
            id=4,
            code_reference="UOM-001",
            name="Test",
            price=Decimal("1000.00"),
            tax_rate="19.00",
            unit_measure_id=999,  # Unknown
            standard_code_id=1,
            tribute_id=1,
            is_excluded=False,
        )
        result = product_to_factus_dict(prod, quantity="1")
        assert result["unit_measure_code"] == "94"


# ═══════════════════════════════════════════════════════════════════════════
# Mapping helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestMappingHelpers:
    def test_identification_document_map(self) -> None:
        assert _map_identification_document_id(6) == "31"  # NIT
        assert _map_identification_document_id(3) == "13"  # Cédula
        assert _map_identification_document_id(999) == "13"  # Fallback

    def test_tribute_map(self) -> None:
        assert _map_tribute_id("21") == "ZZ"  # No aplica
        assert _map_tribute_id("22") == "22"  # Gran Contribuyente
        assert _map_tribute_id("23") == "08"  # Autorretenedor
        assert _map_tribute_id(None) == "ZZ"  # Fallback
        assert _map_tribute_id("999") == "ZZ"  # Fallback

    def test_legal_organization_map(self) -> None:
        assert _map_legal_organization_id("1") == "1"  # Persona jurídica
        assert _map_legal_organization_id("2") == "2"  # Persona natural
        assert _map_legal_organization_id(None) == "2"  # Fallback

    def test_unit_measure_map(self) -> None:
        assert _map_unit_measure_id(70) == "94"  # Unidad
        assert _map_unit_measure_id(158) == "109"  # Hora
        assert _map_unit_measure_id(999) == "94"  # Fallback

    def test_standard_code_map(self) -> None:
        assert _map_standard_code_id(1) == "999"  # Estándar de adopción del contribuyente
        assert _map_standard_code_id(2) == "2"  # UNSPSC
        assert _map_standard_code_id(999) == "999"  # Fallback

    def test_item_tribute_to_tax_code(self) -> None:
        assert _map_item_tribute_to_tax_code(1) == "01"  # IVA
        assert _map_item_tribute_to_tax_code(2) == "04"  # INC
        assert _map_item_tribute_to_tax_code(999) == "01"  # Fallback
