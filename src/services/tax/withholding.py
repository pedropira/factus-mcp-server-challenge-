"""
Withholding tax calculator — Colombian DIAN retentions.

Pure functions that determine applicable withholding taxes based on:
  - Customer type (natural person, legal entity, Gran Contribuyente, Autorretenedor)
  - Product type (taxable, excluded, services)
  - Amounts (UVT thresholds)
  - Payment method (electronic → ReteGMF)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.services.tax import config


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


def calculate(
    customer: dict[str, Any],
    items: list[dict[str, Any]],
    gross_total: Decimal,
    payment_details: list[dict[str, Any]] | None = None,
) -> dict[int, list[dict[str, str]]]:
    """Calculate applicable withholding taxes per item.

    Args:
        customer: Customer dict in Factus API format (with tribute_code,
            legal_organization_code, etc.).
        items: List of item dicts (each must have code_reference, price,
            quantity, and optionally taxes, is_excluded).
        gross_total: Sum of all items' price * quantity (before tax).
        payment_details: Payment details (used for ReteGMF detection).

    Returns:
        Dict mapping item index → list of withholding tax dicts in
        Factus API format:
        {
            0: [{"code": "06", "rate": "2.50", "tax_amount": "37500.00"}],
            1: [],
        }
    NOTA: El campo se llama 'rate' (no 'withholding_tax_rate') según
    la documentación oficial de Factus API v2 para items.*.withholding_taxes.*.rate
    """
    result: dict[int, list[dict[str, str]]] = {i: [] for i in range(len(items))}
    if not items:
        return result

    customer_tribute = customer.get("tribute_code", "ZZ")
    org_type = customer.get("legal_organization_code", "2")
    municipality = customer.get("municipality_code", "11001")

    # --- ReteRenta ---
    reterenta_rate = _get_reterenta_rate(customer_tribute, org_type, items)
    if reterenta_rate is not None and gross_total > config.UVT * config.RETE_RENTA_UVT_THRESHOLD:
        reterenta_amount = _round(gross_total * reterenta_rate / Decimal("100"))
        reterenta_dict = {
            "code": "06",
            "rate": f"{reterenta_rate:.2f}",
            "tax_amount": f"{reterenta_amount:.2f}",
        }
        # Distribute ReteRenta proportionally across all items
        for idx, item in enumerate(items):
            item_gross = _item_gross(item)
            if gross_total > Decimal("0"):
                proportion = item_gross / gross_total
                item_amount = _round(reterenta_amount * proportion)
                if item_amount > Decimal("0"):
                    result[idx].append({
                        "code": "06",
            "rate": f"{reterenta_rate:.2f}",
                        "tax_amount": f"{item_amount:.2f}",
                    })
            else:
                result[idx].append(reterenta_dict)

    # --- ReteIVA ---
    reteiva_per_item = _get_reteiva_per_item(items, customer_tribute)
    for idx, amount in reteiva_per_item.items():
        if amount > Decimal("0"):
            result[idx].append({
                "code": "05",
                "rate": f"{config.RETE_IVA_RATE:.2f}",
                "tax_amount": f"{amount:.2f}",
            })

    # --- ReteICA ---
    reteica_per_item = _get_reteica_per_item(items, municipality)
    for idx, amount in reteica_per_item.items():
        if amount > Decimal("0"):
            # Determine the rate used
            rate = _get_reteica_rate(municipality, _is_service_item(items[idx]))
            result[idx].append({
                "code": "07",
                "rate": f"{rate:.2f}",
                "tax_amount": f"{amount:.2f}",
            })

    # --- ReteGMF / 4x1000 ---
    gmf_amount = _get_rete_gmf_amount(payment_details, gross_total)
    if gmf_amount is not None and gmf_amount > Decimal("0"):
        # Distribute ReteGMF proportionally across all items
        for idx, item in enumerate(items):
            item_gross = _item_gross(item)
            if gross_total > Decimal("0"):
                proportion = item_gross / gross_total
                item_gmf = _round(gmf_amount * proportion)
                if item_gmf > Decimal("0"):
                    result[idx].append({
                        "code": "20",
                        "rate": f"{config.RETE_GMF_RATE:.2f}",
                        "tax_amount": f"{item_gmf:.2f}",
                    })

    return result


# ═══════════════════════════════════════════════════════════════════════════
# ReteRenta — code "06"
# ═══════════════════════════════════════════════════════════════════════════


def _get_reterenta_rate(
    customer_tribute: str,
    legal_org_code: str,
    items: list[dict[str, Any]],
) -> Decimal | None:
    """Determine the applicable ReteRenta rate.

    Returns:
        The rate as a percentage (e.g. Decimal("2.50") for 2.5%),
        or None if ReteRenta does not apply.

    Rules:
      - Autorretenedores (tribute_code "08") → NO ReteRenta
      - Persona natural (legal_org_code "2") → 2.5%
      - Persona jurídica (legal_org_code "1") → 3.5%
      - Services items present → 4.0%
    """
    # Autorretenedores handle their own ReteRenta — not applied by seller
    if customer_tribute in config.AUTORRETENEDOR_TRIBUTE_CODES:
        return None

    # Check if there are service-type items (rate 4.0%)
    # We detect services by standard_code or by item name containing service keywords
    # This is a simplified detection — in production, Product should have a type field
    if _has_service_items(items):
        return config.RETE_RENTA_RATE_SERVICES

    # Determine rate based on customer type
    if legal_org_code == "1":
        return config.RETE_RENTA_RATE_LEGAL
    if legal_org_code == "2":
        return config.RETE_RENTA_RATE_NATURAL

    return None


# ═══════════════════════════════════════════════════════════════════════════
# ReteIVA — code "05"
# ═══════════════════════════════════════════════════════════════════════════


def _get_reteiva_per_item(
    items: list[dict[str, Any]],
    customer_tribute: str,
) -> dict[int, Decimal]:
    """Calculate ReteIVA amount for each item.

    ReteIVA applies when:
      - Customer is Gran Contribuyente (tribute_code "22") or Autorretenedor ("08")
      - Item is subject to IVA (has a tax with code "01" and rate > 0)

    Rate: 15% on the IVA portion of the item.
    The IVA portion is calculated as: price * quantity * (rate / (100 + rate))
    """
    result: dict[int, Decimal] = {}

    if customer_tribute not in config.RETE_IVA_APPLICABLE_TRIBUTE_CODES:
        return result

    for idx, item in enumerate(items):
        if _is_excluded(item):
            continue

        gross = _item_gross(item)
        if gross <= Decimal("0"):
            continue

        # Look for IVA tax (code "01") in the item's taxes
        taxes = item.get("taxes", [])
        for tax in taxes:
            if tax.get("code") == "01":
                try:
                    rate = Decimal(tax.get("rate", "0"))
                except Exception:
                    continue
                if rate <= Decimal("0"):
                    continue
                # IVA is included in the price
                iva_amount = _round(gross * rate / (Decimal("100") + rate))
                rete_iva = _round(iva_amount * config.RETE_IVA_RATE / Decimal("100"))
                if rete_iva > Decimal("0"):
                    current = result.get(idx, Decimal("0"))
                    result[idx] = current + rete_iva
                break  # Only one IVA tax per item expected

    return result


# ═══════════════════════════════════════════════════════════════════════════
# ReteICA — code "07"
# ═══════════════════════════════════════════════════════════════════════════


def _get_reteica_per_item(
    items: list[dict[str, Any]],
    municipality_code: str,
) -> dict[int, Decimal]:
    """Calculate ReteICA amount for each service item.

    ReteICA applies to service-type items based on municipal rates.
    """
    result: dict[int, Decimal] = {}

    for idx, item in enumerate(items):
        if not _is_service_item(item):
            continue

        gross = _item_gross(item)
        if gross <= Decimal("0"):
            continue

        rate = _get_reteica_rate(municipality_code, service=True)
        # Check if there's a non-service rate for this municipality
        commercial_rate = _get_reteica_rate(municipality_code, service=False)

        # Use the appropriate rate based on item type
        ic_amount = _round(gross * rate / Decimal("100"))
        if ic_amount > Decimal("0"):
            result[idx] = ic_amount

    return result


def _get_reteica_rate(municipality_code: str, service: bool = True) -> Decimal:
    """Get ReteICA rate for a municipality.

    Args:
        municipality_code: DIAN municipality code (e.g. "11001" for Bogotá).
        service: True for service items, False for commercial.

    Returns:
        Rate percentage (e.g. Decimal("0.20") for 0.2%).
        Returns 0 if municipality not configured.
    """
    if service:
        key = f"{municipality_code}_services"
        if key in config.RETE_ICA_RATES:
            return config.RETE_ICA_RATES[key]

    if municipality_code in config.RETE_ICA_RATES:
        return config.RETE_ICA_RATES[municipality_code]

    return Decimal("0")


# ═══════════════════════════════════════════════════════════════════════════
# ReteGMF / 4x1000 — code "20"
# ═══════════════════════════════════════════════════════════════════════════


def _get_rete_gmf_amount(
    payment_details: list[dict[str, Any]] | None,
    gross_total: Decimal,
) -> Decimal | None:
    """Calculate ReteGMF (4x1000) amount.

    Applies when:
      - Payment is made through the financial system (transfer, card, etc.)
      - Amount exceeds 100 UVT

    Returns:
        Amount to withhold, or None if not applicable.
    """
    if not payment_details:
        return None

    # Check if any payment method triggers ReteGMF
    triggers_gmf = False
    for detail in payment_details:
        method = detail.get("payment_method_code", "")
        if method in config.RETE_GMF_PAYMENT_METHOD_CODES:
            triggers_gmf = True
            break

    if not triggers_gmf:
        return None

    # Check threshold
    threshold = config.UVT * config.RETE_GMF_UVT_THRESHOLD
    if gross_total <= threshold:
        return None

    amount = _round(gross_total * config.RETE_GMF_RATE / Decimal("100"))
    return amount


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _is_excluded(item: dict[str, Any]) -> bool:
    """Check if an item is excluded from taxes.

    Handles both boolean and string representations (Factus API
    maps is_excluded to "true"/"false" strings).
    """
    val = item.get("is_excluded", False)
    if isinstance(val, bool):
        return val
    return str(val).lower() == "true"


def _is_autorretenedor(customer: dict[str, Any]) -> bool:
    """Check if customer is Gran Contribuyente con Autorretención."""
    return customer.get("tribute_code", "") in config.AUTORRETENEDOR_TRIBUTE_CODES


def _is_gran_contribuyente(customer: dict[str, Any]) -> bool:
    """Check if customer is Gran Contribuyente (with or without autorretención)."""
    return customer.get("tribute_code", "") in config.RETE_IVA_APPLICABLE_TRIBUTE_CODES


def _has_service_items(items: list[dict[str, Any]]) -> bool:
    """Detect if any items are service-type.

    Simple heuristic: checks for standard_code or name hints.
    In production, Product model should have a type field.
    """
    for item in items:
        if _is_service_item(item):
            return True
    return False


def _is_service_item(item: dict[str, Any]) -> bool:
    """Check if an individual item is a service.

    Uses standard_code to detect services:
    - Standard code "1" (estándar contribuyente) could be goods or services
    - Standard code "2" (UNSPSC) would need category lookup
    - For now, items with non-physical unit measures (hours, days, months) are services
    """
    # Unit measures that typically indicate services
    service_units = {"158", "151", "154", "156", "104"}  # hour, day, month, year, percentage
    unit = item.get("unit_measure_code", "")
    return unit in service_units


def _item_gross(item: dict[str, Any]) -> Decimal:
    """Calculate gross value for an item (price * quantity, minus discount)."""
    try:
        price = Decimal(str(item.get("price", "0")))
        qty = Decimal(str(item.get("quantity", "1")))
        disc = Decimal(str(item.get("discount_rate", "0")))
    except Exception:
        return Decimal("0")

    gross = price * qty * (Decimal("1") - disc / Decimal("100"))
    return _round(gross)


def _round(value: Decimal) -> Decimal:
    """Round to 2 decimal places (rounded half-up)."""
    return value.quantize(Decimal("0.01"))
