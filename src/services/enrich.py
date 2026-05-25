"""
Shared enrichment utilities for Factus API payloads.

Calcula totales, impuestos y payment_details.amount automáticamente
para facturas, notas crédito y notas de ajuste.

Extraído de InvoiceService._enrich_with_totals para reuso.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def enrich_with_totals(payload: dict) -> dict:
    """Calculate and set totals for a Factus API payload.

    Para cada item:
      1. gross = price * quantity * (1 - discount_rate/100)
      2. Para cada impuesto en item.taxes[]:
           tax_amount = gross * (rate / (100 + rate))
         (el precio YA incluye IVA)
      3. Suma todos los impuestos del item

    Total general = suma de gross + suma de taxes.
    Allowance charges: descuentos restan, recargos suman.

    Setea payment_details[0].amount al total calculado.

    Args:
        payload: Factus API payload con items, payment_details,
                 y opcionalmente allowance_charges.

    Returns:
        El mismo payload con totals poblados.
    """
    items = payload.get("items", [])
    total_gross = Decimal("0")
    total_tax = Decimal("0")

    for item in items:
        gross, tax = _calculate_item_taxes(item)
        total_gross += gross
        total_tax += tax

    # Include allowance_charges in total
    allowance_total = Decimal("0")
    allowance_charges = payload.get("allowance_charges", [])
    if allowance_charges:
        for ac in allowance_charges:
            try:
                amount = Decimal(ac.get("amount", "0"))
            except Exception:
                amount = Decimal("0")
            if ac.get("is_surcharge", False):
                allowance_total += amount
            else:
                allowance_total -= amount

    total = total_gross + total_tax + allowance_total

    details = payload.get("payment_details", [])
    if details:
        details[0]["amount"] = f"{total:.2f}"

    return payload


def _calculate_item_taxes(item: dict[str, Any]) -> tuple[Decimal, Decimal]:
    """Calculate gross and tax amounts for a single item.

    El precio en Factus API incluye impuestos (CON IVA incluído).
    Para extraer el impuesto:
        tax_amount = gross * (rate / (100 + rate))

    Args:
        item: Item dict con price, quantity, discount_rate, taxes[].

    Returns:
        Tuple of (gross_value, tax_amount) as Decimals.
    """
    try:
        price = Decimal(str(item.get("price", "0")))
        qty = Decimal(str(item.get("quantity", "1")))
        disc = Decimal(str(item.get("discount_rate", "0")))
    except Exception:
        return Decimal("0"), Decimal("0")

    gross = price * qty * (Decimal("1") - disc / Decimal("100"))
    gross = gross.quantize(Decimal("0.01"))

    total_tax = Decimal("0")
    taxes = item.get("taxes", [])
    for tax_entry in taxes:
        try:
            rate = Decimal(tax_entry.get("rate", "0"))
        except Exception:
            continue
        if rate > Decimal("0"):
            # Price includes tax, so tax = gross * (rate / (100 + rate))
            tax_amount = gross * rate / (Decimal("100") + rate)
            tax_amount = tax_amount.quantize(Decimal("0.01"))
            total_tax += tax_amount

    total_tax = total_tax.quantize(Decimal("0.01"))
    return gross, total_tax
