import pytest
from src.core.constants import get_dian_code

def test_get_dian_code_valid():
    # Mapeos válidos de tipos de documento
    assert get_dian_code("document_types", "Cédula de ciudadanía") == "13"
    assert get_dian_code("document_types", "nit") == "31"
    assert get_dian_code("document_types", "Pasaporte") == "41"

    # Mapeos válidos de métodos de pago
    assert get_dian_code("payment_methods", "Efectivo") == "10"
    assert get_dian_code("payment_methods", "transferencia") == "47"

    # Formas de pago
    assert get_dian_code("payment_forms", "Contado") == "1"
    assert get_dian_code("payment_forms", "crédito") == "2"

    # Tipos de organización
    assert get_dian_code("organization_types", "Persona Jurídica") == "1"
    assert get_dian_code("organization_types", "persona natural") == "2"

    # Tipos de impuestos
    assert get_dian_code("tax_types", "IVA") == "01"
    assert get_dian_code("tax_types", "INC") == "04"

    # Retenciones
    assert get_dian_code("retentions", "ReteIVA") == "05"
    assert get_dian_code("retentions", "ReteRenta") == "06"

    # Tipos de documento de numeración
    assert get_dian_code("numbering_doc_types", "Factura") == "21"
    assert get_dian_code("numbering_doc_types", "Nota Crédito") == "22"

def test_get_dian_code_invalid_category():
    with pytest.raises(ValueError) as exc:
        get_dian_code("invalid_category", "Efectivo")
    assert "Invalid category" in str(exc.value)

def test_get_dian_code_invalid_name():
    with pytest.raises(ValueError) as exc:
        get_dian_code("payment_methods", "NoExiste")
    assert "not found in category" in str(exc.value)
