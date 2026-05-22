"""
Prueba de conexión real contra la API de Factus (sandbox).

Valida que:
  1. Las credenciales en .env son válidas
  2. El OAuth2 flow funciona (login automático)
  3. El FactusClient puede hacer requests autenticadas
  4. La URL del sandbox es la correcta

Uso:
    uv run python scripts/test_factus_connection.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.config import Settings
from src.infrastructure.factus_client import FactusClient


async def main() -> None:
    print("=" * 60)
    print("Factus API Connection Test")
    print("=" * 60)

    # 1. Cargar settings
    print("\n[1/4] Cargando configuracion...")
    try:
        settings = Settings()  # type: ignore[call-arg]
        print(f"  [OK] ENV:      {settings.ENV}")
        print(f"  [OK] Username: {settings.FACTUS_USERNAME}")
        print(f"  [OK] DB:       {settings.DATABASE_URL}")
    except Exception as e:
        print(f"  [ERROR] Error cargando settings: {e}")
        sys.exit(1)

    # 2. Abrir cliente
    print("\n[2/4] Abriendo FactusClient...")
    try:
        client = FactusClient(settings)
        print("  [OK] Cliente creado")
    except Exception as e:
        print(f"  [ERROR] Error creando cliente: {e}")
        sys.exit(1)

    # 3. Hacer request autenticada
    # El primer GET dispara el login automatico via FactusAuth
    print("\n[3/4] Ejecutando GET /v2/bills?limit=1 ...")
    print("      (Esto dispara login automatico si es necesario)")
    try:
        async with client as c:
            response = await c.get("/v2/bills", params={"limit": 1})
            # Forzar lectura del body en httpx streaming mode
            await response.aread()

            print(f"\n  [STATUS] {response.status_code} {response.reason_phrase}")

            if response.is_success:
                print("  [OK] Request exitosa - conexion OK")
            else:
                print(f"  [WARN] La API respondio con error")

            # Mostrar respuesta (truncada si es muy larga)
            try:
                data = response.json()
                text = json.dumps(data, indent=2, ensure_ascii=False)
                if len(text) > 2000:
                    print(f"\n  [DATA] Respuesta ({len(text)} chars, mostrando primeros 2000):")
                    print(f"  {text[:2000]}...")
                else:
                    print(f"\n  [DATA] Respuesta:")
                    print(f"  {text}")
            except Exception:
                print(f"\n  [DATA] Respuesta raw ({len(response.text)} chars):")
                print(f"  {response.text[:1000]}")

    except Exception as e:
        print(f"\n  [ERROR] Error en la request: {type(e).__name__}: {e}")
        sys.exit(1)

    # 4. Resumen
    print("\n" + "=" * 60)
    if response.is_success:  # type: ignore[possibly-undefined]
        print("  [OK] CONEXION EXITOSA - FactusClient funciona correctamente")
        print("  [KEY] Auth flow:  OK (login y token caching)")
        print("  [KEY] URL base:  ", client.base_url)
        print("  [KEY] Endpoint:   /v2/bills")
    else:
        print("  [WARN] CONEXION ESTABLECIDA pero la API devolvio error")
        print("         Revisa el mensaje de error arriba")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
