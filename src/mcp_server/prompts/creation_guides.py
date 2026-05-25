"""
Creation guide prompts for the Factus MCP server.

Each prompt provides a step-by-step guide for creating a specific type of
electronic document in Factus, referencing the relevant tools and DIAN codes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(server: FastMCP) -> None:
    """Register all creation guide prompts on the MCP server."""

    @server.prompt(
        name="crear-factura-guia",
        description="Guía paso a paso para crear una factura electrónica en Factus, desde la preparación hasta el envío a DIAN.",
    )
    async def crear_factura_guia() -> str:
        """Guía completa para crear facturas electrónicas."""
        return """
# Guía: Crear Factura Electrónica en Factus

## 1. Preparación

### 1.1 Verificar datos del cliente
Usa `search_customers` para buscar el cliente por identificación, nombre o email.
Si no existe, usa `create_customer` para registrarlo.

### 1.2 Verificar productos/servicios
Usa `search_products` para buscar los productos por nombre o código.
Si no existen, usa `create_product` para registrarlos.

### 1.3 Consultar rangos de numeración
Usa `get_active_numbering_ranges` con `document_type_id=21` para ver los rangos activos para facturas.
Usa `get_default_numbering_range` para obtener el rango por defecto.

### 1.4 Consultar establecimientos
Usa `list_establishments` para ver las sucursales registradas.

## 2. Creación de la Factura

Tienes dos opciones:

### Opción A: Factura con flujo completo (recomendada)
Usa `create_invoice_with_numbering` con:
- `customer_id`: ID del cliente en base de datos local
- `numbering_range_id`: ID del rango de numeración
- `establishment_id`: ID del establecimiento (opcional)
- `items`: Lista de items con código, cantidad, precio, tasa de IVA
- `payment_details`: Forma de pago (código DIAN 1=Contado, 2=Crédito)
- `reference_code`: Código único interno

### Opción B: Factura con datos en formato Factus
Usa `create_invoice` si ya tienes los datos en formato Factus (customer como dict, items como listas de dicts).

## 3. Verificación

Usa `get_invoice_by_reference` con el `reference_code` para verificar el estado.
Usa `download_invoice_pdf` o `download_invoice_xml` para descargar los documentos.

## 4. Códigos DIAN Útiles

- `identification_document_id`: 1=Cédula, 2=NIT, 3=Tarjeta Identidad, 4=Cédula Extranjería
- `document_type_id` para facturas: 21
- `payment_method`: 1=Contado, 2=Crédito
- `unit_measure_id`: 70=Unidad, 94=Kilogramo, 96=Metro
- `tribute_id`: 1=IVA, 2=INC
- Consulta todos los códigos con los recursos `factus://dian/codes/*`
"""

    @server.prompt(
        name="crear-nota-credito-guia",
        description="Guía paso a paso para crear una nota crédito electrónica que corrige una factura existente.",
    )
    async def crear_nota_credito_guia() -> str:
        """Guía completa para crear notas crédito."""
        return """
# Guía: Crear Nota Crédito Electrónica

## ¿Qué es una Nota Crédito?
Una nota crédito (tipo "02") corrige o anula una factura electrónica ya emitida.
Se usa para devoluciones, descuentos posteriores o anulación total de la factura.

## 1. Preparación

### 1.1 Identificar la factura a corregir
Usa `get_invoice_by_reference` o `get_invoice_by_number` para obtener la factura original.

### 1.2 Elegir el concepto de corrección
Códigos de concepto (`correction_concept_code`):
- `1`: Devolución total o parcial de mercancía
- `2`: Anulación total de la factura
- `3`: Reemplazo total de la factura
- `4`: Descuento por volumen de operaciones
- `5`: Descuento por pronto pago
- `6`: Otras deducciones

## 2. Creación de la Nota Crédito

Usa `create_credit_note` con:
- `reference_code`: Código único interno para la nota crédito
- `correction_concept_code`: Código del concepto de corrección (1-6)
- `bill_number`: Número de factura Factus que se corrige (incluye prefijo, ej: "SETP990003793")
- `numbering_range_id`: ID del rango de numeración (opcional, usa el default si no se envía)
- `customer`: Datos del cliente (misma estructura que en factura)
- `items`: Items a corregir (solo los que aplican)
- `payment_details`: Detalles de pago
- `send_email`: true/false para enviar al cliente

## 3. Verificación

Usa `list_credit_notes` con filtro `reference_code` para ver el estado.
Usa `get_credit_note` con el `factus_id` (ID interno de Factus, no el número).
Usa `download_credit_note_pdf` o `download_credit_note_xml` para descargar.

## ⚠️ Nota Importante
Las notas crédito usan `factus_id` (ID interno de Factus) para get/delete/download.
NO usan el número de documento como las facturas. Obtén el `factus_id` de la respuesta al crear o de `list_credit_notes`.
"""

    @server.prompt(
        name="crear-documento-soporte-guia",
        description="Guía paso a paso para crear un documento soporte electrónico para transacciones con proveedores sin factura electrónica.",
    )
    async def crear_documento_soporte_guia() -> str:
        """Guía completa para crear documentos soporte."""
        return """
# Guía: Crear Documento Soporte Electrónico

## ¿Qué es un Documento Soporte?
Un documento soporte (tipo "03") se usa para transacciones con proveedores que NO emiten factura electrónica.
Es obligatorio para deducir costos y gastos en el impuesto de renta.

## 1. Preparación

### 1.1 Datos del proveedor
El proveedor se pasa como un diccionario con la misma estructura que un cliente en formato Factus:
- `identification`: Número de identificación
- `dv`: Dígito de verificación
- `company`: Razón social
- `names`: Nombres (si es persona natural)
- `email`: Correo electrónico
- `address`: Dirección
- `phone`: Teléfono
- `municipality_id`: Código DIAN del municipio (ej: 11001)
- `identification_document_id`: Tipo de identificación (1-11)

### 1.2 Productos/items
Misma estructura que en facturas:
- `code_reference`: Código del producto
- `description`: Descripción
- `quantity`: Cantidad
- `price`: Precio unitario
- `tax_rate`: Tasa de IVA (ej: "19.00")
- `unit_measure_id`: Código DIAN de unidad de medida (70=unidad)
- `standard_code_id`: 1=Estándar contribuyente, 2=UNSPSC

## 2. Creación

Usa `create_support_document` con:
- `reference_code`: Código único interno
- `provider`: Diccionario con datos del proveedor
- `items`: Lista de items
- `send_email`: true/false

## 3. Verificación

Usa `get_support_document` con el número Factus (incluye prefijo).
Usa `download_support_document_pdf` para descargar el PDF.

## ⚠️ Notas Importantes
- Los documentos soporte usan el **número Factus** para get/download (como las facturas)
- Para eliminar, usan el `reference_code` (no el número ni factus_id)
- No tienen notas crédito asociadas — se corrigen con notas de ajuste
"""

    @server.prompt(
        name="crear-nota-ajuste-guia",
        description="Guía paso a paso para crear una nota de ajuste que corrige un documento soporte existente.",
    )
    async def crear_nota_ajuste_guia() -> str:
        """Guía completa para crear notas de ajuste."""
        return """
# Guía: Crear Nota de Ajuste (Documento Soporte)

## ¿Qué es una Nota de Ajuste?
Una nota de ajuste (tipo "04") corrige un documento soporte existente.
Es el equivalente a la nota crédito, pero para documentos soporte.

## 1. Preparación

### 1.1 Identificar el documento soporte a corregir
Usa `get_support_document` con el número Factus del documento original.

### 1.2 Datos del proveedor
Usa la misma información del proveedor del documento original.

## 2. Creación

Usa `create_adjustment_note` con:
- `reference_code`: Código único interno para la nota de ajuste
- `support_document_number`: Número Factus del documento soporte que se corrige
- `correction_concept_code`: Código del motivo de corrección
- `payment_details`: Array con al menos un medio de pago
- `provider`: Datos del proveedor (misma estructura que en el documento soporte)
- `items`: Items a ajustar

## 3. Verificación

Usa `list_adjustment_notes` con filtro `reference_code`.
Usa `get_adjustment_note` con el `number` (número de documento Factus).
Usa `download_adjustment_note_pdf` para descargar el PDF.

## ⚠️ Nota Importante
Las notas de ajuste usan el **número de documento** de Factus para get/download.
Para eliminar, usan el `reference_code`. Obtén ambos de la respuesta al crear o de `list_adjustment_notes`.
"""


__all__ = ["register"]
