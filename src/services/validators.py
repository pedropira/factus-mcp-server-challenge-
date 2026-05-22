"""
InvoiceValidator — pre-submit DIAN validation rules.

Validates invoice payloads before sending them to the Factus API.
Catches missing or invalid fields early and provides clear error messages.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


class InvoiceValidator:
    """Pre-submit validation for Factus API invoice payloads.

    All methods are static and return a list of error messages.
    An empty list means the input is valid.
    """

    REQUIRED_CUSTOMER_FIELDS: list[str] = [
        "identification_document_code",
        "identification",
        "email",
        "address",
        "municipality_code",
        "legal_organization_code",
        "tribute_code",
    ]

    REQUIRED_ITEM_FIELDS: list[str] = [
        "code_reference",
        "name",
        "quantity",
        "price",
        "unit_measure_code",
        "standard_code",
    ]

    @classmethod
    def validate(cls, payload: dict[str, Any]) -> list[str]:
        """Run all validators and return combined error list.

        Args:
            payload: The Factus API payload dict.

        Returns:
            List of error messages (empty if valid).
        """
        errors: list[str] = []
        errors.extend(cls.validate_customer(payload.get("customer", {})))
        errors.extend(cls.validate_items(payload.get("items", [])))
        errors.extend(cls.validate_payment(payload.get("payment_details")))
        return errors

    # ── Customer validation ──────────────────────────────────────────────

    @classmethod
    def validate_customer(cls, customer: dict[str, Any]) -> list[str]:
        """Validate customer fields required by DIAN.

        Returns:
            List of error messages for missing or invalid fields.
        """
        errors: list[str] = []

        if not customer:
            return ["Customer data is required"]

        for field in cls.REQUIRED_CUSTOMER_FIELDS:
            if not customer.get(field):
                errors.append(f"Customer missing required field: {field}")

        # At least one of names or company must be present
        if not customer.get("names") and not customer.get("company"):
            errors.append(
                "Customer must have at least one of: names, company"
            )

        return errors

    # ── Items validation ────────────────────────────────────────────────

    @classmethod
    def validate_items(cls, items: list[dict[str, Any]]) -> list[str]:
        """Validate each item in the items array.

        Returns:
            List of error messages for missing or invalid item fields.
        """
        errors: list[str] = []

        if not items:
            return ["At least one item is required"]

        for idx, item in enumerate(items):
            idx_label = idx  # 0-based index for error messages

            # Check required fields
            for field in cls.REQUIRED_ITEM_FIELDS:
                if not item.get(field):
                    errors.append(
                        f"Item [{idx_label}] missing required field: {field}"
                    )

            # Price must be >= 0
            try:
                price = Decimal(str(item.get("price", "0")))
                if price < Decimal("0"):
                    errors.append(
                        f"Item [{idx_label}] has negative price: {price}"
                    )
            except Exception:
                errors.append(
                    f"Item [{idx_label}] has invalid price value"
                )

            # Quantity must be > 0
            try:
                qty = Decimal(str(item.get("quantity", "0")))
                if qty <= Decimal("0"):
                    errors.append(
                        f"Item [{idx_label}] must have quantity greater than 0"
                    )
            except Exception:
                errors.append(
                    f"Item [{idx_label}] has invalid quantity value"
                )

            # At least one tax entry
            taxes = item.get("taxes", [])
            if not taxes:
                errors.append(
                    f"Item [{idx_label}] must have at least one tax entry"
                )

            # Check each tax entry has code and rate
            for tidx, tax in enumerate(taxes):
                if not tax.get("code"):
                    errors.append(
                        f"Item [{idx_label}] tax [{tidx}] missing code"
                    )
                if not tax.get("rate"):
                    errors.append(
                        f"Item [{idx_label}] tax [{tidx}] missing rate"
                    )

        return errors

    # ── Payment details validation ────────────────────────────────────────

    @classmethod
    def validate_payment(
        cls, payment_details: list[dict[str, Any]] | None
    ) -> list[str]:
        """Validate payment details.

        Returns:
            List of error messages for missing or invalid payment fields.
        """
        errors: list[str] = []

        if not payment_details:
            return ["At least one payment detail is required"]

        for idx, detail in enumerate(payment_details):
            if not detail.get("payment_form"):
                errors.append(
                    f"Payment detail [{idx}] missing required field: payment_form"
                )
            if not detail.get("payment_method_code"):
                errors.append(
                    f"Payment detail [{idx}] missing required field: payment_method_code"
                )

        return errors
