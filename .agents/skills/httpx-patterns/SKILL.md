---
name: httpx-patterns
description: >
  Async HTTP client patterns with httpx, including transparent auth, token refresh, retry logic, and error handling.
  Trigger: When creating HTTP clients with httpx, implementing authentication flows, handling token refresh, or making async API requests.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Creating async HTTP clients with `httpx.AsyncClient`
- Implementing transparent authentication with `httpx.Auth` (token login, refresh)
- Handling token expiration and concurrent request synchronization
- Configuring timeouts, retries, and error handling for external APIs
- Making GET/POST requests with JSON bodies to REST APIs

## Critical Patterns

### 1. Transparent Auth with httpx.Auth (NOT AsyncAuth)

For httpx >= 0.28.x, use `httpx.Auth` with `async_auth_flow`. `AsyncAuth` does NOT exist in modern httpx.

```python
import asyncio
import httpx
from httpx import Auth, Request, Response

class BearerTokenAuth(Auth):
    """Transparent auth that handles login and token refresh."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._lock = asyncio.Lock()
        self._auth_flow_auth: httpx.Auth | None = None

    async def async_auth_flow(self, request: Request) -> AsyncGenerator[Request, Response]:
        # Ensure we have a token
        if self._token is None:
            async with self._lock:
                if self._token is None:
                    await self._login()

        # Clone request with auth header
        request.headers["Authorization"] = f"Bearer {self._token}"
        response = yield request

        # Handle 401 — token expired, refresh once
        if response.status_code == 401:
            async with self._lock:
                await self._login()
            request.headers["Authorization"] = f"Bearer {self._token}"
            yield request
```

### 2. Login with Token Extraction

Keep login logic in a separate async method. Parse JSON response for access_token/token_type.

```python
async def _login(self) -> None:
    """Authenticate and store token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.example.com/auth/login",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
```

### 3. Auth YIELD Must Be Inline

The `yield` in `async_auth_flow` is part of httpx's internal generator protocol. You CANNOT extract it into a separate method.

```python
# ✅ CORRECT: yield is inline in async_auth_flow
async def async_auth_flow(self, request: Request):
    # prepare...
    response = yield request
    # handle...

# ❌ WRONG: yield cannot be moved to a helper
async def helper(self, request):  # TypeError: 'async_generator' cannot be used...
    response = yield request
```

### 4. AsyncClient with Auth Injection

Create the client with the auth instance pre-configured. All requests automatically get headers.

```python
class APIClient:
    def __init__(self, base_url: str, auth: BearerTokenAuth):
        self._client = httpx.AsyncClient(base_url=base_url, auth=auth)

    async def get(self, path: str, **kwargs):
        return await self._client.get(path, **kwargs)

    async def post(self, path: str, json: dict | None = None, **kwargs):
        return await self._client.post(path, json=json, **kwargs)

    async def close(self):
        await self._client.aclose()
```

### 5. Context Manager Support

Wrap the client in `__aenter__`/`__aexit__` for `async with` usage.

```python
class APIClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

### 6. Timeout Configuration

Set explicit timeouts to avoid hanging on slow API responses. Use different timeouts for different operations.

```python
from httpx import Timeout

# Per-client timeout
client = httpx.AsyncClient(
    base_url="https://api.example.com",
    timeout=Timeout(30.0, connect=10.0, read=20.0, write=10.0)
)

# Per-request timeout override
response = await client.get("/slow-endpoint", timeout=Timeout(60.0))
```

### 7. Error Handling and Retry

Handle transient errors with exponential backoff for robustness.

```python
import asyncio
from httpx import HTTPError, HTTPStatusError, RequestError

async def fetch_with_retry(client: httpx.AsyncClient, path: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await client.get(path)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            # 4xx — don't retry client errors
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                raise
            # 5xx or 429 — retry with backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
        except RequestError:
            # Network error — retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
```

### 8. JSON Body POST (no dict() wrapper)

Pass dicts directly to `json=` parameter. httpx serializes and sets Content-Type automatically.

```python
data = {"key": "value", "nested": {"inner": 42}}
response = await client.post("/endpoint", json=data)
```

### 9. Response Validation

Always validate HTTP status codes explicitly. Use `raise_for_status()` or check `.is_success`.

```python
response = await client.get("/health")
response.raise_for_status()  # raises HTTPStatusError for 4xx/5xx

# Or check manually
if response.status_code != 200:
    raise ValueError(f"Expected 200, got {response.status_code}: {response.text}")
```

## Commands

```bash
pip install httpx

# Install with optional dependencies
pip install "httpx[http2]"       # HTTP/2 support
pip install "httpx[cli]"         # CLI tool (httpx command)
pip install "httpx[brotli]"      # Brotli compression
```

## Critical Warnings

- httpx >= 0.28 uses `httpx.Auth` (NOT `AsyncAuth`) — `AsyncAuth` does NOT exist
- The `yield` in `async_auth_flow` cannot be extracted into a helper method — it must be inline
- Always use `asyncio.Lock()` (not `threading.Lock`) for async auth flows
- Always close the client with `await client.aclose()` or use `async with`
- httpx follows redirects by default (30x) — disable with `follow_redirects=False` if not desired
