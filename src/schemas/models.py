"""
Modelos SQLModel para entidades de Factus.

SQLModel combina Pydantic (validación) + SQLAlchemy (ORM).
Se usan tanto como modelos de DB como esquemas de serialización.

Los tipos de datos siguen la API de Factus:
  - Campos anidados (order_reference, billing_period, withholding_taxes)
    se almacenan como JSON via sqlmodel.Field(sa_type=JSON)
  - Foreign keys referencian tablas padre (customer, establishment, etc.)
  - Unique constraints para evitar duplicados (reference_code, etc.)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel, String


# ═══════════════════════════════════════════════════════════════════════════
# Customer (cliente / adquiriente)
# ═══════════════════════════════════════════════════════════════════════════


class Customer(SQLModel, table=True):
    """Cliente o adquiriente del documento electrónico."""

    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    identification_document_id: int = Field(
        description="ID del tipo de documento (Factus API: 1-11)"
    )
    identification: str = Field(
        max_length=50, description="Número de identificación del cliente"
    )
    dv: Optional[str] = Field(
        default=None, max_length=2,
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

    # Relaciones
    invoices: list["Invoice"] = Relationship(back_populates="customer")

    def __repr__(self) -> str:
        return (
            f"Customer(id={self.id}, identification={self.identification}, "
            f"names={self.names!r}, company={self.company!r})"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Establishment (establecimiento / sucursal)
# ═══════════════════════════════════════════════════════════════════════════


class Establishment(SQLModel, table=True):
    """Establecimiento del emisor que aparece en el documento.

    Opcional — solo necesario si el emisor maneja más de un establecimiento.
    """

    __tablename__ = "establishments"

    id: Optional[int] = Field(default=None, primary_key=True)
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

    invoices: list["Invoice"] = Relationship(back_populates="establishment")


# ═══════════════════════════════════════════════════════════════════════════
# NumberingRange (rango de numeración)
# ═══════════════════════════════════════════════════════════════════════════


class NumberingRange(SQLModel, table=True):
    """Rango de numeración autorizado por la DIAN para un tipo de documento."""

    __tablename__ = "numbering_ranges"

    id: Optional[int] = Field(default=None, primary_key=True)
    factus_id: Optional[int] = Field(
        default=None, description="ID del rango en la API de Factus (se obtiene al sincronizar)",
    )
    prefix: str = Field(
        max_length=10, description="Prefijo del rango (ej: SETP, FAC)",
    )
    from_number: int = Field(description="Número inicial del rango")
    to_number: int = Field(description="Número final del rango")
    resolution_number: str = Field(
        max_length=50, description="Número de resolución DIAN",
    )
    start_date: str = Field(
        max_length=10, description="Fecha inicio de vigencia (DD-MM-YYYY)",
    )
    end_date: str = Field(
        max_length=10, description="Fecha fin de vigencia (DD-MM-YYYY)",
    )
    months: int = Field(description="Meses de vigencia")
    document_type_id: str = Field(
        max_length=5,
        description="Tipo de documento (21=factura, 22=nota crédito, "
        "24=doc. soporte)",
    )
    is_active: bool = Field(default=True, description="Si el rango está activo")

    invoices: list["Invoice"] = Relationship(back_populates="numbering_range")


# ═══════════════════════════════════════════════════════════════════════════
# Invoice (factura electrónica)
# ═══════════════════════════════════════════════════════════════════════════


class Invoice(SQLModel, table=True):
    """Factura electrónica — entidad principal del sistema."""

    __tablename__ = "invoices"

    # ── PK ───────────────────────────────────────────────────────────────
    id: Optional[int] = Field(default=None, primary_key=True)

    # ── Datos del documento ──────────────────────────────────────────────
    document: str = Field(
        default="01", max_length=5,
        description="Código del tipo de documento (01=factura, "
        "03=instrumento electrónico)",
    )
    numbering_range_id: int = Field(
        foreign_key="numbering_ranges.id",
        description="ID del rango de numeración",
    )
    reference_code: str = Field(
        max_length=100, unique=True, index=True,
        description="Código único de referencia (evita duplicados)",
    )
    observation: Optional[str] = Field(
        default=None, max_length=250, description="Observación (max 250 chars)",
    )

    # ── Pago ─────────────────────────────────────────────────────────────
    payment_form: Optional[str] = Field(
        default="1", max_length=5, description="Forma de pago (1=contado, 2=crédito)",
    )
    payment_due_date: Optional[str] = Field(
        default=None, max_length=10,
        description="Fecha de vencimiento (YYYY-MM-DD, requerido si crédito)",
    )
    payment_method_code: Optional[str] = Field(
        default="10", max_length=5, description="Código del método de pago",
    )

    # ── Operación ────────────────────────────────────────────────────────
    operation_type: Optional[int] = Field(
        default=10, description="Tipo de operación (10=estándar, 11=mandatos, "
        "12=transporte)",
    )
    send_email: bool = Field(default=True, description="Enviar correo al cliente")

    # ── Objetos anidados (JSON) ──────────────────────────────────────────
    order_reference: Optional[dict] = Field(
        default=None, sa_type=JSON,
        description="Orden de pedido: {code, issue_date}",
    )
    billing_period: Optional[dict] = Field(
        default=None, sa_type=JSON,
        description="Periodo de facturación: {start_date, start_time, "
        "end_date, end_time}",
    )

    # ── Foreign keys ─────────────────────────────────────────────────────
    establishment_id: Optional[int] = Field(
        default=None, foreign_key="establishments.id",
        description="ID del establecimiento (opcional)",
    )
    customer_id: int = Field(
        foreign_key="customers.id",
        description="ID del cliente/adquiriente",
    )

    # ── Datos de respuesta de Factus (se llenan post-creación) ───────────
    number: Optional[str] = Field(
        default=None, max_length=50,
        description="Número de factura asignado (prefijo + consecutivo)",
    )
    status: Optional[int] = Field(
        default=None, description="Estado del documento en Factus",
    )
    cufe: Optional[str] = Field(
        default=None, max_length=100,
        description="CUFE / CUDE (código único de facturación electrónica)",
    )
    qr: Optional[str] = Field(
        default=None, max_length=500, description="URL del código QR",
    )
    validated: Optional[str] = Field(
        default=None, max_length=50,
        description="Fecha de validación DIAN",
    )
    gross_value: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Valor bruto antes de descuentos",
    )
    taxable_amount: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Base gravable",
    )
    tax_amount: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Monto total de impuestos",
    )
    total: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Valor total de la factura",
    )
    discount: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
        description="Descuento total aplicado",
    )
    discount_rate: Optional[str] = Field(
        default=None, max_length=10,
        description="Porcentaje de descuento global",
    )
    has_claim: bool = Field(default=False, description="Tiene reclamo")
    is_negotiable_instrument: bool = Field(
        default=False, description="Es título negociable",
    )
    errors: Optional[list] = Field(
        default=None, sa_type=JSON,
        description="Errores devueltos por Factus/DIAN",
    )
    created_at: Optional[datetime] = Field(
        default=None, description="Fecha de creación en Factus",
    )

    # ── Relaciones ───────────────────────────────────────────────────────
    customer: Optional[Customer] = Relationship(back_populates="invoices")
    establishment: Optional[Establishment] = Relationship(back_populates="invoices")
    numbering_range: Optional[NumberingRange] = Relationship(back_populates="invoices")
    items: list["InvoiceItem"] = Relationship(back_populates="invoice")

    def __repr__(self) -> str:
        return (
            f"Invoice(id={self.id}, reference_code={self.reference_code!r}, "
            f"number={self.number!r}, total={self.total})"
        )


# ═══════════════════════════════════════════════════════════════════════════
# InvoiceItem (ítem / producto de la factura)
# ═══════════════════════════════════════════════════════════════════════════


class InvoiceItem(SQLModel, table=True):
    """Ítem (producto o servicio) de una factura electrónica."""

    __tablename__ = "invoice_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(
        foreign_key="invoices.id",
        description="ID de la factura a la que pertenece",
    )

    # ── Datos del ítem ───────────────────────────────────────────────────
    code_reference: str = Field(
        max_length=100, description="Código de referencia del producto",
    )
    name: str = Field(
        max_length=300, description="Nombre del producto o servicio",
    )
    quantity: int = Field(description="Cantidad (entero)")
    price: Decimal = Field(
        max_digits=20, decimal_places=2,
        description="Precio unitario CON impuestos incluidos",
    )
    discount_rate: Optional[Decimal] = Field(
        default=0, max_digits=5, decimal_places=2,
        description="Porcentaje de descuento",
    )
    tax_rate: str = Field(
        max_length=10, description="Porcentaje de impuesto (ej: 19.00)",
    )

    # ── Referencias a tablas de Factus ───────────────────────────────────
    unit_measure_id: int = Field(
        description="ID de la unidad de medida (Factus API: 70=unidad, etc.)",
    )
    standard_code_id: int = Field(
        description="ID del estándar de producto "
        "(1=contribuyente, 2=UNSPSC, etc.)",
    )
    is_excluded: bool = Field(
        default=False,
        description="True si el producto está excluido de IVA",
    )
    tribute_id: int = Field(
        description="ID del tributo aplicado (1=IVA, 2=INC, etc.)",
    )

    # ── Opcionales ───────────────────────────────────────────────────────
    scheme_id: Optional[str] = Field(
        default=None, max_length=5,
        description="ID del esquema (requerido si operation_type=11 o 12)",
    )
    note: Optional[str] = Field(
        default=None, max_length=500,
        description="Información adicional del producto",
    )

    # ── Datos anidados (JSON) ────────────────────────────────────────────
    withholding_taxes: Optional[list] = Field(
        default=None, sa_type=JSON,
        description="Autorretenciones aplicadas al ítem",
    )
    mandate: Optional[dict] = Field(
        default=None, sa_type=JSON,
        description="Información del mandante "
        "(requerido si scheme_id=1)",
    )
    additional_properties: Optional[list] = Field(
        default=None, sa_type=JSON,
        description="Propiedades adicionales (sector transporte)",
    )

    # ── Resultados de Factus (post-creación) ─────────────────────────────
    gross_value: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
    )
    taxable_amount: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
    )
    tax_amount: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
    )
    total: Optional[Decimal] = Field(
        default=None, max_digits=20, decimal_places=2,
    )

    # ── Relaciones ───────────────────────────────────────────────────────
    invoice: Optional[Invoice] = Relationship(back_populates="items")

    def __repr__(self) -> str:
        return (
            f"InvoiceItem(id={self.id}, code={self.code_reference!r}, "
            f"name={self.name!r}, qty={self.quantity}, "
            f"price={self.price})"
        )


# ═══════════════════════════════════════════════════════════════════════════
# WithholdingTax (autorretención)
# ── Modelo plano opcional si se prefiere tabla en lugar de JSON ───────────
# ═══════════════════════════════════════════════════════════════════════════


class WithholdingTax(SQLModel, table=True):
    """Autorretención aplicada a un ítem de factura.

    Alternativa a guardar withholding_taxes como JSON en InvoiceItem.
    Útil si se necesita consultar/reportar retenciones individualmente.
    """

    __tablename__ = "withholding_taxes"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_item_id: int = Field(
        foreign_key="invoice_items.id",
        description="Ítem al que aplica la retención",
    )
    code: str = Field(
        max_length=10, description="Código de la retención "
        "(ej: 05=ReteIVA, 06=ReteRenta)",
    )
    withholding_tax_rate: str = Field(
        max_length=10, description="Porcentaje de retención (ej: 7.00)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# AllowanceCharge (descuento / recargo global)
# ═══════════════════════════════════════════════════════════════════════════


class AllowanceCharge(SQLModel, table=True):
    """Descuento o recargo aplicado a nivel de factura."""

    __tablename__ = "allowance_charges"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(
        foreign_key="invoices.id",
        description="Factura a la que aplica",
    )
    concept_type: str = Field(
        max_length=5,
        description="Código del tipo de descuento/recargo "
        "(01=pronto pago, 02=volumen, ZZ=otros)",
    )
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


# ═══════════════════════════════════════════════════════════════════════════
# Product (catálogo de productos)
# ═══════════════════════════════════════════════════════════════════════════


class Product(SQLModel, table=True):
    """Producto o servicio del catálogo del emisor."""

    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    code_reference: str = Field(
        max_length=100, unique=True, index=True,
        description="Código de referencia único del producto",
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
        description="ID del estándar de producto "
        "(1=contribuyente, 2=UNSPSC, etc.)",
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

    def __repr__(self) -> str:
        return (
            f"Product(id={self.id}, code={self.code_reference!r}, "
            f"name={self.name!r}, price={self.price})"
        )
