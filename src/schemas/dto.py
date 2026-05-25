"""
Input DTOs (Pydantic/SQLModel models) for the service layer.

These define the contract for creating and updating entities, separated
from the database models in models.py to allow different field shapes.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOMER (local DB CRUD)
# ═══════════════════════════════════════════════════════════════════════════


class CustomerCreate(SQLModel):
    identification_document_id: int
    identification: str = Field(max_length=50)
    dv: Optional[str] = Field(default=None, max_length=2)
    company: Optional[str] = Field(default=None, max_length=200)
    trade_name: Optional[str] = Field(default=None, max_length=200)
    names: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=200)
    legal_organization_id: Optional[str] = Field(default=None, max_length=5)
    tribute_id: Optional[str] = Field(default=None, max_length=5)
    municipality_id: Optional[str] = Field(default=None, max_length=10)


class CustomerUpdate(SQLModel):
    identification_document_id: Optional[int] = None
    identification: Optional[str] = Field(default=None, max_length=50)
    dv: Optional[str] = Field(default=None, max_length=2)
    company: Optional[str] = Field(default=None, max_length=200)
    trade_name: Optional[str] = Field(default=None, max_length=200)
    names: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=200)
    legal_organization_id: Optional[str] = Field(default=None, max_length=5)
    tribute_id: Optional[str] = Field(default=None, max_length=5)
    municipality_id: Optional[str] = Field(default=None, max_length=10)


# ═══════════════════════════════════════════════════════════════════════════
# ESTABLISHMENT (local DB CRUD)
# ═══════════════════════════════════════════════════════════════════════════


class EstablishmentCreate(SQLModel):
    name: str = Field(max_length=200)
    address: str = Field(max_length=200)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    municipality_id: str = Field(max_length=10)


class EstablishmentUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=200)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    municipality_id: Optional[str] = Field(default=None, max_length=10)


# ═══════════════════════════════════════════════════════════════════════════
# NUMBERING RANGE (local DB CRUD)
# ═══════════════════════════════════════════════════════════════════════════


class NumberingRangeCreate(SQLModel):
    prefix: str = Field(max_length=10)
    from_number: int
    to_number: int
    resolution_number: str = Field(max_length=50)
    start_date: str = Field(max_length=10)
    end_date: str = Field(max_length=10)
    months: int
    document_type_id: str = Field(max_length=5)
    is_active: bool = True


class NumberingRangeUpdate(SQLModel):
    prefix: Optional[str] = Field(default=None, max_length=10)
    from_number: Optional[int] = None
    to_number: Optional[int] = None
    resolution_number: Optional[str] = Field(default=None, max_length=50)
    start_date: Optional[str] = Field(default=None, max_length=10)
    end_date: Optional[str] = Field(default=None, max_length=10)
    months: Optional[int] = None
    document_type_id: Optional[str] = Field(default=None, max_length=5)
    is_active: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCT (local DB CRUD)
# ═══════════════════════════════════════════════════════════════════════════


class ProductCreate(SQLModel):
    code_reference: str = Field(max_length=100)
    name: str = Field(max_length=300)
    price: Decimal = Field(max_digits=20, decimal_places=2)
    tax_rate: str = Field(max_length=10)
    unit_measure_id: int
    standard_code_id: int
    tribute_id: int
    is_excluded: bool = False
    note: Optional[str] = Field(default=None, max_length=500)


class ProductUpdate(SQLModel):
    code_reference: Optional[str] = Field(default=None, max_length=100)
    name: Optional[str] = Field(default=None, max_length=300)
    price: Optional[Decimal] = Field(default=None, max_digits=20, decimal_places=2)
    tax_rate: Optional[str] = Field(default=None, max_length=10)
    unit_measure_id: Optional[int] = None
    standard_code_id: Optional[int] = None
    tribute_id: Optional[int] = None
    is_excluded: Optional[bool] = None
    note: Optional[str] = Field(default=None, max_length=500)


# ═══════════════════════════════════════════════════════════════════════════
# FACTUS API — INVOICE (Bill)
# ═══════════════════════════════════════════════════════════════════════════


class InvoiceCreate(SQLModel):
    """DTO para crear una factura electrónica vía POST /v2/bills/validate.

    Todos los campos reflejan lo que la API de Factus espera en su body.
    Los precios se calculan automáticamente si no se provee total.
    """

    reference_code: str = Field(
        max_length=100, description="Código único del documento (evita duplicados)"
    )
    document: str = Field(
        default="01", description="Tipo de documento (01=factura electrónica)"
    )
    operation_type: str = Field(
        default="10", description="Tipo de operación (10=estándar)"
    )
    observation: Optional[str] = Field(default=None, max_length=250)
    send_email: bool = Field(default=False)
    payment_details: list[dict]
    customer: dict
    items: list[dict]
    allowance_charges: Optional[list[dict]] = Field(
        default=None,
        description="Descuentos y recargos globales. "
        "Cada dict: {is_surcharge: bool, reason: str, "
        "base_amount: str, amount: str}",
    )


# ═══════════════════════════════════════════════════════════════════════════
# FACTUS API — CREDIT NOTE
# ═══════════════════════════════════════════════════════════════════════════


class CreditNoteCreate(SQLModel):
    """DTO para crear una nota crédito vía POST /v2/credit-notes."""

    reference_code: str = Field(max_length=100)
    document: str = Field(default="02", description="02=nota crédito")
    operation_type: str = Field(default="20", description="20=NC que referencia factura")
    correction_concept_code: str = Field(description="Código de corrección (1-6)")
    observation: Optional[str] = Field(default=None, max_length=250)
    send_email: bool = Field(default=False)
    invoice_reference: str = Field(description="Número de factura que referencia")
    payment_details: list[dict]
    customer: dict
    items: list[dict]


# ═══════════════════════════════════════════════════════════════════════════
# FACTUS API — SUPPORT DOCUMENT (Documento Soporte)
# ═══════════════════════════════════════════════════════════════════════════


class SupportDocumentCreate(SQLModel):
    """DTO para crear un documento soporte vía POST /v2/support-documents/validate.

    Los documentos soporte (type "03") se usan para transacciones con
    proveedores no obligados a facturar electrónicamente.
    """

    reference_code: str = Field(
        max_length=100, description="Código único del documento"
    )
    document: str = Field(
        default="03", description="Tipo de documento (03=documento soporte)"
    )
    provider: dict = Field(description="Datos del proveedor (similar a customer)")
    items: list[dict] = Field(description="Ítems del documento soporte")
    observation: Optional[str] = Field(default=None, max_length=250)
    send_email: bool = Field(default=False)


# ═══════════════════════════════════════════════════════════════════════════
# FACTUS API — ADJUSTMENT NOTE (Nota de Ajuste)
# ═══════════════════════════════════════════════════════════════════════════


class AdjustmentNoteCreate(SQLModel):
    """DTO para crear una nota de ajuste vía POST /v2/adjustment-notes/validate.

    Las notas de ajuste (type "04") corrigen documentos soporte existentes.
    """

    reference_code: str = Field(
        max_length=100, description="Código único del documento"
    )
    support_document_number: str = Field(
        description="Número de documento soporte que referencia"
    )
    correction_concept_code: str = Field(
        description="Código del concepto de corrección (obligatorio)"
    )
    payment_details: list[dict] = Field(
        description="Medios de pago (array, al menos uno)"
    )
    provider: dict = Field(description="Datos del proveedor")
    items: list[dict] = Field(description="Ítems de la nota de ajuste")
    created_time: Optional[str] = Field(
        default=None, description="Hora de creación (HH:mm:ss)"
    )
    numbering_range_id: Optional[int] = Field(
        default=None, description="ID del rango de numeración"
    )
    cash_rounding_amount: Optional[str] = Field(
        default=None, description="Redondeo de caja"
    )
    observation: Optional[str] = Field(default=None, max_length=250)
