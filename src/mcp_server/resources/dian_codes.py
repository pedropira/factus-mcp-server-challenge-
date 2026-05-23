"""
MCP resources for DIAN codes and tax configuration.

Exposes read-only data as MCP resources to prevent AI agent hallucinations.
All data comes from `src.core.constants` and `src.services.tax.config`.

URI scheme:
  factus://dian/{category}     — DIAN and Factus API code mappings
  factus://config/{name}       — Tax configuration constants
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# ═══════════════════════════════════════════════════════════════════════════
# URI → Source mapping
# ═══════════════════════════════════════════════════════════════════════════

# Maps factus://dian/{category} path → (source_dict, description)
_DIAN_RESOURCE_MAP: dict[str, tuple[dict[str, Any], str]] = {}

# We populate lazily to avoid import overhead at module load time.
def _build_dian_map() -> dict[str, tuple[dict[str, Any], str]]:
    """Build the DIAN resource map, importing constants on first call."""
    from src.core.constants import DIAN_CONSTANTS, FACTUS_API_IDS

    return {
        "document-types": (
            DIAN_CONSTANTS["document_types"],
            "DIAN official document type codes (cédula, NIT, pasaporte, etc.)",
        ),
        "identification-types": (
            FACTUS_API_IDS["identification_document_ids"],
            "Factus API identification type IDs (internal ids, not DIAN codes)",
        ),
        "tribute-codes": (
            FACTUS_API_IDS["customer_tribute_ids"],
            "Customer tribute codes (IVA régimen común, gran contribuyente, etc.)",
        ),
        "unit-measures": (
            FACTUS_API_IDS["unit_measure_ids"],
            "Unit of measure codes (unidad, kilogramo, metro, etc.)",
        ),
        "payment-forms": (
            DIAN_CONSTANTS["payment_forms"],
            "Payment form codes (contado=1, crédito=2)",
        ),
        "payment-methods": (
            DIAN_CONSTANTS["payment_methods"],
            "Payment method codes (efectivo=10, transferencia=47, etc.)",
        ),
        "standard-codes": (
            DIAN_CONSTANTS["standard_codes"],
            "Product standard identification codes (UNSPSC, GTIN, etc.)",
        ),
        "allowance-charge-concepts": (
            DIAN_CONSTANTS["allowance_charge_concepts"],
            "Allowance and charge reason codes (descuentos y recargos)",
        ),
        "correction-codes": (
            DIAN_CONSTANTS["correction_codes"],
            "Credit note correction concept codes (devolución, anulación, etc.)",
        ),
    }


def register(server: FastMCP) -> None:
    """Register all DIAN and tax config resources on the MCP server."""

    # ──────────────────────────────────────────────────────────────────────
    # 1. DIAN codes — dynamic resource via URI template
    # ──────────────────────────────────────────────────────────────────────

    @server.resource("factus://dian/{category}")
    async def get_dian_codes(category: str) -> str:
        """Get a DIAN or Factus API code mapping by category.

        Available categories:
          - document-types       DIAN official document type codes
          - identification-types Factus API identification type IDs
          - tribute-codes        Customer tribute codes
          - unit-measures        Unit of measure codes
          - payment-forms        Payment form codes (contado/crédito)
          - payment-methods      Payment method codes
          - standard-codes       Product standard identification codes
          - allowance-charge-concepts  Allowance/charge reason codes
          - correction-codes     Credit note correction concept codes
        """
        dian_map = _build_dian_map()
        entry = dian_map.get(category)
        if entry is None:
            available = ", ".join(sorted(dian_map.keys()))
            return json.dumps(
                {
                    "error": f"Unknown DIAN category '{category}'",
                    "available_categories": available,
                },
                indent=2,
                ensure_ascii=False,
            )
        data, _description = entry
        return json.dumps(data, indent=2, ensure_ascii=False)

    # ──────────────────────────────────────────────────────────────────────
    # 2. Tax configuration — separate resources for clarity
    # ──────────────────────────────────────────────────────────────────────

    @server.resource("factus://config/uvt")
    async def get_uvt_config() -> str:
        """UVT (Unidad de Valor Tributario) value and withholding thresholds.

        Returns the current UVT value in COP and all UVT-based thresholds
        used for determining which withholdings apply.
        """
        from src.services.tax.config import (
            UVT,
            RETE_RENTA_UVT_THRESHOLD,
            SERVICES_UVT_THRESHOLD,
            RETE_GMF_UVT_THRESHOLD,
        )

        return json.dumps(
            {
                "uvt": float(UVT),
                "uvt_cop": f"${UVT:,}",
                "reterenta_goods_uvt": RETE_RENTA_UVT_THRESHOLD,
                "reterenta_services_uvt": SERVICES_UVT_THRESHOLD,
                "rete_gmf_uvt": RETE_GMF_UVT_THRESHOLD,
                "description": (
                    "UVT (Unidad de Valor Tributario) es la unidad de medida "
                    "usada por la DIAN para determinar umbrales de retenciones. "
                    "Si el valor de la operación supera el umbral en UVT, "
                    "la retención aplica."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )

    @server.resource("factus://config/tax-rates")
    async def get_tax_rates() -> str:
        """All tax rates used by the system: IVA, ReteRenta, ReteIVA, ReteICA, ReteGMF."""
        from src.services.tax.config import (
            RETE_RENTA_RATE_NATURAL,
            RETE_RENTA_RATE_LEGAL,
            RETE_RENTA_RATE_SERVICES,
            RETE_IVA_RATE,
            RETE_IVA_SIMPLE_RATE,
            RETE_GMF_RATE,
        )

        return json.dumps(
            {
                "iva": {"rate": "19.00%", "code": "01"},
                "rete_renta": {
                    "natural_person": f"{float(RETE_RENTA_RATE_NATURAL)}%",
                    "legal_entity": f"{float(RETE_RENTA_RATE_LEGAL)}%",
                    "services": f"{float(RETE_RENTA_RATE_SERVICES)}%",
                    "code": "06",
                },
                "rete_iva": {
                    "standard": f"{float(RETE_IVA_RATE)}%",
                    "simple_tax_regime": f"{float(RETE_IVA_SIMPLE_RATE)}%",
                    "code": "05",
                },
                "rete_ica": {
                    "rate_varies_by_municipality": True,
                    "typical_range": "0.20% - 1.00%",
                    "code": "07",
                    "note": "See factus://config/reteica-rates for municipality-specific rates",
                },
                "rete_gmf": {
                    "rate": f"{float(RETE_GMF_RATE)}% (4x1000)",
                    "code": "20",
                    "threshold_uvt": 100,
                },
                "description": (
                    "Tasas de retención aplicables en Colombia. "
                    "Cada tipo de retención tiene su propio código DIAN "
                    "y condiciones de aplicación."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )

    @server.resource("factus://config/reteica-rates")
    async def get_reteica_rates() -> str:
        """Municipality-specific ReteICA rates.

        ReteICA (Impuesto de Industria y Comercio) varies by municipality.
        This resource provides default rates; consult municipal statutes for
        exact values.
        """
        from src.services.tax.config import RETE_ICA_RATES

        formatted = {}
        for key, rate in RETE_ICA_RATES.items():
            formatted[key] = f"{float(rate)}%"

        return json.dumps(
            {
                "rates": formatted,
                "description": (
                    "Tasas de ReteICA por municipio. "
                    "Los códigos son los códigos DIAN de municipio (ej: 11001=Bogotá). "
                    "Sufijo '_services' indica la tasa para servicios."
                ),
                "note": (
                    "Estas son tasas por defecto. "
                    "Consulte el estatuto municipal para valores exactos."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )

    @server.resource("factus://config/withholding-rules")
    async def get_withholding_rules() -> str:
        """Rules and conditions for each withholding type.

        Explains when each withholding applies, who is affected,
        and any special conditions.
        """
        from src.services.tax.config import (
            AUTORRETENEDOR_TRIBUTE_CODES,
            RETE_IVA_APPLICABLE_TRIBUTE_CODES,
            RETE_GMF_PAYMENT_METHOD_CODES,
            RETE_RENTA_UVT_THRESHOLD,
            SERVICES_UVT_THRESHOLD,
            RETE_GMF_UVT_THRESHOLD,
            UVT,
        )

        uvt_cop = float(UVT)

        return json.dumps(
            {
                "reterenta": {
                    "code": "06",
                    "description": "Retención en la Fuente a título de Renta",
                    "applies_to": [
                        "Compras de bienes y servicios a personas naturales y jurídicas",
                    ],
                    "who_is_exempt": [
                        "Autorretenedores (códigos de tributo: "
                        + ", ".join(sorted(AUTORRETENEDOR_TRIBUTE_CODES))
                        + ")",
                    ],
                    "goods_threshold": {
                        "uvt": RETE_RENTA_UVT_THRESHOLD,
                        "cop": f"${RETE_RENTA_UVT_THRESHOLD * int(uvt_cop):,}",
                        "condition": (
                            "Aplica solo si el monto de la operación "
                            "supera este umbral"
                        ),
                    },
                    "services_threshold": {
                        "uvt": SERVICES_UVT_THRESHOLD,
                        "cop": f"${SERVICES_UVT_THRESHOLD * int(uvt_cop):,}",
                        "condition": (
                            "Aplica solo si el monto de la operación "
                            "supera este umbral"
                        ),
                    },
                },
                "reteiva": {
                    "code": "05",
                    "description": "Retención en la Fuente de IVA",
                    "applies_when": "El cliente es Gran Contribuyente o Autorretenedor",
                    "applicable_tribute_codes": sorted(
                        RETE_IVA_APPLICABLE_TRIBUTE_CODES
                    ),
                    "rate": "15% (11% para Régimen Simple)",
                },
                "reteica": {
                    "code": "07",
                    "description": "Retención de Impuesto de Industria y Comercio",
                    "applies_to": "Operaciones gravadas con ICA en el municipio",
                    "rate": "Varía por municipio (ver factus://config/reteica-rates)",
                },
                "rete_gmf": {
                    "code": "20",
                    "description": "Retención por Movilización de Recursos Financieros (4x1000)",
                    "threshold": {
                        "uvt": RETE_GMF_UVT_THRESHOLD,
                        "cop": f"${RETE_GMF_UVT_THRESHOLD * int(uvt_cop):,}",
                    },
                    "payment_methods_that_trigger": sorted(
                        RETE_GMF_PAYMENT_METHOD_CODES
                    ),
                },
            },
            indent=2,
            ensure_ascii=False,
        )


__all__ = ["register"]
