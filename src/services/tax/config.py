"""
Colombian tax configuration: UVT, thresholds, and withholding rates.

UVT (Unidad de Valor Tributario) 2026 — estimated value based on DIAN
resolution. Update yearly when official value is published.
"""

from __future__ import annotations

from decimal import Decimal

# ═══════════════════════════════════════════════════════════════════════════
# UVT — Unidad de Valor Tributario
# ═══════════════════════════════════════════════════════════════════════════
# 2026 estimated value ~ 47,000 COP (confirm against official DIAN resolution)

UVT: Decimal = Decimal("47000")

# Thresholds (in UVT)
RETE_RENTA_UVT_THRESHOLD: int = 27      # 27 UVT ≈ 1,269,000 COP
SERVICES_UVT_THRESHOLD: int = 4          # 4 UVT ≈ 188,000 COP
RETE_GMF_UVT_THRESHOLD: int = 100       # 100 UVT ≈ 4,700,000 COP

# ═══════════════════════════════════════════════════════════════════════════
# ReteRenta (code "06")
# ═══════════════════════════════════════════════════════════════════════════

# Rates by customer type (percentage)
RETE_RENTA_RATE_NATURAL: Decimal = Decimal("2.50")   # Persona natural
RETE_RENTA_RATE_LEGAL: Decimal = Decimal("3.50")     # Persona jurídica
RETE_RENTA_RATE_SERVICES: Decimal = Decimal("4.00")  # Servicios en general

# Customers who are EXEMPT from ReteRenta (they self-withhold)
AUTORRETENEDOR_TRIBUTE_CODES: set[str] = {"08"}  # Gran Contribuyente con Autorretención

# ═══════════════════════════════════════════════════════════════════════════
# ReteIVA (code "05")
# ═══════════════════════════════════════════════════════════════════════════

RETE_IVA_RATE: Decimal = Decimal("15.00")           # 15% on the IVA portion
RETE_IVA_SIMPLE_RATE: Decimal = Decimal("11.00")     # 11% for Régimen Simple

# Customers who trigger ReteIVA (Gran Contribuyente or Autorretenedor)
RETE_IVA_APPLICABLE_TRIBUTE_CODES: set[str] = {"08", "22"}

# ═══════════════════════════════════════════════════════════════════════════
# ReteICA (code "07")
# ═══════════════════════════════════════════════════════════════════════════

# Rates per municipality (DIAN code → rate %)
# Default rate for Bogotá (11001): 0.2% for services, 0.4% for commercial
# Actual rates depend on municipal statute — these are common defaults.
RETE_ICA_RATES: dict[str, Decimal] = {
    "11001": Decimal("0.40"),   # Bogotá — commercial
    "11001_services": Decimal("0.20"),  # Bogotá — services
}

# ═══════════════════════════════════════════════════════════════════════════
# ReteGMF / 4x1000 (code "20")
# ═══════════════════════════════════════════════════════════════════════════

RETE_GMF_RATE: Decimal = Decimal("0.40")  # 0.4% (4x1000)

# Payment methods that trigger ReteGMF (electronic/financial system)
# DIAN codes for payment methods
RETE_GMF_PAYMENT_METHOD_CODES: set[str] = {
    "42",  # Consignación bancaria
    "47",  # Transferencia débito bancaria
    "48",  # Tarjeta crédito
    "49",  # Tarjeta débito
}

# ═══════════════════════════════════════════════════════════════════════════
# Tribute codes for customer type detection
# ═══════════════════════════════════════════════════════════════════════════

# "ZZ" = No aplica (no special tax regime)
# "01" = IVA régimen común
# "02" = IVA régimen simplificado
# "22" = Gran Contribuyente
# "08" = Gran Contribuyente con Autorretención
# "25" = Régimen Simple de Tributación
