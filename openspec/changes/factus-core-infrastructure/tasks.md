# Tasks: Core Infrastructure

## Phase 1: Foundation (Configuration & Constants)

- [x] 1.1 **[RED]** Create `tests/test_config.py` asserting validation failures on missing required variables and invalid formats (e.g. invalid email).
- [x] 1.2 **[GREEN]** Implement `src/core/config.py` using `Settings` from `pydantic-settings` to load configurations and satisfy config tests.
- [x] 1.3 **[RED]** Create `tests/test_constants.py` asserting correct DIAN code lookups (e.g. "Cédula de ciudadanía" -> "13", "Efectivo" -> "10", "Bogotá" -> "11001").
- [x] 1.4 **[GREEN]** Implement `src/core/constants.py` containing complete DIAN constant mappings and a lookup helper to satisfy constant tests.

## Phase 2: Factus Async Client & Auth

- [x] 2.1 **[RED]** Create `tests/test_client.py` asserting on-demand auth flows (first request logins, second requests use cache, expired tokens trigger renew) using mocked HTTP transport.
- [x] 2.2 **[GREEN]** Implement `FactusAuth(httpx.Auth)` in `src/infrastructure/factus_client.py` with `asyncio.Lock` and token validity checking.
- [x] 2.3 **[GREEN]** Implement `FactusClient` wrapping `httpx.AsyncClient` with `FactusAuth` instance in `src/infrastructure/factus_client.py`.
- [x] 2.4 **[REFACTOR]** Clean up types, docstrings, and handle potential API exceptions in `src/infrastructure/factus_client.py`.

## Phase 3: Setup & Verification

- [x] 3.1 **[RED/GREEN]** Define default values in `.env` and write startup validation hook in `main.py` calling `Settings()`.
- [x] 3.2 **[VERIFY]** Run full test suite with `pytest` and verify 100% success rate.
