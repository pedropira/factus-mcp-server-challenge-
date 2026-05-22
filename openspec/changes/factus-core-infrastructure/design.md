# Design: Core Infrastructure

## Technical Approach

We will implement the configurations, constants, and transparent client auth in Python 3.14 using `pydantic-settings` and `httpx`. The implementation strictly matches the specs for validation and on-demand token renewal.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|----------|--------|-------------------------|-----------|
| **Auth Interception** | Inherit from `httpx.AsyncAuth` | Manual token check in service layer | `AsyncAuth` decouples security from business logic. Every HTTP request automatically gets authenticated without services knowing about tokens. |
| **Token Safety** | `asyncio.Lock` for refresh | No lock (concurrent calls retry) | Concurrent requests during token expiration would trigger multiple auth requests. Lock ensures only one token request is made. |
| **Email Validator** | Custom regex / `@` check validator in Pydantic | `email-validator` library | Avoid adding external package dependency if a basic domain syntax validation is sufficient. |

## Data Flow

```
Request sent ──→ [FactusAuth] ──(Check Token)── [Valid?]
                     │                             │
                     │ (No/Expired)                │ (Yes)
                     ▼                             ▼
             [Acquire Lock]               [Inject Bearer Header]
                     │                             │
             [POST /oauth/token]                   │
                     │                             │
              [Update Memory]                      │
                     │                             │
                     ▼                             ▼
             [Inject Bearer Header] ───────→ [Send to Factus API]
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/core/config.py` | Create | Pydantic-Settings `Settings` class definition. |
| `src/core/constants.py` | Create | Reference dicts for DIAN document/tax/payment codes. |
| `src/infrastructure/factus_client.py` | Create | Class `FactusAuth(httpx.AsyncAuth)` and `FactusClient`. |
| `tests/test_infra.py` | Create | Async tests asserting configuration errors, constants, and Auth refresh. |
| `.env` | Modify | Add sandbox placeholders. |

## Interfaces / Contracts

### Config Settings
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    ENV: str = Field("sandbox", pattern="^(sandbox|production)$")
    FACTUS_CLIENT_ID: str
    FACTUS_CLIENT_SECRET: str
    FACTUS_USERNAME: str
    FACTUS_PASSWORD: str
    MCP_EVALUATION_KEY: str
    DATABASE_URL: str = Field("sqlite+aiosqlite:///factus.db")

    class Config:
        env_file = ".env"
```

### AsyncAuth Signature
```python
import httpx
import asyncio

class FactusAuth(httpx.AsyncAuth):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://app-sandbox.factus.com.co" if settings.ENV == "sandbox" else "https://api.factus.com.co" # (or production URL)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def async_auth_flow(self, request: httpx.Request):
        # transparent token resolution and injection
        ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `Settings` parsing | Instantiating Settings with missing/invalid params; assert raised `ValidationError`. |
| Unit | DIAN constants resolution | Verify mappings match official codes (e.g. CC -> 13, Efectivo -> 10). |
| Unit / Integration | `FactusAuth` flow | Use `httpx.MockTransport` to mock `/oauth/token` responses. Assert first call logins, second uses cached token, and third refreshes when expired. |

## Migration / Rollout

No migration required.

## Open Questions

None
