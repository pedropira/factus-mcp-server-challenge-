# DIAN / Factus constants mappings and helper functions
#
# Este archivo contiene dos tipos de constantes:
#   1. DIAN_CONSTANTS — códigos oficiales DIAN (estándar colombiano)
#   2. FACTUS_API_IDS — IDs específicos que usa la API de Factus
#
# La API de Factus NO usa los códigos DIAN directamente, sino sus propios IDs
# internos (ej: Cédula de Ciudadanía → id=3 en Factus, pero código DIAN 13).

import unicodedata


def _strip_accents(text: str) -> str:
    """Elimina acentos (tildes) de un string."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

# ═══════════════════════════════════════════════════════════════════════════
# 1. CÓDIGOS OFICIALES DIAN (estándar colombiano)
# ═══════════════════════════════════════════════════════════════════════════

DIAN_CONSTANTS = {
    # ── Tipos de documento de identidad (códigos DIAN oficiales) ──────────
    "document_types": {
        "registro civil": "11",
        "tarjeta de identidad": "12",
        "cédula de ciudadanía": "13",
        "tarjeta de extranjería": "21",
        "cédula de extranjería": "22",
        "nit": "31",
        "pasaporte": "41",
        "documento de identificación extranjero": "42",
        "pep": "47",
        "ppt": "48",
    },
    # ── Métodos de pago DIAN ─────────────────────────────────────────────
    "payment_methods": {
        "efectivo": "10",
        "consignación bancaria": "42",
        "consignación": "42",
        "transferencia": "47",
        "transferencia débito bancaria": "47",
        "tarjeta crédito": "48",
        "tarjeta débito": "49",
    },
    # ── Formas de pago ───────────────────────────────────────────────────
    "payment_forms": {
        "contado": "1",
        "crédito": "2",
    },
    # ── Tipos de organización ────────────────────────────────────────────
    "organization_types": {
        "persona jurídica": "1",
        "persona natural": "2",
    },
    # ── Tipos de impuesto ────────────────────────────────────────────────
    "tax_types": {
        "iva": "01",
        "inc": "04",
        "ultraprocesados": "35",
    },
    # ── Retenciones ──────────────────────────────────────────────────────
    "retentions": {
        "reteiva": "05",
        "reterenta": "06",
    },
    # ── Tipos de documento para rangos de numeración ─────────────────────
    "numbering_doc_types": {
        "factura": "21",
        "nota crédito": "22",
        "documento soporte": "24",
    },
    # ── Códigos de documento (campo `document` en factura) ───────────────
    "doc_codes": {
        "factura electrónica": "01",
        "factura": "01",
        "instrumento electrónico": "03",
    },
    # ── Tipos de operación ───────────────────────────────────────────────
    "operation_types": {
        "estándar": "10",
        "mandatos": "11",
        "transporte": "12",
    },
    # ── Códigos de corrección (notas crédito) ────────────────────────────
    "correction_codes": {
        "devolución parcial": "1",
        "anulación": "2",
        "rebaja o descuento": "3",
        "ajuste de precio": "4",
        "descuento pronto pago": "5",
        "descuento por volumen": "6",
    },
    # ── Estándar de identificación del producto ──────────────────────────
    "standard_codes": {
        "estándar contribuyente": "1",
        "unspsc": "2",
        "partida arancelaria": "3",
        "gtin": "4",
    },
    # ── Códigos de evento DIAN ───────────────────────────────────────────
    "event_codes": {
        "acuse de recibo": "030",
        "reclamo": "031",
        "recibo del bien": "032",
        "aceptación expresa": "033",
        "aceptación tácita": "034",
    },
    # ── Conceptos de reclamo ─────────────────────────────────────────────
    "claim_concepts": {
        "documento con inconsistencias": "1",
        "mercancía no entregada": "2",
        "mercancía entregada parcialmente": "3",
        "servicio no prestado": "4",
    },
    # ─── Códigos de recargos y descuentos (allowance_charges) ────────────
    "allowance_charge_concepts": {
        "descuento por pronto pago": "01",
        "descuento por volumen": "02",
        "descuento por promoción": "03",
        "recargo por interés": "53",
        "recargo por mora": "54",
        "otros recargos": "ZZ",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. FACTUS API IDs — lo que realmente espera la API de Factus
# ═══════════════════════════════════════════════════════════════════════════
# La API de Factus tiene sus propios IDs internos, diferentes de los códigos
# DIAN oficiales. Usar estas constantes al construir requests a la API.

FACTUS_API_IDS = {
    # ── Tipos de documento de identidad (Factus API) ─────────────────────
    # Tabla oficial: https://developers.factus.com.co/tablas-de-referencia/
    "identification_document_ids": {
        "registro civil": 1,
        "tarjeta de identidad": 2,
        "cédula de ciudadanía": 3,
        "tarjeta de extranjería": 4,
        "cédula de extranjería": 5,
        "nit": 6,
        "pasaporte": 7,
        "documento identificación extranjero": 8,
        "pep": 9,
        "nit otro país": 10,
        "nuip": 11,
    },
    # ── IDs de tributos para clientes ────────────────────────────────────
    "customer_tribute_ids": {
        "iva régimen común": 1,
        "iva régimen simplificado": 2,
        "no aplica": 21,
        "gran contribuyente": 22,
        "autorretenedor": 23,
        "agente de retención iva": 24,
        "régimen simple de tributación": 25,
    },
    # ── IDs de organización legal ────────────────────────────────────────
    "legal_organization_ids": {
        "persona jurídica": 1,
        "persona natural": 2,
    },
    # ── IDs de tributos para productos/items ─────────────────────────────
    "item_tribute_ids": {
        "iva": 1,
        "inc": 2,
        "iva e inc": 3,
        "no causa": 4,
    },
    # ── IDs de unidad de medida (DIAN, usados por Factus) ───────────────
    # Códigos UN/ECE rec. 20
    "unit_measure_ids": {
        "unidad": 70,
        "kilogramo": 46,
        "kgm": 414,
        "libra": 96,
        "tonelada": 94,
        "metro": 45,
        "metro cuadrado": 30,
        "metro cúbico": 66,
        "litro": 85,
        "galón": 87,
        "gll": 874,
        "caja": 80,
        "docena": 77,
        "paquete": 79,
        "par": 76,
        "hora": 158,
        "día": 151,
        "mes": 154,
        "año": 156,
        "porcentaje": 104,
        "gramo": 47,
        "mililitro": 5,
        "barril": 81,
    },
    # ── IDs de municipio (códigos DIAN) ─────────────────────────────────
    # Lista completa vía GET /v1/municipalities?name=
    # Aquí solo los más comunes. Para el resto, consultar la API.
    "municipality_ids": {
        "bogotá": "11001",
        "medellín": "05001",
        "cali": "76001",
        "barranquilla": "08001",
        "cartagena": "13001",
        "cúcuta": "54001",
        "bucaramanga": "68001",
        "pereira": "66001",
        "manizales": "17001",
        "ibagué": "73001",
        "pasto": "52001",
        "villavicencio": "50001",
    },
    # ── IDs de países (ISO 3166-1 alfa-2) ────────────────────────────────
    "country_ids": {
        "colombia": "CO",
        "brasil": "BR",
        "perú": "PE",
        "ecuador": "EC",
        "venezuela": "VE",
        "panamá": "PA",
        "méxico": "MX",
        "chile": "CL",
        "argentina": "AR",
        "uruguay": "UY",
        "paraguay": "PY",
        "bolivia": "BO",
        "estados unidos": "US",
        "canadá": "CA",
        "españa": "ES",
        "reino unido": "GB",
        "alemania": "DE",
        "francia": "FR",
        "italia": "IT",
        "china": "CN",
        "japón": "JP",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _normalize_name(name: str) -> str:
    """Normaliza: minúsculas, sin acentos, sin espacios al inicio/final."""
    return _strip_accents(name.strip().lower())


def get_dian_code(category: str, name_or_alias: str) -> str:
    """
    Busca un código DIAN oficial a partir de su descripción o alias.
    Búsqueda insensible a mayúsculas/minúsculas y sin acentos.

    Args:
        category: Una categoría de DIAN_CONSTANTS (e.g. "document_types").
        name_or_alias: Nombre o alias para buscar.

    Returns:
        El código DIAN correspondiente (string).

    Raises:
        ValueError: Si la categoría o el nombre no existen.
    """
    if category not in DIAN_CONSTANTS:
        raise ValueError(
            f"Invalid category '{category}'. Available: {list(DIAN_CONSTANTS.keys())}"
        )

    category_map = DIAN_CONSTANTS[category]
    normalized_key = _normalize_name(name_or_alias)

    if normalized_key in category_map:
        return category_map[normalized_key]

    # Intentar también contra claves normalizadas
    for key, code in category_map.items():
        if _normalize_name(key) == normalized_key:
            return code

    raise ValueError(
        f"Name or alias '{name_or_alias}' not found in category '{category}'."
    )


def get_factus_api_id(category: str, name_or_alias: str) -> int | str:
    """
    Busca un ID de la API de Factus a partir de su descripción.
    Búsqueda insensible a mayúsculas/minúsculas y sin acentos.

    Args:
        category: Una categoría de FACTUS_API_IDS
                  (e.g. "identification_document_ids").
        name_or_alias: Nombre o alias para buscar.

    Returns:
        El ID numérico o código string que espera la API de Factus.

    Raises:
        ValueError: Si la categoría o el nombre no existen.
    """
    if category not in FACTUS_API_IDS:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Available: {list(FACTUS_API_IDS.keys())}"
        )

    category_map = FACTUS_API_IDS[category]
    normalized_key = _normalize_name(name_or_alias)

    if normalized_key in category_map:
        return category_map[normalized_key]

    # Intentar también contra claves normalizadas
    for key, code in category_map.items():
        if _normalize_name(key) == normalized_key:
            return code

    raise ValueError(
        f"Name or alias '{name_or_alias}' not found in "
        f"Factus category '{category}'."
    )
