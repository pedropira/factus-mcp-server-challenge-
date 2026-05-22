from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import re

class Settings(BaseSettings):
    ENV: str = Field("sandbox")
    FACTUS_CLIENT_ID: str
    FACTUS_CLIENT_SECRET: str
    FACTUS_USERNAME: str
    FACTUS_PASSWORD: str
    MCP_EVALUATION_KEY: str
    DATABASE_URL: str 

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ("sandbox", "production"):
            raise ValueError("ENV must be either 'sandbox' or 'production'")
        return v

    @field_validator("FACTUS_USERNAME")
    @classmethod
    def validate_username_email(cls, v: str) -> str:
        # Validación de formato de email simple sin dependencias externas
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("FACTUS_USERNAME must be a valid email address")
        return v

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }
