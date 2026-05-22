"""
Factus MCP Server — Punto de entrada.

Valida la configuración al arranque (falla rápido si falta .env o hay
credenciales inválidas), inicializa la base de datos (crea tablas si
no existen) e inicia el servidor MCP.
"""

import asyncio

from src.core.config import Settings
from src.infrastructure.database import create_db_and_tables


def validate_config() -> Settings:
    """Valida la configuración al arranque.

    Carga y valida las variables de entorno usando Pydantic Settings.
    Si falta alguna variable requerida o tiene un formato inválido,
    eleva ValidationError y el proceso termina (fail-fast).

    Returns:
        Settings: Instancia validada de configuración.
    """
    return Settings()  # type: ignore[call-arg]


async def startup() -> Settings:
    """Rutina de inicialización del servidor.

    1. Valida configuración (fail-fast)
    2. Crea tablas de base de datos si no existen

    Returns:
        Settings: Instancia validada de configuración.
    """
    settings = validate_config()
    await create_db_and_tables(settings)
    print(
        f"Factus MCP Server starting in ENV={settings.ENV} "
        f"(DB: {settings.DATABASE_URL})"
    )
    return settings


def main() -> None:
    """Punto de entrada del servidor MCP de Factus."""
    asyncio.run(startup())


if __name__ == "__main__":
    main()
