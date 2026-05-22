"""
Exploracion integral de la API de Factus (sandbox).

Ejecuta 4 endpoints para probar el funcionamiento completo:
  1. GET  /v2/numbering-ranges  - Rangos de numeracion activos
  2. POST /v2/bills/validate    - Crear factura estandar
  3. GET  /v2/credit-notes      - Listar notas credito
  4. GET  /v2/companies         - Informacion de la empresa

Uso:
    uv run python scripts/explore_factus_api.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.config import Settings
from src.infrastructure.factus_client import FactusClient


SEP = "=" * 70


def _print_response(label: str, response, *, truncate: int = 3000) -> None:
    """Muestra la respuesta formateada."""
    print(f"\n  -- {label} --")
    print(f"  [STATUS] {response.status_code} {response.reason_phrase}")

    try:
        data = response.json()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        if len(text) > truncate:
            print(f"  [DATA] ({len(text)} chars, showing {truncate}):")
            print(f"  {text[:truncate]}...")
        else:
            print(f"  [DATA]")
            for line in text.splitlines():
                print(f"  {line}")
    except Exception:
        print(f"  [DATA] raw ({len(response.text)} chars):")
        print(f"  {response.text[:1000]}")


def _make_reference_code() -> str:
    """Genera un reference_code unico basado en timestamp."""
    ts = int(time.time() * 1000)
    return f"EXPLORE-{ts}"


async def step_get_numbering_ranges(settings: Settings) -> int | None:
    """Paso 1: Obtener rangos de numeracion activos."""
    print(SEP)
    print("  1. RANGOS DE NUMERACION  (GET /v2/numbering-ranges)")

    try:
        async with FactusClient(settings) as client:
            response = await client.get(
                "/v2/numbering-ranges",
                params={"filter[is_active]": 1},
            )
            await response.aread()
            _print_response("Numbering ranges", response, truncate=2000)

            data = response.json()
            ranges = data.get("data", [])
            if isinstance(ranges, list) and len(ranges) > 0:
                first = ranges[0]
                rid = first.get("id")
                print(f"\n  >>> Usando numbering_range_id={rid} "
                      f"(prefix='{first.get('prefix')}')")
                return rid

            print("\n  >>> No hay rangos activos. Se omite numbering_range_id.")
            return None
    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")
        return None


async def step_create_invoice(
    settings: Settings,
    ref_code: str,
    numbering_range_id: int | None,
) -> None:
    """Paso 2: Crear factura estandar."""
    print(SEP)
    print("  2. CREAR FACTURA ESTANDAR  (POST /v2/bills/validate)")

    # Items: 1 x $10,000 + 3 x $20,000 = $70,000 (bruto sin IVA)
    # IVA 19% = $13,300
    # Total = $83,300 (mismo calculo que el ejemplo oficial)
    items = [
        {
            "code_reference": "PROD-000A",
            "name": "Producto de prueba A",
            "quantity": "1.00",
            "discount_rate": "0.00",
            "price": "10000.00",
            "unit_measure_code": "94",
            "standard_code": "999",
            "taxes": [{"code": "01", "rate": "19.00"}],
        },
        {
            "code_reference": "PROD-000B",
            "name": "Producto de prueba B",
            "quantity": "3.00",
            "discount_rate": "0.00",
            "price": "20000.00",
            "unit_measure_code": "94",
            "standard_code": "999",
            "taxes": [{"code": "01", "rate": "19.00"}],
        },
    ]

    # Calcular total automaticamente:
    # gross = sum(price * quantity * (1 - discount_rate/100))
    # tax = gross * 0.19 (para IVA 19%)
    # total = gross + tax
    gross = sum(
        float(i["price"]) * float(i["quantity"]) * (1 - float(i["discount_rate"]) / 100)
        for i in items
    )
    tax = gross * 0.19
    total = gross + tax
    total_str = f"{total:.2f}"

    body: dict = {
        "reference_code": ref_code,
        "document": "01",
        "operation_type": "10",
        "observation": "Factura de prueba - exploracion API",
        "send_email": False,
        "payment_details": [
            {
                "payment_form": "1",
                "payment_method_code": "10",
                "reference_code": f"PAY-{ref_code}",
                "amount": total_str,
            }
        ],
        "customer": {
            "identification_document_code": "13",
            "identification": "222222222222",
            "names": "Cliente de prueba",
            "address": "Calle 123 # 45-67",
            "email": "cliente@example.com",
            "phone": "3001234567",
            "legal_organization_code": "2",
            "tribute_code": "ZZ",
            "municipality_code": "11001",
        },
        "items": items,
    }

    if numbering_range_id is not None:
        body["numbering_range_id"] = numbering_range_id

    print(f"\n  [BODY] {json.dumps(body, indent=2, ensure_ascii=False)[:1500]}")

    try:
        async with FactusClient(settings) as client:
            response = await client.post("/v2/bills/validate", json=body)
            await response.aread()
            _print_response("Create invoice", response, truncate=4000)
    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")


async def step_list_credit_notes(settings: Settings) -> None:
    """Paso 3: Listar notas credito."""
    print(SEP)
    print("  3. NOTAS CREDITO  (GET /v2/credit-notes)")

    try:
        async with FactusClient(settings) as client:
            response = await client.get("/v2/credit-notes", params={"limit": 5})
            await response.aread()
            _print_response("Credit notes", response, truncate=2000)
    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")


async def step_get_company(settings: Settings) -> None:
    """Paso 4: Obtener informacion de la empresa."""
    print(SEP)
    print("  4. INFORMACION EMPRESA  (GET /v2/companies)")

    try:
        async with FactusClient(settings) as client:
            response = await client.get("/v2/companies")
            await response.aread()
            _print_response("Company info", response, truncate=2000)
    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")


async def main() -> None:
    print(SEP)
    print("  EXPLORACION INTEGRAL - API FACTUS (SANDBOX)")
    print(SEP)

    # Cargar configuracion
    print("\n[0/4] Cargando configuracion...")
    try:
        settings = Settings()  # type: ignore[call-arg]
        print(f"  [OK] ENV:      {settings.ENV}")
        print(f"  [OK] Username: {settings.FACTUS_USERNAME}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)

    ref_code = _make_reference_code()
    print(f"  [OK] Ref code: {ref_code}")

    # Paso 1 - Numeracion
    numbering_range_id = await step_get_numbering_ranges(settings)

    # Paso 2 - Crear factura
    await step_create_invoice(settings, ref_code, numbering_range_id)

    # Paso 3 - Notas credito
    await step_list_credit_notes(settings)

    # Paso 4 - Empresa
    await step_get_company(settings)

    # Resumen
    print(f"\n{SEP}")
    print("  EXPLORACION COMPLETADA")
    print(SEP)
    print()
    print("  Endpoints probados:")
    print("    [1] GET  /v2/numbering-ranges  - Rangos de numeracion")
    print("    [2] POST /v2/bills/validate    - Crear factura estandar")
    print("    [3] GET  /v2/credit-notes      - Notas credito")
    print("    [4] GET  /v2/companies         - Informacion empresa")
    print(f"  Reference code usado: {ref_code}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
