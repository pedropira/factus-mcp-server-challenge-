import pytest
from pydantic import ValidationError
from src.core.config import Settings

def test_settings_missing_required_fields() -> None:
    # Debería fallar si faltan los campos obligatorios.
    # Pasamos _env_file=None para que pydantic-settings NO cargue el .env
    # y así aislar el test de cualquier configuración existente.
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="sandbox",
            _env_file=None,
        )
    # Verificamos que se queje de los campos requeridos
    errors = exc_info.value.errors()
    missing_fields = {err["loc"][0] for err in errors if err["type"] == "missing"}
    assert "FACTUS_CLIENT_ID" in missing_fields
    assert "FACTUS_CLIENT_SECRET" in missing_fields
    assert "FACTUS_USERNAME" in missing_fields
    assert "FACTUS_PASSWORD" in missing_fields
    assert "MCP_EVALUATION_KEY" in missing_fields

def test_settings_invalid_env():
    # ENV solo puede ser sandbox o production
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="invalid_env",
            FACTUS_CLIENT_ID="123",
            FACTUS_CLIENT_SECRET="abc",
            FACTUS_USERNAME="test@example.com",
            FACTUS_PASSWORD="password",
            MCP_EVALUATION_KEY="key",
        )
    errors = exc_info.value.errors()
    assert any(err["loc"][0] == "ENV" for err in errors)

def test_settings_invalid_username_format():
    # FACTUS_USERNAME debe ser un email
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="sandbox",
            FACTUS_CLIENT_ID="123",
            FACTUS_CLIENT_SECRET="abc",
            FACTUS_USERNAME="not-an-email",
            FACTUS_PASSWORD="password",
            MCP_EVALUATION_KEY="key",
        )
    errors = exc_info.value.errors()
    assert any(err["loc"][0] == "FACTUS_USERNAME" for err in errors)

def test_settings_valid_defaults():
    # Debería cargarse correctamente si le pasamos lo mínimo requerido
    settings = Settings(
        FACTUS_CLIENT_ID="123",
        FACTUS_CLIENT_SECRET="abc",
        FACTUS_USERNAME="test@example.com",
        FACTUS_PASSWORD="password",
        MCP_EVALUATION_KEY="key",
    )
    assert settings.ENV == "sandbox"
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///factus.db"
