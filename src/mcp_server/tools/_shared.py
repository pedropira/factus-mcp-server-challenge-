"""
Shared utility functions for MCP tool modules.

Estas funciones están extraídas de los tool modules individuales para
evitar duplicación. Si ves _json_safe o _item_to_factus en un tool file,
importalas de acá en lugar de redefinirlas.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.services.invoice_service import FactusApiError
from src.services.mappers import (
    _map_item_tribute_to_tax_code,
    _map_standard_code_id,
    _map_unit_measure_id,
)


def error_body(e: Exception) -> str:
    """Extract a detailed error message, including Factus API body when available.

    Args:
        e: The exception (may be FactusApiError or generic).

    Returns:
        Human-readable error string with status and body details.
    """
    if isinstance(e, FactusApiError):
        details = f"{e} | status={e.status_code}"
        if e.body:
            details += f" | body={e.body}"
        return details
    return str(e)


def json_safe(d: dict) -> dict:
    """Convert Decimal values to strings for JSON serialization."""
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in d.items()}


def item_to_factus(item: object) -> dict:
    """Convert _InvoiceItemInput to Factus API item dict with mapped codes.

    Mapea los IDs internos (unit_measure_id, standard_code_id, tribute_id)
    a los códigos DIAN que la API de Factus espera, y arma el array de
    taxes con code + rate.
    """
    d = json_safe(item.model_dump(exclude_none=True))
    d["unit_measure_code"] = _map_unit_measure_id(item.unit_measure_id)
    d["standard_code"] = _map_standard_code_id(item.standard_code_id)
    tax_code = _map_item_tribute_to_tax_code(item.tribute_id)
    d["taxes"] = [{"code": tax_code, "rate": item.tax_rate}]
    d.pop("unit_measure_id", None)
    d.pop("standard_code_id", None)
    d.pop("tribute_id", None)
    return d
