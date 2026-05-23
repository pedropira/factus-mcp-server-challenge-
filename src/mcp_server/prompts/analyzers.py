"""
Analytical prompts for the Factus MCP server.

Each prompt provides analytical guidance for specific tasks related to
Colombian electronic invoicing, DIAN compliance, and tax calculations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(server: FastMCP) -> None:
    """Register all analytical prompts on the MCP server."""

    @server.prompt(
        name="analizar-obligaciones-tributarias",
        description="Analiza las obligaciones tributarias del contribuyente basado en el perfil de la empresa registrada en Factus.",
    )
    async def analizar_obligaciones_tributarias() -> str:
        """Analiza obligaciones tributarias del contribuyente."""
        return """
# Análisis de Obligaciones Tributarias

## Información Base
Para realizar este análisis, primero obtén la información de la empresa usando `get_company_info`.

## Pasos del Análisis

### 1. Perfil del Contribuyente
Revisa los datos de la empresa: NIT, razón social, régimen tributario.
Identifica si es responsable de IVA, Gran Contribuyente, o régimen simple.

### 2. Responsabilidades Fiscales
Analiza las responsabilidades tributarias:
- **IVA**: Obligatorio si vende productos gravados
- **Retención en la fuente**: Aplica si es agente de retención
- **ICA**: Según actividades económicas y municipio
- **INC**: Si comercializa productos con impuesto al consumo

### 3. Tipos de Documento Aplicables
Determina qué documentos electrónicos debe emitir:
- **Factura electrónica**: Operaciones con otros responsables de IVA
- **Documento soporte**: Pagos a no responsables (régimen simple, no facturadores)
- **Nota crédito**: Correcciones a facturas
- **Nota de ajuste**: Correcciones a documentos soporte

### 4. Recomendaciones
Basado en el perfil, sugiere configuraciones y procesos para cumplimiento DIAN.

## Recursos Útiles
- `factus://dian/codes/identification-types` — Tipos de identificación
- `factus://dian/codes/municipalities` — Códigos de municipios
- `factus://dian/tax/withholding-rates` — Tarifas de retención
"""

    @server.prompt(
        name="analizar-factura-antes-enviar",
        description="Revisa y valida una factura antes de enviarla a DIAN, verificando datos requeridos y códigos DIAN correctos.",
    )
    async def analizar_factura_antes_enviar() -> str:
        """Lista de verificación pre-envío para facturas."""
        return """
# Análisis de Factura Antes de Enviar a DIAN

## Lista de Verificación

### 1. Datos del Cliente
- [ ] Identificación: NIT o cédula válido
- [ ] DV: Dígito de verificación correcto (para NIT)
- [ ] Tipo de identificación: Código DIAN correcto
- [ ] Municipio: Código DIAN del municipio (ej: 11001 para Bogotá)
- [ ] Correo electrónico válido

### 2. Productos/Items
- [ ] Código de referencia único
- [ ] Cantidad > 0
- [ ] Precio > 0
- [ ] Tasa de IVA correcta (0%, 5%, 19%)
- [ ] Unidad de medida: Código DIAN correcto
- [ ] Código estándar: 1=Contribuyente, 2=UNSPSC

### 3. Numeración
- [ ] Rango de numeración activo para facturas (document_type_id=21)
- [ ] Prefijo correcto según el rango
- [ ] Número disponible dentro del rango autorizado por DIAN

### 4. Valores
- [ ] Subtotal correcto (precio x cantidad)
- [ ] IVA calculado correctamente
- [ ] Totales consistentes

### 5. Forma de Pago
- [ ] Código de forma de pago: 1=Contado, 2=Crédito
- [ ] Plazo si es crédito

## Herramientas a Usar
1. `get_active_numbering_ranges(document_type_id=21)` — Verificar rango disponible
2. `get_default_numbering_range(document_type_id=21)` — Obtener rango por defecto
3. `search_customers(query)` — Buscar y verificar cliente
4. `get_invoice_by_reference(reference_code)` — Verificar que reference_code no exista

## Códigos DIAN Útiles
Consulta los recursos disponibles para verificar códigos:
- `factus://dian/codes/identification-types`
- `factus://dian/codes/municipalities`
- `factus://dian/codes/payment-methods`
- `factus://dian/codes/unit-measures`
"""

    @server.prompt(
        name="comparar-tipos-documento",
        description="Compara los diferentes tipos de documentos electrónicos soportados: factura, nota crédito, documento soporte y nota de ajuste.",
    )
    async def comparar_tipos_documento() -> str:
        """Comparación de tipos de documento electrónicos."""
        return """
# Comparación de Tipos de Documento Electrónicos

## Resumen Rápido

| Característica | Factura | Nota Crédito | Doc. Soporte | Nota Ajuste |
|---|---|---|---|---|
| Tipo DIAN | 01 | 02 | 03 | 04 |
| A quién | Clientes | Clientes | Proveedores | Proveedores |
| Corrige a | -- | Factura | -- | Doc. Soporte |
| Obligatorio | Si | No | Si (sin FE) | No |

## Factura Electrónica (Tipo 01)
- **Uso**: Venta de bienes o servicios a responsables de IVA
- **Herramientas**: `create_invoice`, `create_invoice_with_numbering`
- **Búsqueda**: Por numero (`get_invoice_by_number`) o reference_code (`get_invoice_by_reference`)
- **Eliminación**: Por reference_code
- **Descarga**: Por numero (PDF/XML)

## Nota Crédito (Tipo 02)
- **Uso**: Corregir o anular una factura existente
- **Conceptos**: 1=Devolución, 2=Anulación, 3=Reemplazo, 4=Descuento, 5=Pronto pago, 6=Deducciones
- **ID para operaciones**: Usa `factus_id` (ID interno Factus), NO el número de documento
- **Herramientas**: `create_credit_note`, `list_credit_notes`, `get_credit_note`

## Documento Soporte (Tipo 03)
- **Uso**: Pagos a proveedores que NO facturan electrónicamente
- **Relevancia fiscal**: Permite deducir costos en renta
- **ID para operaciones**: Usa número Factus (con prefijo) para get y download
- **Eliminación**: Por reference_code
- **Herramientas**: `create_support_document`, `get_support_document`

## Nota de Ajuste (Tipo 04)
- **Uso**: Corregir un documento soporte
- **ID para operaciones**: Usa `factus_id`, NO el número de documento
- **Herramientas**: `create_adjustment_note`, `list_adjustment_notes`

## Diferencias Clave en IDs
| Documento | Get | Delete | Download |
|---|---|---|---|
| Factura | number | reference_code | number |
| Nota Crédito | factus_id | factus_id | factus_id |
| Doc. Soporte | number | reference_code | number |
| Nota Ajuste | factus_id | factus_id | factus_id |
"""

    @server.prompt(
        name="analizar-codigos-dian",
        description="Guía para consultar y entender los códigos DIAN disponibles: tipos de identificación, municipios, formas de pago, unidades de medida, etc.",
    )
    async def analizar_codigos_dian() -> str:
        """Guía de consulta de códigos DIAN."""
        return """
# Análisis de Códigos DIAN

## Categorías Disponibles

### Tipos de Identificación
Recurso: `factus://dian/codes/identification-types`
- 1: Cédula de Ciudadanía
- 2: NIT
- 3: Tarjeta de Identidad
- 4: Cédula de Extranjería
- 5: Pasaporte
- 6: Documento Extranjero
- 7: NIT Extranjero
- 11: Registro Civil

### Tipos de Documento
Recurso: `factus://dian/codes/document-types`
- 01: Factura Electrónica
- 02: Nota Crédito
- 03: Documento Soporte
- 04: Nota de Ajuste

### Formas de Pago
Recurso: `factus://dian/codes/payment-methods`
- 1: Contado
- 2: Crédito

### Unidades de Medida
Recurso: `factus://dian/codes/unit-measures`
- 70: Unidad
- 94: Kilogramo
- 96: Metro
- 97: Metro cuadrado

### Tipos de Tributo
Recurso: `factus://dian/codes/tribute-types`
- 1: IVA
- 2: INC (Impuesto Nacional al Consumo)
- 3: Impuesto al Carbono

### Responsabilidades Fiscales
Recurso: `factus://dian/codes/tax-responsibilities`
Define los códigos de responsabilidades fiscales.

### Municipios
Recurso: `factus://dian/codes/municipalities`
Formato: Código de 5 dígitos (ej: 11001=Bogotá, 05001=Medellín, 76001=Cali)

## Configuración de Impuestos
- `factus://dian/tax/config` — Tarifas vigentes de IVA, INC, Retención
- `factus://dian/tax/withholding-rates` — Tarifas de retención en la fuente

## Uso Práctico
Antes de crear cualquier documento, consulta los recursos relevantes para asegurar que los códigos sean correctos.
"""

    @server.prompt(
        name="simular-retenciones",
        description="Simula el cálculo de retenciones en la fuente para una factura, basado en tarifas actuales y valores de la operación.",
    )
    async def simular_retenciones() -> str:
        """Simulación de cálculo de retenciones."""
        return """
# Simulación de Retenciones

## Información de Base
Para simular retenciones, consulta primero:
- `factus://dian/tax/withholding-rates` — Tarifas de retención actuales
- `factus://dian/tax/config` — Configuración tributaria vigente

## Tipos de Retención

### Retención en la Fuente (ReteFuente)
Aplica a pagos a proveedores cuando el comprador es agente de retención.
- **Honorarios**: 10% (o tarifa vigente)
- **Servicios**: 4% (o tarifa vigente)
- **Compras**: 2.5% (o tarifa vigente)
- **Arrendamientos**: 3.5% (o tarifa vigente)

### Retención de IVA (ReteIVA)
Aplica a ciertos contribuyentes calificados como agentes de retención de IVA.
- Tarifa general: 15% del IVA facturado

### Retención de ICA
Varía según el municipio y la actividad económica.
- Tarifa típica: 0.2% a 1% del valor de la operación

## Cálculo de Ejemplo

Para una factura de $10,000,000 con IVA 19%:
```
Valor base:          $10,000,000
IVA (19%):           $1,900,000
Total factura:       $11,900,000

Retenciones:
- Retefuente (2.5%):  $250,000
- ReteIVA (15% IVA):  $285,000
- ICA (0.4%):         $40,000

Total a pagar:        $11,325,000
```

## Notas
- Las tarifas varían según la actividad económica y el municipio
- La configuración de retenciones se establece en Factus
- Consulta siempre las tarifas vigentes antes de emitir documentos
- Usa `factus://dian/tax/withholding-rates` para tarifas actualizadas
"""


__all__ = ["register"]
