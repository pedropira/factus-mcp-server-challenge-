"""
Tests for WithholdingTaxCalculator — Colombian DIAN retentions.

Covers all four withholding types:
  - ReteRenta (code "06")
  - ReteIVA  (code "05")
  - ReteICA  (code "07")
  - ReteGMF  (code "20")

Each test verifies the pure function `calculate()` from
src.services.tax.withholding.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.services.tax.withholding import (
    _get_rete_gmf_amount,
    _get_reteica_per_item,
    _get_reteiva_per_item,
    _item_gross,
    calculate,
)


# ═══════════════════════════════════════════════════════════════════════════
# _item_gross
# ═══════════════════════════════════════════════════════════════════════════


class TestItemGross:
    def test_basic_price_times_quantity(self) -> None:
        item = {"price": "10000.00", "quantity": "2"}
        assert _item_gross(item) == Decimal("20000.00")

    def test_with_discount(self) -> None:
        item = {"price": "50000.00", "quantity": "1", "discount_rate": "10.00"}
        assert _item_gross(item) == Decimal("45000.00")

    def test_zero_quantity(self) -> None:
        item = {"price": "10000.00", "quantity": "0"}
        assert _item_gross(item) == Decimal("0.00")

    def test_default_quantity_is_one(self) -> None:
        item = {"price": "10000.00"}
        assert _item_gross(item) == Decimal("10000.00")

    def test_invalid_price_returns_zero(self) -> None:
        item = {"price": "not-a-number", "quantity": "1"}
        assert _item_gross(item) == Decimal("0.00")


# ═══════════════════════════════════════════════════════════════════════════
# ReteRenta — code "06"
# ═══════════════════════════════════════════════════════════════════════════


class TestReteRenta:
    """Covers: rates by customer type, autorretenedor exemption, UVT threshold."""

    CUSTOMER_NATURAL = {
        "tribute_code": "ZZ",
        "legal_organization_code": "2",  # Persona natural
        "municipality_code": "11001",
    }
    CUSTOMER_LEGAL = {
        "tribute_code": "01",
        "legal_organization_code": "1",  # Persona jurídica
        "municipality_code": "11001",
    }
    CUSTOMER_AUTORRETENEDOR = {
        "tribute_code": "08",  # Autorretenedor
        "legal_organization_code": "1",
        "municipality_code": "11001",
    }

    ITEM_GOODS = [
        {
            "code_reference": "PROD-001",
            "price": "1000000.00",
            "quantity": "2",
            "discount_rate": "0.00",
        }
    ]

    def test_natural_person_above_threshold(self) -> None:
        """Persona natural, above 27 UVT → ReteRenta 2.5%."""
        result = calculate(self.CUSTOMER_NATURAL, self.ITEM_GOODS, Decimal("2000000.00"))
        # gross = 2_000_000 > 27*47000 = 1_269_000
        # reterenta = 2_000_000 * 2.5 / 100 = 50_000
        assert 0 in result
        assert len(result[0]) == 1
        assert result[0][0]["code"] == "06"
        assert result[0][0]["withholding_tax_rate"] == "2.50"
        assert result[0][0]["tax_amount"] == "50000.00"

    def test_legal_entity_above_threshold(self) -> None:
        """Persona jurídica, above 27 UVT → ReteRenta 3.5%."""
        result = calculate(self.CUSTOMER_LEGAL, self.ITEM_GOODS, Decimal("2000000.00"))
        assert result[0][0]["withholding_tax_rate"] == "3.50"
        assert result[0][0]["tax_amount"] == "70000.00"

    def test_below_uvt_threshold_no_reterenta(self) -> None:
        """Below 27 UVT → NO ReteRenta."""
        small_item = [
            {
                "code_reference": "PROD-001",
                "price": "50000.00",
                "quantity": "1",
                "discount_rate": "0.00",
            }
        ]
        result = calculate(self.CUSTOMER_NATURAL, small_item, Decimal("50000.00"))
        # 50_000 < 1_269_000 → no ReteRenta
        assert 0 in result
        assert len(result[0]) == 0

    def test_autorretenedor_no_reterenta(self) -> None:
        """Autorretenedor (tribute_code "08") → NO ReteRenta."""
        result = calculate(
            self.CUSTOMER_AUTORRETENEDOR, self.ITEM_GOODS, Decimal("2000000.00")
        )
        assert 0 in result
        # May still have other withholdings, but NOT ReteRenta
        codes = [w["code"] for w in result[0]]
        assert "06" not in codes

    def test_services_rate_is_4_percent(self) -> None:
        """Services items (hour unit measure) → ReteRenta 4.0%."""
        service_items = [
            {
                "code_reference": "SRV-001",
                "price": "2000000.00",
                "quantity": "1",
                "discount_rate": "0.00",
                "unit_measure_code": "158",  # hour
            }
        ]
        result = calculate(self.CUSTOMER_NATURAL, service_items, Decimal("2000000.00"))
        assert result[0][0]["withholding_tax_rate"] == "4.00"
        assert result[0][0]["tax_amount"] == "80000.00"

    def test_reterenta_distributed_proportionally(self) -> None:
        """Multiple items → ReteRenta distributed by gross value."""
        items = [
            {
                "code_reference": "PROD-A",
                "price": "1500000.00",
                "quantity": "1",
                "discount_rate": "0.00",
            },
            {
                "code_reference": "PROD-B",
                "price": "500000.00",
                "quantity": "1",
                "discount_rate": "0.00",
            },
        ]
        total_gross = Decimal("2000000.00")  # > 27*47000 = 1_269_000
        result = calculate(self.CUSTOMER_NATURAL, items, total_gross)
        # total ReteRenta = 2_000_000 * 2.5/100 = 50_000
        # Item A proportion: 1_500_000/2_000_000 = 0.75 → 37_500
        # Item B proportion: 500_000/2_000_000 = 0.25 → 12_500
        assert len(result[0]) == 1
        assert len(result[1]) == 1
        assert result[0][0]["tax_amount"] == "37500.00"
        assert result[1][0]["tax_amount"] == "12500.00"


# ═══════════════════════════════════════════════════════════════════════════
# ReteIVA — code "05"
# ═══════════════════════════════════════════════════════════════════════════


class TestReteIVA:
    """Covers: Gran Contribuyente, Autorretenedor, non-applicable customers."""

    CUSTOMER_GRAN_CONTRIBUYENTE = {
        "tribute_code": "22",
        "legal_organization_code": "1",
        "municipality_code": "11001",
    }
    CUSTOMER_STANDARD = {
        "tribute_code": "01",
        "legal_organization_code": "2",
        "municipality_code": "11001",
    }

    ITEM_WITH_IVA = [
        {
            "code_reference": "PROD-001",
            "price": "100000.00",
            "quantity": "1",
            "discount_rate": "0.00",
            "taxes": [{"code": "01", "rate": "19.00"}],
        }
    ]

    def test_gran_contribuyente_triggers_reteiva(self) -> None:
        """Gran Contribuyente (tribute "22") → ReteIVA on IVA portion."""
        result = _get_reteiva_per_item(self.ITEM_WITH_IVA, "22")
        # gross=100_000, iva = 100_000 * 19/119 = 15966.39
        # reteiva = 15966.39 * 15/100 = 2394.96
        assert 0 in result
        assert result[0] == Decimal("2394.96")

    def test_autorretenedor_triggers_reteiva(self) -> None:
        """Autorretenedor (tribute "08") → ReteIVA."""
        result = _get_reteiva_per_item(self.ITEM_WITH_IVA, "08")
        assert 0 in result
        assert result[0] == Decimal("2394.96")

    def test_standard_customer_no_reteiva(self) -> None:
        """Standard customer (tribute "01") → NO ReteIVA."""
        result = _get_reteiva_per_item(self.ITEM_WITH_IVA, "01")
        assert result == {}

    def test_item_without_iva_tax_no_reteiva(self) -> None:
        """Item without IVA tax (code "01") → NO ReteIVA."""
        items = [
            {
                "code_reference": "PROD-001",
                "price": "100000.00",
                "quantity": "1",
                "discount_rate": "0.00",
                "taxes": [{"code": "04", "rate": "8.00"}],  # INC, not IVA
            }
        ]
        result = _get_reteiva_per_item(items, "22")
        assert result == {}


# ═══════════════════════════════════════════════════════════════════════════
# ReteICA — code "07"
# ═══════════════════════════════════════════════════════════════════════════


class TestReteICA:
    """Covers: service items with municipal rates, non-service items."""

    SERVICE_ITEM = [
        {
            "code_reference": "SRV-001",
            "price": "500000.00",
            "quantity": "1",
            "discount_rate": "0.00",
            "unit_measure_code": "158",  # hour → service
        }
    ]
    GOODS_ITEM = [
        {
            "code_reference": "PROD-001",
            "price": "500000.00",
            "quantity": "1",
            "discount_rate": "0.00",
            "unit_measure_code": "94",  # unidad → goods
        }
    ]

    def test_service_item_in_bogota(self) -> None:
        """Service item in Bogotá (11001) → ReteICA 0.2%."""
        result = _get_reteica_per_item(self.SERVICE_ITEM, "11001")
        assert 0 in result
        assert result[0] == Decimal("1000.00")  # 500_000 * 0.2 / 100

    def test_goods_item_no_reteica(self) -> None:
        """Goods item → NO ReteICA."""
        result = _get_reteica_per_item(self.GOODS_ITEM, "11001")
        assert result == {}

    def test_unknown_municipality_no_rate(self) -> None:
        """Unknown municipality → 0% rate → no ReteICA."""
        result = _get_reteica_per_item(self.SERVICE_ITEM, "99999")
        assert result == {}


# ═══════════════════════════════════════════════════════════════════════════
# ReteGMF / 4x1000 — code "20"
# ═══════════════════════════════════════════════════════════════════════════


class TestReteGMF:
    """Covers: electronic payment triggers, threshold, cash payment."""

    def test_electronic_payment_above_threshold(self) -> None:
        """Electronic payment (transfer) > 100 UVT → ReteGMF 0.4%."""
        payment_details = [{"payment_method_code": "47"}]  # Transferencia bancaria
        gross_total = Decimal("10000000.00")  # > 100*47000 = 4_700_000
        result = _get_rete_gmf_amount(payment_details, gross_total)
        assert result is not None
        assert result == Decimal("40000.00")  # 10_000_000 * 0.4 / 100

    def test_cash_payment_no_gmf(self) -> None:
        """Cash payment → NO ReteGMF."""
        payment_details = [{"payment_method_code": "10"}]  # Cash
        gross_total = Decimal("10000000.00")
        result = _get_rete_gmf_amount(payment_details, gross_total)
        assert result is None

    def test_below_uvt_threshold_no_gmf(self) -> None:
        """Electronic payment but below 100 UVT → NO ReteGMF."""
        payment_details = [{"payment_method_code": "47"}]
        gross_total = Decimal("1000000.00")  # < 4_700_000
        result = _get_rete_gmf_amount(payment_details, gross_total)
        assert result is None

    def test_no_payment_details_no_gmf(self) -> None:
        """No payment details → NO ReteGMF."""
        result = _get_rete_gmf_amount(None, Decimal("10000000.00"))
        assert result is None

    def test_gmf_distributed_proportionally(self) -> None:
        """Multiple items → ReteGMF distributed proportionally."""
        customer = {
            "tribute_code": "ZZ",
            "legal_organization_code": "2",
            "municipality_code": "11001",
        }
        items = [
            {
                "code_reference": "PROD-A",
                "price": "6000000.00",
                "quantity": "1",
                "discount_rate": "0.00",
            },
            {
                "code_reference": "PROD-B",
                "price": "4000000.00",
                "quantity": "1",
                "discount_rate": "0.00",
            },
        ]
        payment_details = [{"payment_method_code": "47"}]  # Transfer
        result = calculate(customer, items, Decimal("10000000.00"), payment_details)
        # total GMF = 10_000_000 * 0.4/100 = 40_000
        # Item A: 60% → 24_000, Item B: 40% → 16_000
        assert len(result[0]) == 2  # ReteRenta + ReteGMF
        assert len(result[1]) == 2
        # Find GMF entries
        gmf_a = [w for w in result[0] if w["code"] == "20"][0]
        gmf_b = [w for w in result[1] if w["code"] == "20"][0]
        assert gmf_a["tax_amount"] == "24000.00"
        assert gmf_b["tax_amount"] == "16000.00"


# ═══════════════════════════════════════════════════════════════════════════
# Integration — calculate() full flow
# ═══════════════════════════════════════════════════════════════════════════


class TestCalculateIntegration:
    """End-to-end tests combining multiple withholding types."""

    def test_empty_items_returns_empty_dict(self) -> None:
        """No items → empty result."""
        customer = {"tribute_code": "ZZ", "legal_organization_code": "2"}
        result = calculate(customer, [], Decimal("0"))
        assert result == {}

    def test_goods_for_natural_person_no_withholdings(self) -> None:
        """Small purchase by natural person → no withholdings."""
        customer = {
            "tribute_code": "ZZ",
            "legal_organization_code": "2",
            "municipality_code": "11001",
        }
        items = [
            {
                "code_reference": "PROD-001",
                "price": "50000.00",
                "quantity": "1",
                "discount_rate": "0.00",
                "taxes": [{"code": "01", "rate": "19.00"}],
            }
        ]
        payment_details = [{"payment_method_code": "10"}]  # Cash
        result = calculate(customer, items, Decimal("50000.00"), payment_details)
        # Below 27 UVT, cash payment, no autorretenedor → no withholdings
        assert len(result[0]) == 0

    def test_full_withholding_scenario(self) -> None:
        """Service to Gran Contribuyente via transfer → ReteRenta + ReteIVA + ReteICA + ReteGMF."""
        customer = {
            "tribute_code": "22",  # Gran Contribuyente
            "legal_organization_code": "1",  # Persona jurídica
            "municipality_code": "11001",  # Bogotá
        }
        items = [
            {
                "code_reference": "SRV-001",
                "price": "5000000.00",
                "quantity": "1",
                "discount_rate": "0.00",
                "unit_measure_code": "158",  # hour → service
                "taxes": [{"code": "01", "rate": "19.00"}],  # IVA
            }
        ]
        payment_details = [{"payment_method_code": "47"}]  # Transfer
        total_gross = Decimal("5000000.00")
        result = calculate(customer, items, total_gross, payment_details)

        withholdings = result[0]
        codes = {w["code"] for w in withholdings}

        assert "06" in codes  # ReteRenta 4.0% (services) → 200_000
        assert "05" in codes  # ReteIVA on IVA portion → 5_000_000*19/119*15% = 119_747.90
        assert "07" in codes  # ReteICA 0.2% (Bogotá services) → 10_000
        assert "20" in codes  # ReteGMF 0.4% → 20_000

        # Check specific amounts
        for w in withholdings:
            if w["code"] == "06":
                assert w["tax_amount"] == "200000.00"
            elif w["code"] == "05":
                assert w["tax_amount"] == "119747.90"
            elif w["code"] == "07":
                assert w["tax_amount"] == "10000.00"
            elif w["code"] == "20":
                assert w["tax_amount"] == "20000.00"
