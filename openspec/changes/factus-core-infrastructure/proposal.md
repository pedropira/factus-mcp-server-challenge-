# Proposal: Core Infrastructure

## Intent

Implement the core configuration, DIAN code constants, and the async Factus HTTP client with invisible on-demand authentication.

## Scope

### In Scope
- Setup of environment configuration using `pydantic-settings`.
- Mapping of DIAN reference tables (document types, taxes, municipalities).
- Integration of `httpx.AsyncAuth` class for silent OAuth2 login/refresh.
- Configured `.env` file template and validation on server start.

### Out of Scope
- Local database model creation or CRUD repositories.
- Services for invoices, credit notes, and support documents.
- MCP protocol layers (tools, resources, prompts).

## Capabilities

### New Capabilities
- `core-configuration`: Validation of global settings from environment variables.
- `dian-constants`: Resolution of fiscal codes for Colombian localization.
- `factus-client`: Silent, auto-refreshing authentication client for the Factus API.

### Modified Capabilities
None

## Approach

1. Create `src/core/config.py` using `Settings` from `pydantic-settings`.
2. Define lists and dicts of DIAN constants in `src/core/constants.py`.
3. Implement `FactusAuth(httpx.AsyncAuth)` in `src/infrastructure/factus_client.py`. It holds the `access_token` and expiration in memory, refreshing it using client credentials when needed.
4. Provide unit tests using `pytest` and `pytest-asyncio` to assert configuration validation and OAuth token renewal mock scenarios.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/core/config.py` | New | Global configuration class. |
| `src/core/constants.py` | New | Static dictionaries for DIAN codes. |
| `src/infrastructure/factus_client.py` | New | HTTP client and async Auth flow. |
| `tests/test_infra.py` | New | Tests for config, constants, and Auth. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Expired Token Race Condition | Low | Use a mutex/lock during refresh or verify token validity before request dispatch. |
| Sandbox Down | Medium | Use robust error handling and fallback HTTP exception raising. |

## Rollback Plan

Delete files created in this change: `src/core/config.py`, `src/core/constants.py`, `src/infrastructure/factus_client.py`, and `tests/test_infra.py`.

## Dependencies

- Python packages: `pydantic-settings`, `httpx`, `pytest`, `pytest-asyncio` (already installed).

## Success Criteria

- [ ] Configurations load successfully from `.env` or raise validation errors on missing fields.
- [ ] Dictionaries resolve DIAN codes accurately.
- [ ] Custom `AsyncAuth` automatically makes OAuth POST to `/oauth/token` on the first call or when token expires, and intercepts subsequent calls correctly.
- [ ] Unit tests pass with 100% success rate.
