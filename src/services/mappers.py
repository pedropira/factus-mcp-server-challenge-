"""
Factus API v2 payload mappers.

Convert local DB models (Customer, Product, Establishment) into the
dict format expected by the Factus API v2 endpoints.

Key mappings:
  - Factus API IDs → DIAN codes (for identification_document, unit_measure)
  - Factus API tribute IDs → DIAN tribute codes
  - Field name normalization (e.g. municipality_id → municipality_code)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from src.schemas.models import Customer, Establishment, Product

# ═══════════════════════════════════════════════════════════════════════════
# ID → Code Mappings
# ═══════════════════════════════════════════════════════════════════════════
# The Factus API v2 expects DIAN codes (strings), not Factus internal IDs.
# These maps convert Factus DB IDs to DIAN codes.

# Factus identification_document_id → DIAN code
IDENTIFICATION_DOCUMENT_MAP: dict[int, str] = {
    1: "11",    # Registro Civil
    2: "12",    # Tarjeta de Identidad
    3: "13",    # Cédula de Ciudadanía
    4: "21",    # Tarjeta de Extranjería
    5: "22",    # Cédula de Extranjería
    6: "31",    # NIT
    7: "41",    # Pasaporte
    8: "42",    # Documento de Identificación Extranjero
    9: "47",    # PEP (Permiso Especial de Permanencia)
    10: "31",   # NIT otro país (maps to NIT DIAN code)
    11: "11",   # NUIP (maps to Registro Civil DIAN code)
}

# Factus tribute_id → DIAN tribute_code
TRIBUTE_MAP: dict[str, str] = {
    "1": "01",     # IVA Régimen Común
    "2": "02",     # IVA Régimen Simplificado
    "21": "ZZ",    # No aplica
    "22": "22",    # Gran Contribuyente
    "23": "08",    # Autorretenedor (Gran Contribuyente con Autorretención)
    "24": "23",    # Agente de Retención IVA
    "25": "25",    # Régimen Simple de Tributación
}

# Factus unit_measure_id → DIAN code
UNIT_MEASURE_MAP: dict[int, str] = {
    70: "94",      # Unidad
    46: "97",      # Kilo
    96: "98",      # Libra
    94: "99",      # Tonelada
    45: "100",     # Metro
    30: "101",     # Metro cuadrado
    66: "102",     # Metro cúbico
    85: "103",     # Litro
    87: "104",     # Galón
    77: "105",     # Docena
    79: "106",     # Paquete
    76: "107",     # Par
    80: "108",     # Caja
    158: "109",    # Hora
    151: "110",    # Día
    154: "111",    # Mes
    156: "112",    # Año
    104: "113",    # Porcentaje
    47: "114",     # Gramo
    5: "115",      # Mililitro
    81: "116",     # Barril
    414: "117",    # KGM (kilogramo masa)
    874: "118",    # GLL (galón)
}

# Factus standard_code_id → DIAN standard_code
# IMPORTANTE: DIAN usa "999" para "Estándar de adopción del contribuyente"
STANDARD_CODE_MAP: dict[int, str] = {
    1: "999",  # Estándar de adopción del contribuyente
    2: "2",    # UNSPSC
    3: "3",    # Partida arancelaria
    4: "4",    # GTIN
}

# Factus item_tribute_id → DIAN tax code
ITEM_TRIBUTE_TAX_CODE_MAP: dict[int, str] = {
    1: "01",   # IVA
    2: "04",   # INC
    3: "01",   # IVA e INC (usar IVA como default)
    4: "01",   # No causa (no tax, rate 0)
}


# ═══════════════════════════════════════════════════════════════════════════
# Customer → Factus dict
# ═══════════════════════════════════════════════════════════════════════════


def customer_to_factus_dict(
    customer: Customer,
    establishment: Optional[Establishment] = None,
) -> dict[str, Any]:
    """Convert a Customer DB model to a Factus API customer dict.

    Args:
        customer: Customer model instance.
        establishment: Optional Establishment for additional context
            (address, municipality).

    Returns:
        Dict ready to use as the ``customer`` field in Factus API requests.
    """
    result: dict[str, Any] = {
        "identification_document_code": _map_identification_document_id(
            customer.identification_document_id
        ),
        "identification": customer.identification,
        "dv": customer.dv or "",
        "company": customer.company or "",
        "trade_name": customer.trade_name or "",
        "names": customer.names or "",
        "address": customer.address or "",
        "email": customer.email or "",
        "phone": customer.phone or "",
        "legal_organization_code": _map_legal_organization_id(
            customer.legal_organization_id
        ),
        "tribute_code": _map_tribute_id(customer.tribute_id),
        "municipality_code": customer.municipality_id or "",
    }

    # Remove empty/None values to keep payload clean
    return _clean_dict(result)


# ═══════════════════════════════════════════════════════════════════════════
# Provider (raw dict) → Factus dict
# ═══════════════════════════════════════════════════════════════════════════
# Support documents and adjustment notes accept a raw ``provider`` dict from
# the MCP tool. The LLM may pass Factus API fields (``identification_document_code``)
# OR user-friendly fields (``identification_document_id``). This mapper handles
# both and fills missing required fields with sensible defaults.
#
# Accepted field formats:
#   - ``identification_document_id`` (int)   → ``identification_document_code`` (str)
#   - ``identification_document_code`` (str) → passed through
#   - ``legal_organization_id`` (str)        → ``legal_organization_code`` (str)
#   - ``tribute_id`` (str)                   → ``tribute_code`` (str)
#   - ``municipality_id`` (str)              → ``municipality_code`` (str)
# ═══════════════════════════════════════════════════════════════════════════


def provider_to_factus_dict(provider: dict) -> dict[str, Any]:
    """Convert a raw provider dict to Factus API format.

    Accepts both user-friendly fields (``identification_document_id``)
    and Factus API fields (``identification_document_code``). Missing
    required fields are filled with sensible defaults so the Factus API
    has a valid payload.

    Args:
        provider: Raw provider dict from the MCP tool.

    Returns:
        Dict ready to use as the ``provider`` field in Factus API requests.
    """
    result: dict[str, Any] = {}

    # ── identification_document ──
    if "identification_document_code" in provider:
        result["identification_document_code"] = provider["identification_document_code"]
    elif "identification_document_id" in provider:
        result["identification_document_code"] = _map_identification_document_id(
            provider["identification_document_id"]
        )
    else:
        result["identification_document_code"] = "13"  # CC por defecto

    # ── Pass-through fields ──
    for field in ("identification", "dv", "company", "trade_name", "names",
                  "address", "email", "phone"):
        result[field] = provider.get(field, "")

    # ── legal_organization ──
    if "legal_organization_code" in provider:
        result["legal_organization_code"] = provider["legal_organization_code"]
    elif "legal_organization_id" in provider:
        result["legal_organization_code"] = _map_legal_organization_id(
            provider["legal_organization_id"]
        )
    else:
        result["legal_organization_code"] = "2"  # Persona Natural por defecto

    # ── tribute ──
    if "tribute_code" in provider:
        result["tribute_code"] = provider["tribute_code"]
    elif "tribute_id" in provider:
        result["tribute_code"] = _map_tribute_id(provider["tribute_id"])
    else:
        result["tribute_code"] = "ZZ"  # No aplica por defecto

    # ── municipality ──
    if "municipality_code" in provider:
        result["municipality_code"] = provider["municipality_code"]
    elif "municipality_id" in provider:
        result["municipality_code"] = provider["municipality_id"]
    else:
        result["municipality_code"] = "11001"  # Bogotá por defecto

    return _clean_dict(result)


# ═══════════════════════════════════════════════════════════════════════════
# Product → Factus item dict
# ═══════════════════════════════════════════════════════════════════════════


def product_to_factus_dict(
    product: Product,
    quantity: int | Decimal | str,
    discount_rate: str = "0.00",
) -> dict[str, Any]:
    """Convert a Product DB model to a Factus API item dict.

    Args:
        product: Product model instance.
        quantity: Quantity of the product.
        discount_rate: Discount rate percentage (default "0.00").

    Returns:
        Dict ready to use as an item in the Factus API items array.
    """
    qty = _format_decimal(quantity)
    price = _format_decimal(product.price)
    disc = discount_rate if discount_rate else "0.00"

    # Calculate total discount
    total_discount = _format_decimal(
        Decimal(price) * Decimal(qty) * Decimal(disc) / Decimal("100")
    )

    # Build taxes array
    tax_code = _map_item_tribute_to_tax_code(product.tribute_id)
    taxes: list[dict[str, str]] = [
        {"code": tax_code, "rate": product.tax_rate}
    ]

    result: dict[str, Any] = {
        "code_reference": product.code_reference,
        "name": product.name,
        "quantity": qty,
        "discount_rate": disc,
        "price": price,
        "taxes": taxes,
        "unit_measure_code": _map_unit_measure_id(product.unit_measure_id),
        "standard_code": _map_standard_code_id(product.standard_code_id),
        "is_excluded": str(product.is_excluded).lower(),
        "total_discount": total_discount,
    }

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Internal mapping helpers
# ═══════════════════════════════════════════════════════════════════════════


def _map_identification_document_id(factus_id: int) -> str:
    """Convert Factus identification_document ID to DIAN code.

    Args:
        factus_id: Factus API ID (1-11).

    Returns:
        DIAN code string (e.g. "31" for NIT).
        Falls back to "13" (Cédula de Ciudadanía) if unknown.
    """
    return IDENTIFICATION_DOCUMENT_MAP.get(factus_id, "13")


def _map_tribute_id(tribute_id: str | None) -> str:
    """Convert Factus tribute_id to DIAN tribute_code.

    Args:
        tribute_id: Factus API tribute ID (e.g. "21", "22", "23").

    Returns:
        DIAN tribute code (e.g. "ZZ", "22", "08").
        Falls back to "ZZ" (No aplica) if unknown or None.
    """
    if tribute_id is None:
        return "ZZ"
    return TRIBUTE_MAP.get(tribute_id, "ZZ")


def _map_legal_organization_id(org_id: str | None) -> str:
    """Map legal organization ID to DIAN code.

    The Factus API IDs and DIAN codes are the same for this field:
      1 = Persona Jurídica
      2 = Persona Natural

    Args:
        org_id: Factus API ID or None.

    Returns:
        DIAN code ("1" or "2").
        Falls back to "2" (Persona Natural) if unknown.
    """
    if org_id in ("1", "2"):
        return org_id
    return "2"


def _map_unit_measure_id(factus_id: int) -> str:
    """Convert Factus unit_measure ID to DIAN code.

    Args:
        factus_id: Factus API unit measure ID.

    Returns:
        DIAN unit measure code.
        Falls back to "94" (Unidad) if unknown.
    """
    return UNIT_MEASURE_MAP.get(factus_id, "94")


def _map_standard_code_id(factus_id: int) -> str:
    """Convert Factus standard_code ID to DIAN code.

    Args:
        factus_id: Factus API standard code ID.

    Returns:
        DIAN standard code.
        Falls back to "999" (Estándar de adopción del contribuyente) if unknown.
    """
    return STANDARD_CODE_MAP.get(factus_id, "999")


def _map_item_tribute_to_tax_code(tribute_id: int) -> str:
    """Convert Factus item_tribute_id to DIAN tax code.

    Args:
        tribute_id: Factus API item tribute ID.

    Returns:
        DIAN tax code (e.g. "01" for IVA).
        Falls back to "01" if unknown.
    """
    return ITEM_TRIBUTE_TAX_CODE_MAP.get(tribute_id, "01")


# ═══════════════════════════════════════════════════════════════════════════
# Utility helpers
# ═══════════════════════════════════════════════════════════════════════════


def _format_decimal(value: int | Decimal | str) -> str:
    """Format a numeric value as a string with 2 decimal places."""
    return f"{Decimal(str(value)):.2f}"


def _clean_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove keys with None or empty string values."""
    return {k: v for k, v in d.items() if v not in (None, "")}
