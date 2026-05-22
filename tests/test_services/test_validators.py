"""
Tests for InvoiceValidator — pre-submit DIAN validation rules.

Covers:
  - validate_customer()
  - validate_items()
  - validate_payment()
  - validate() (combined)
"""

from __future__ import annotations

import pytest

from src.services.validators import InvoiceValidator


# ═══════════════════════════════════════════════════════════════════════════
# validate_customer
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateCustomer:
    def test_valid_customer_returns_no_errors(self) -> None:
        customer = {
            "identification_document_code": "13",
            "identification": "123456789",
            "email": "test@example.com",
            "address": "Calle 123",
            "municipality_code": "11001",
            "legal_organization_code": "2",
            "tribute_code": "ZZ",
            "names": "John Doe",
        }
        errors = InvoiceValidator.validate_customer(customer)
        assert errors == []

    def test_missing_required_fields(self) -> None:
        customer = {
            "identification_document_code": "13",
            "email": "test@example.com",
        }
        errors = InvoiceValidator.validate_customer(customer)
        assert "Customer missing required field: identification" in errors
        assert "Customer missing required field: address" in errors
        assert "Customer missing required field: municipality_code" in errors
        assert "Customer missing required field: legal_organization_code" in errors
        assert "Customer missing required field: tribute_code" in errors

    def test_empty_customer(self) -> None:
        errors = InvoiceValidator.validate_customer({})
        assert "Customer data is required" in errors

    def test_no_names_or_company(self) -> None:
        customer = {
            "identification_document_code": "13",
            "identification": "123456789",
            "email": "t@t.com",
            "address": "Calle 1",
            "municipality_code": "11001",
            "legal_organization_code": "2",
            "tribute_code": "ZZ",
        }
        errors = InvoiceValidator.validate_customer(customer)
        assert "Customer must have at least one of: names, company" in errors


# ═══════════════════════════════════════════════════════════════════════════
# validate_items
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateItems:
    def test_valid_items_returns_no_errors(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "name": "Producto",
                "quantity": "1.00",
                "price": "10000.00",
                "unit_measure_code": "94",
                "standard_code": "1",
                "taxes": [{"code": "01", "rate": "19.00"}],
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert errors == []

    def test_empty_items(self) -> None:
        errors = InvoiceValidator.validate_items([])
        assert "At least one item is required" in errors

    def test_missing_required_fields(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "price": "10000.00",
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert 'Item [0] missing required field: name' in errors
        assert 'Item [0] missing required field: quantity' in errors
        assert 'Item [0] missing required field: unit_measure_code' in errors
        assert 'Item [0] missing required field: standard_code' in errors

    def test_negative_price(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "name": "Test",
                "quantity": "1.00",
                "price": "-100.00",
                "unit_measure_code": "94",
                "standard_code": "1",
                "taxes": [{"code": "01", "rate": "19.00"}],
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert any("negative price" in e for e in errors)

    def test_zero_quantity(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "name": "Test",
                "quantity": "0.00",
                "price": "10000.00",
                "unit_measure_code": "94",
                "standard_code": "1",
                "taxes": [{"code": "01", "rate": "19.00"}],
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert 'Item [0] must have quantity greater than 0' in errors

    def test_no_taxes(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "name": "Test",
                "quantity": "1.00",
                "price": "10000.00",
                "unit_measure_code": "94",
                "standard_code": "1",
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert 'Item [0] must have at least one tax entry' in errors

    def test_tax_missing_code_or_rate(self) -> None:
        items = [
            {
                "code_reference": "PROD-001",
                "name": "Test",
                "quantity": "1.00",
                "price": "10000.00",
                "unit_measure_code": "94",
                "standard_code": "1",
                "taxes": [{"rate": "19.00"}],  # Missing code
            }
        ]
        errors = InvoiceValidator.validate_items(items)
        assert 'Item [0] tax [0] missing code' in errors


# ═══════════════════════════════════════════════════════════════════════════
# validate_payment
# ═══════════════════════════════════════════════════════════════════════════


class TestValidatePayment:
    def test_valid_payment_returns_no_errors(self) -> None:
        details = [
            {
                "payment_form": "1",
                "payment_method_code": "10",
            }
        ]
        errors = InvoiceValidator.validate_payment(details)
        assert errors == []

    def test_missing_payment_details(self) -> None:
        errors = InvoiceValidator.validate_payment(None)
        assert "At least one payment detail is required" in errors
        errors = InvoiceValidator.validate_payment([])
        assert "At least one payment detail is required" in errors

    def test_missing_required_fields(self) -> None:
        details = [{"amount": "100000.00"}]
        errors = InvoiceValidator.validate_payment(details)
        assert 'Payment detail [0] missing required field: payment_form' in errors
        assert 'Payment detail [0] missing required field: payment_method_code' in errors


# ═══════════════════════════════════════════════════════════════════════════
# validate() — combined
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateCombined:
    def test_valid_payload_returns_empty(self) -> None:
        payload = {
            "customer": {
                "identification_document_code": "13",
                "identification": "123456789",
                "email": "t@t.com",
                "address": "Calle 1",
                "municipality_code": "11001",
                "legal_organization_code": "2",
                "tribute_code": "ZZ",
                "names": "John Doe",
            },
            "items": [
                {
                    "code_reference": "PROD-001",
                    "name": "Producto",
                    "quantity": "1.00",
                    "price": "10000.00",
                    "unit_measure_code": "94",
                    "standard_code": "1",
                    "taxes": [{"code": "01", "rate": "19.00"}],
                }
            ],
            "payment_details": [
                {"payment_form": "1", "payment_method_code": "10"}
            ],
        }
        errors = InvoiceValidator.validate(payload)
        assert errors == []

    def test_empty_payload_returns_errors(self) -> None:
        errors = InvoiceValidator.validate({})
        assert len(errors) >= 3  # Customer, items, and payment errors
        assert "Customer data is required" in errors
        assert "At least one item is required" in errors
        assert "At least one payment detail is required" in errors
