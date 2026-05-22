"""
Tax — Colombian tax business rules (retenciones, IVA, UVT thresholds).

Módulo con funciones puras para calcular retenciones y config de impuestos
colombianos según la normativa DIAN.
"""

from src.services.tax.config import UVT
from src.services.tax.withholding import calculate

__all__ = [
    "UVT",
    "calculate",
]
