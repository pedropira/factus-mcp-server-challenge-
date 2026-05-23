"""
Pydantic models for all MCP tool parameters.

Each model maps to exactly one MCP tool. Pydantic auto-generates the
JSON Schema that MCP exposes to LLMs via `list_tools`, so descriptions
must be written for the LLM, not for human developers.

Naming convention: {Verb}{Domain}Params — e.g. CreateCustomerParams.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOMER TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateCustomerParams(BaseModel):
    """Create a new customer (purchaser) in the local database."""

    identification_document_id: int = Field(
        description="ID del tipo de documento (Factus API: 1-11)"
    )
    identification: str = Field(
        max_length=50, description="Número de identificación del cliente"
    )
    dv: Optional[str] = Field(
        default=None, max_length=1,
        description="Dígito de verificación (requerido si NIT)",
    )
    company: Optional[str] = Field(
        default=None, max_length=200,
        description="Razón social (persona jurídica)",
    )
    trade_name: Optional[str] = Field(
        default=None, max_length=200, description="Nombre comercial",
    )
    names: Optional[str] = Field(
        default=None, max_length=200,
        description="Nombres del cliente (persona natural)",
    )
    address: Optional[str] = Field(
        default=None, max_length=200, description="Dirección del cliente",
    )
    email: Optional[str] = Field(
        default=None, max_length=200, description="Correo electrónico",
    )
    phone: Optional[str] = Field(
        default=None, max_length=50, description="Teléfono del cliente",
    )
    legal_organization_id: Optional[str] = Field(
        default=None, max_length=5,
        description="ID del tipo de organización (Factus API)",
    )
    tribute_id: Optional[str] = Field(
        default=None, max_length=5,
        description="ID del tributo del cliente",
    )
    municipality_id: Optional[str] = Field(
        default=None, max_length=10,
        description="ID del municipio (código DIAN: 11001, 05001, etc.)",
    )


class GetCustomerParams(BaseModel):
    """Get a customer by their database ID."""

    id: int = Field(description="ID del cliente en la base de datos local")


class SearchCustomersParams(BaseModel):
    """Search customers by identification, name, company, or email."""

    query: str = Field(
        min_length=1, description="Texto de búsqueda (identificación, nombre, empresa o email)"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class UpdateCustomerParams(BaseModel):
    """Update an existing customer. Only provided fields are changed."""

    id: int = Field(description="ID del cliente a actualizar")
    identification_document_id: Optional[int] = Field(
        default=None, description="ID del tipo de documento",
    )
    identification: Optional[str] = Field(
        default=None, max_length=50, description="Número de identificación",
    )
    dv: Optional[str] = Field(
        default=None, max_length=1, description="Dígito de verificación",
    )
    company: Optional[str] = Field(
        default=None, max_length=200, description="Razón social",
    )
    trade_name: Optional[str] = Field(
        default=None, max_length=200, description="Nombre comercial",
    )
    names: Optional[str] = Field(
        default=None, max_length=200, description="Nombres del cliente",
    )
    address: Optional[str] = Field(
        default=None, max_length=200, description="Dirección",
    )
    email: Optional[str] = Field(
        default=None, max_length=200, description="Correo electrónico",
    )
    phone: Optional[str] = Field(
        default=None, max_length=50, description="Teléfono",
    )
    legal_organization_id: Optional[str] = Field(
        default=None, max_length=5, description="ID del tipo de organización",
    )
    tribute_id: Optional[str] = Field(
        default=None, max_length=5, description="ID del tributo",
    )
    municipality_id: Optional[str] = Field(
        default=None, max_length=10, description="ID del municipio",
    )


class DeleteCustomerParams(BaseModel):
    """Delete a customer by their database ID."""

    id: int = Field(description="ID del cliente a eliminar")


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCT TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateProductParams(BaseModel):
    """Create a new product in the local catalog."""

    code_reference: str = Field(
        max_length=100, description="Código de referencia único del producto",
    )
    name: str = Field(
        max_length=300, description="Nombre del producto o servicio",
    )
    price: Decimal = Field(
        max_digits=20, decimal_places=2,
        description="Precio unitario con impuestos incluidos",
    )
    tax_rate: str = Field(
        max_length=10, description="Porcentaje de impuesto (ej: 19.00)",
    )
    unit_measure_id: int = Field(
        description="ID de la unidad de medida (Factus API: 70=unidad, etc.)",
    )
    standard_code_id: int = Field(
        description="ID del estándar de producto (1=contribuyente, 2=UNSPSC, etc.)",
    )
    tribute_id: int = Field(
        description="ID del tributo aplicado (1=IVA, 2=INC, etc.)",
    )
    is_excluded: bool = Field(
        default=False,
        description="True si el producto está excluido de IVA",
    )
    note: Optional[str] = Field(
        default=None, max_length=500,
        description="Información adicional del producto",
    )


class GetProductParams(BaseModel):
    """Get a product by its database ID."""

    id: int = Field(description="ID del producto en la base de datos local")


class GetProductByCodeParams(BaseModel):
    """Get a product by its unique reference code."""

    code_reference: str = Field(
        description="Código de referencia único del producto",
    )


class SearchProductsParams(BaseModel):
    """Search products by name or code reference."""

    query: str = Field(
        min_length=1, description="Texto de búsqueda (nombre o código de referencia)",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class UpdateProductParams(BaseModel):
    """Update an existing product. Only provided fields are changed."""

    id: int = Field(description="ID del producto a actualizar")
    code_reference: Optional[str] = Field(
        default=None, max_length=100, description="Código de referencia único",
    )
    name: Optional[str] = Field(
        default=None, max_length=300, description="Nombre del producto",
    )
    price: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Precio unitario con impuestos incluidos",
    )
    tax_rate: Optional[str] = Field(
        default=None, max_length=10, description="Porcentaje de impuesto",
    )
    unit_measure_id: Optional[int] = Field(
        default=None, description="ID de la unidad de medida",
    )
    standard_code_id: Optional[int] = Field(
        default=None, description="ID del estándar de producto",
    )
    tribute_id: Optional[int] = Field(
        default=None, description="ID del tributo aplicado",
    )
    is_excluded: Optional[bool] = Field(
        default=None, description="True si está excluido de IVA",
    )
    note: Optional[str] = Field(
        default=None, max_length=500, description="Información adicional",
    )


class DeleteProductParams(BaseModel):
    """Delete a product by its database ID."""

    id: int = Field(description="ID del producto a eliminar")


# ═══════════════════════════════════════════════════════════════════════════
# ESTABLISHMENT TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateEstablishmentParams(BaseModel):
    """Create a new establishment (issuer branch) in the local database."""

    name: str = Field(max_length=200, description="Nombre del establecimiento")
    address: str = Field(
        max_length=200, description="Dirección del establecimiento",
    )
    phone_number: Optional[str] = Field(
        default=None, max_length=50, description="Teléfono",
    )
    email: Optional[str] = Field(
        default=None, max_length=200, description="Correo electrónico",
    )
    municipality_id: str = Field(
        max_length=10,
        description="ID del municipio (código DIAN: 11001, 05001, etc.)",
    )


class GetEstablishmentParams(BaseModel):
    """Get an establishment by its database ID."""

    id: int = Field(description="ID del establecimiento en la base de datos local")


class ListEstablishmentsParams(BaseModel):
    """List establishments with pagination, sorted by name."""

    offset: int = Field(default=0, ge=0, description="Desplazamiento para paginación")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class UpdateEstablishmentParams(BaseModel):
    """Update an existing establishment. Only provided fields are changed."""

    id: int = Field(description="ID del establecimiento a actualizar")
    name: Optional[str] = Field(
        default=None, max_length=200, description="Nombre del establecimiento",
    )
    address: Optional[str] = Field(
        default=None, max_length=200, description="Dirección",
    )
    phone_number: Optional[str] = Field(
        default=None, max_length=50, description="Teléfono",
    )
    email: Optional[str] = Field(
        default=None, max_length=200, description="Correo electrónico",
    )
    municipality_id: Optional[str] = Field(
        default=None, max_length=10, description="ID del municipio",
    )


class DeleteEstablishmentParams(BaseModel):
    """Delete an establishment by its database ID."""

    id: int = Field(description="ID del establecimiento a eliminar")


# ═══════════════════════════════════════════════════════════════════════════
# NUMBERING RANGE TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateNumberingRangeParams(BaseModel):
    """Register a new DIAN numbering range in the local database."""

    document_type_id: int = Field(
        description="Tipo de documento (21=factura, 22=nota crédito, 24=doc. soporte)",
    )
    prefix: str = Field(
        max_length=10, description="Prefijo del rango (ej: SETP, FAC)",
    )
    from_number: int = Field(description="Número inicial del rango")
    to_number: int = Field(description="Número final del rango")
    is_active: bool = Field(default=True, description="Si el rango está activo")


class GetActiveNumberingRangesParams(BaseModel):
    """Get all active numbering ranges, optionally filtered by document type."""

    document_type_id: Optional[int] = Field(
        default=None,
        description="Filtrar por tipo de documento (opcional: 21=factura, 22=NC, 24=DS)",
    )


class GetDefaultNumberingRangeParams(BaseModel):
    """Get the first active numbering range for a document type."""

    document_type_id: int = Field(
        description="Tipo de documento (21=factura, 22=nota crédito, 24=doc. soporte)",
    )


class FetchNumberingRangesFromFactusParams(BaseModel):
    """Fetch numbering ranges from Factus API and sync to local database."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# INVOICE TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class _PaymentDetail(BaseModel):
    """A payment detail entry for an invoice."""

    payment_method_code: str = Field(
        description="Código del método de pago (ej: 10=efectivo, 20=transferencia)"
    )
    payment_due_date: str = Field(
        description="Fecha de vencimiento (YYYY-MM-DD)"
    )
    payment_form: str = Field(
        default="1", description="Forma de pago (1=contado, 2=crédito)"
    )


class _InvoiceItemInput(BaseModel):
    """An invoice line item (product or service)."""

    code_reference: str = Field(description="Código de referencia del producto")
    name: str = Field(description="Nombre del producto o servicio")
    quantity: int = Field(gt=0, description="Cantidad")
    price: Decimal = Field(
        max_digits=20, decimal_places=2,
        description="Precio unitario con impuestos incluidos",
    )
    tax_rate: str = Field(description="Porcentaje de impuesto (ej: 19.00)")
    unit_measure_id: int = Field(
        description="ID de la unidad de medida (Factus API: 70=unidad, etc.)",
    )
    standard_code_id: int = Field(
        description="ID del estándar de producto",
    )
    tribute_id: int = Field(description="ID del tributo (1=IVA, 2=INC)")
    is_excluded: bool = Field(
        default=False, description="True si está excluido de IVA",
    )
    discount_rate: Optional[Decimal] = Field(
        default=None, max_digits=5, decimal_places=2,
        description="Porcentaje de descuento",
    )
    note: Optional[str] = Field(
        default=None, max_length=500,
        description="Información adicional del producto",
    )


class _AllowanceChargeInput(BaseModel):
    """A global discount or surcharge applied at invoice level."""

    is_surcharge: bool = Field(
        description="True=recargo, False=descuento",
    )
    reason: str = Field(
        max_length=500, description="Razón del descuento o recargo",
    )
    base_amount: Decimal = Field(
        max_digits=20, decimal_places=2,
        description="Base sobre la cual se calcula",
    )
    amount: Decimal = Field(
        max_digits=20, decimal_places=2,
        description="Valor monetario del descuento/recargo",
    )


class CreateInvoiceParams(BaseModel):
    """Create an electronic invoice via Factus API (POST /v2/bills/validate).

    The customer and items are provided as structured dicts that Factus API expects.
    For the full Colombian flow with numbering range, use create_invoice_with_numbering.
    """

    reference_code: str = Field(
        max_length=100, description="Código único de referencia (evita duplicados)",
    )
    document: str = Field(
        default="01", description="Tipo de documento (01=factura electrónica)",
    )
    operation_type: str = Field(
        default="10", description="Tipo de operación (10=estándar)",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )
    send_email: bool = Field(default=False, description="Enviar correo al cliente")
    payment_details: list[_PaymentDetail] = Field(
        description="Detalles de pago (método, fecha, forma)",
    )
    customer: dict = Field(
        description="Datos del cliente en formato Factus API "
        "(usar mappers.customer_to_factus_dict para convertir)",
    )
    items: list[_InvoiceItemInput] = Field(
        description="Ítems de la factura (productos/servicios)",
    )
    allowance_charges: Optional[list[_AllowanceChargeInput]] = Field(
        default=None,
        description="Descuentos y recargos globales a nivel de factura",
    )


class CreateInvoiceWithNumberingParams(BaseModel):
    """Create an electronic invoice with the full Colombian business flow.

    This tool:
      1. Maps local DB models to Factus API dicts via mappers
      2. Validates with InvoiceValidator
      3. Gets next available number from NumberingRangeService
      4. Calculates withholdings
      5. Calls InvoiceService.create_with_numbering
    """

    reference_code: str = Field(
        max_length=100, description="Código único de referencia (evita duplicados)",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )
    send_email: bool = Field(default=False, description="Enviar correo al cliente")
    payment_details: list[_PaymentDetail] = Field(
        description="Detalles de pago (método, fecha, forma)",
    )
    items: list[_InvoiceItemInput] = Field(
        description="Ítems de la factura (productos/servicios)",
    )
    allowance_charges: Optional[list[_AllowanceChargeInput]] = Field(
        default=None,
        description="Descuentos y recargos globales a nivel de factura",
    )

    # IDs locales para el flujo completo
    customer_id: int = Field(
        description="ID del cliente en la base de datos local",
    )
    numbering_range_id: int = Field(
        description="ID del rango de numeración en la base de datos local",
    )
    establishment_id: Optional[int] = Field(
        default=None,
        description="ID del establecimiento (opcional, solo si hay múltiples sucursales)",
    )


class ListInvoicesParams(BaseModel):
    """List invoices from Factus API with optional filters."""

    status: Optional[str] = Field(
        default=None, description="Filtrar por estado (ej: 1=activa, 2=anulada)",
    )
    reference_code: Optional[str] = Field(
        default=None, description="Filtrar por código de referencia",
    )
    offset: int = Field(default=0, ge=0, description="Desplazamiento para paginación")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class GetInvoiceByNumberParams(BaseModel):
    """Get an invoice by its Factus-assigned number (prefix + consecutive)."""

    number: str = Field(
        description="Número de factura asignado por Factus (prefijo + consecutivo)",
    )


class GetInvoiceByReferenceParams(BaseModel):
    """Get an invoice by its unique reference code."""

    reference_code: str = Field(
        description="Código único de referencia de la factura",
    )


class DeleteInvoiceParams(BaseModel):
    """Delete an invoice by its reference code."""

    reference_code: str = Field(
        description="Código de referencia de la factura a eliminar",
    )


class DownloadInvoicePdfParams(BaseModel):
    """Download an invoice PDF by its Factus-assigned number."""

    number: str = Field(
        description="Número de factura asignado por Factus (prefijo + consecutivo)",
    )


class DownloadInvoiceXmlParams(BaseModel):
    """Download an invoice XML by its Factus-assigned number."""

    number: str = Field(
        description="Número de factura asignado por Factus (prefijo + consecutivo)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# CREDIT NOTE TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateCreditNoteParams(BaseModel):
    """Create a credit note via Factus API (POST /v2/credit-notes)."""

    reference_code: str = Field(
        max_length=100, description="Código único de referencia",
    )
    correction_concept_code: str = Field(
        description="Código de corrección (1-6: 1=devolución, 2=anulación, etc.)",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )
    send_email: bool = Field(default=False, description="Enviar correo al cliente")
    invoice_reference: str = Field(
        description="Número de factura que referencia (prefijo + consecutivo)",
    )
    payment_details: list[_PaymentDetail] = Field(
        description="Detalles de pago",
    )
    customer: dict = Field(
        description="Datos del cliente en formato Factus API",
    )
    items: list[_InvoiceItemInput] = Field(
        description="Ítems de la nota crédito",
    )


class ListCreditNotesParams(BaseModel):
    """List credit notes from Factus API with optional filters."""

    status: Optional[str] = Field(
        default=None, description="Filtrar por estado",
    )
    reference_code: Optional[str] = Field(
        default=None, description="Filtrar por código de referencia",
    )
    offset: int = Field(default=0, ge=0, description="Desplazamiento para paginación")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class GetCreditNoteParams(BaseModel):
    """Get a credit note by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota crédito en Factus (devuelto por list_credit_notes)",
    )


class DeleteCreditNoteParams(BaseModel):
    """Delete a credit note by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota crédito en Factus",
    )


class DownloadCreditNotePdfParams(BaseModel):
    """Download a credit note PDF by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota crédito en Factus",
    )


class DownloadCreditNoteXmlParams(BaseModel):
    """Download a credit note XML by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota crédito en Factus",
    )


# ═══════════════════════════════════════════════════════════════════════════
# SUPPORT DOCUMENT TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateSupportDocumentParams(BaseModel):
    """Create a support document (Documento Soporte) via Factus API.

    Documentos soporte (type "03") are used for transactions with suppliers
    who are not required to issue electronic invoices.
    """

    reference_code: str = Field(
        max_length=100, description="Código único de referencia",
    )
    provider: dict = Field(
        description="Datos del proveedor en formato Factus API",
    )
    items: list[_InvoiceItemInput] = Field(
        description="Ítems del documento soporte",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )
    send_email: bool = Field(
        default=False, description="Enviar correo al proveedor",
    )


class ListSupportDocumentsParams(BaseModel):
    """List support documents from Factus API with optional filters."""

    status: Optional[str] = Field(default=None, description="Filtrar por estado")
    reference_code: Optional[str] = Field(
        default=None, description="Filtrar por código de referencia",
    )
    offset: int = Field(default=0, ge=0, description="Desplazamiento para paginación")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class GetSupportDocumentParams(BaseModel):
    """Get a support document by its Factus-assigned number."""

    number: str = Field(
        description="Número de documento soporte asignado por Factus",
    )


class DeleteSupportDocumentParams(BaseModel):
    """Delete a support document by its reference code."""

    reference_code: str = Field(
        description="Código de referencia del documento soporte",
    )


class DownloadSupportDocumentPdfParams(BaseModel):
    """Download a support document PDF by its Factus-assigned number."""

    number: str = Field(
        description="Número de documento soporte asignado por Factus",
    )


class DownloadSupportDocumentXmlParams(BaseModel):
    """Download a support document XML by its Factus-assigned number."""

    number: str = Field(
        description="Número de documento soporte asignado por Factus",
    )


# ═══════════════════════════════════════════════════════════════════════════
# ADJUSTMENT NOTE TOOLS
# ═══════════════════════════════════════════════════════════════════════════


class CreateAdjustmentNoteParams(BaseModel):
    """Create an adjustment note (Nota de Ajuste) via Factus API.

    Adjustment notes (type "04") correct existing support documents.
    """

    reference_code: str = Field(
        max_length=100, description="Código único de referencia",
    )
    support_document_reference: str = Field(
        description="Número de documento soporte que referencia",
    )
    provider: dict = Field(
        description="Datos del proveedor en formato Factus API",
    )
    items: list[_InvoiceItemInput] = Field(
        description="Ítems de la nota de ajuste",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )
    send_email: bool = Field(
        default=False, description="Enviar correo al proveedor",
    )


class ListAdjustmentNotesParams(BaseModel):
    """List adjustment notes from Factus API with optional filters."""

    status: Optional[str] = Field(default=None, description="Filtrar por estado")
    reference_code: Optional[str] = Field(
        default=None, description="Filtrar por código de referencia",
    )
    offset: int = Field(default=0, ge=0, description="Desplazamiento para paginación")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de resultados")


class GetAdjustmentNoteParams(BaseModel):
    """Get an adjustment note by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota de ajuste en Factus (devuelto por list_adjustment_notes)",
    )


class DeleteAdjustmentNoteParams(BaseModel):
    """Delete an adjustment note by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota de ajuste en Factus",
    )


class DownloadAdjustmentNotePdfParams(BaseModel):
    """Download an adjustment note PDF by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota de ajuste en Factus",
    )


class DownloadAdjustmentNoteXmlParams(BaseModel):
    """Download an adjustment note XML by its Factus-internal ID."""

    factus_id: int = Field(
        description="ID interno de la nota de ajuste en Factus",
    )


# ═══════════════════════════════════════════════════════════════════════════
# COMPANY TOOL
# ═══════════════════════════════════════════════════════════════════════════


class GetCompanyInfoParams(BaseModel):
    """Get company information from Factus API (no parameters needed)."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# SHARED — Factus dict inputs for complex flows
# ═══════════════════════════════════════════════════════════════════════════

# Re-export shared sub-models so callers can reference them
__all__ = [
    # Customer
    "CreateCustomerParams",
    "GetCustomerParams",
    "SearchCustomersParams",
    "UpdateCustomerParams",
    "DeleteCustomerParams",
    # Product
    "CreateProductParams",
    "GetProductParams",
    "GetProductByCodeParams",
    "SearchProductsParams",
    "UpdateProductParams",
    "DeleteProductParams",
    # Establishment
    "CreateEstablishmentParams",
    "GetEstablishmentParams",
    "ListEstablishmentsParams",
    "UpdateEstablishmentParams",
    "DeleteEstablishmentParams",
    # Numbering Range
    "CreateNumberingRangeParams",
    "GetActiveNumberingRangesParams",
    "GetDefaultNumberingRangeParams",
    "FetchNumberingRangesFromFactusParams",
    # Invoice
    "CreateInvoiceParams",
    "CreateInvoiceWithNumberingParams",
    "ListInvoicesParams",
    "GetInvoiceByNumberParams",
    "GetInvoiceByReferenceParams",
    "DeleteInvoiceParams",
    "DownloadInvoicePdfParams",
    "DownloadInvoiceXmlParams",
    # Credit Note
    "CreateCreditNoteParams",
    "ListCreditNotesParams",
    "GetCreditNoteParams",
    "DeleteCreditNoteParams",
    "DownloadCreditNotePdfParams",
    "DownloadCreditNoteXmlParams",
    # Support Document
    "CreateSupportDocumentParams",
    "ListSupportDocumentsParams",
    "GetSupportDocumentParams",
    "DeleteSupportDocumentParams",
    "DownloadSupportDocumentPdfParams",
    "DownloadSupportDocumentXmlParams",
    # Adjustment Note
    "CreateAdjustmentNoteParams",
    "ListAdjustmentNotesParams",
    "GetAdjustmentNoteParams",
    "DeleteAdjustmentNoteParams",
    "DownloadAdjustmentNotePdfParams",
    "DownloadAdjustmentNoteXmlParams",
    # Company
    "GetCompanyInfoParams",
    # Shared input models (used internally by tools)
    "_PaymentDetail",
    "_InvoiceItemInput",
    "_AllowanceChargeInput",
]
