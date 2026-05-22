# Factus MCP Server — Development Conventions

## Workflow: Two Tracks

### 🏗️ Track 1: SDD Full Cycle
For **complex or architectural changes**. Goes through the complete SDD cycle:

```
propose → design → spec → tasks → apply → verify → archive
```

**When to use:**
- Architecture changes (new modules, project structure changes)
- New features affecting multiple files or layers
- Decisions with tradeoffs (e.g. which pattern to use, which library to pick)
- Changes to public API (MCP contracts, request/response schemas)
- Breaking changes to existing data models

**Output:** Files in `openspec/changes/{change-name}/`

---

### ⚡ Track 2: Fast-track
For **predictable and bounded changes**. Decision logs are kept but no SDD cycle.

**When to use:**
- Bug fixes (fixing an error in a function)
- Predictable boilerplate (connecting a DB, adding a simple REST endpoint)
- Internal refactors that don't change behavior
- Purely technical tasks with no design ambiguity
- Configuration, dependency, or tooling adjustments

**Fast-track rules:**
1. Explain WHAT will be done and WHY before coding
2. Document important decisions in Engram (`mem_save`)
3. If an unplanned architecture decision emerges → pause and evaluate whether to escalate to SDD
4. Tests are mandatory (existing tests must still pass)

---

### How to decide

| If the change involves... | Track |
|---|---|
| Choosing between alternatives with tradeoffs | SDD |
| Deciding table/API structure | SDD |
| Adding a new MCP tool | SDD |
| Models, repos, DB connection | Fast-track |
| Fixing a bug | Fast-track |
| Internal refactor (rename, extract) | Fast-track |
| Unsure? | SDD |

---

## Project Skills

Project-level skills in `.agents/skills/` provide specialized instructions for specific tasks:

| Skill | Trigger |
|-------|---------|
| `sqlmodel-async` | When working with SQLModel models, async sessions, JSON columns, or repositories |
| `httpx-patterns` | When creating HTTP clients, implementing auth flows, or making async API requests |
| `mcp-server-python` | When creating MCP servers, registering tools, or defining tool schemas |
| `python-testing-patterns` | When writing pytest tests, fixtures, mocks, or async test cases |
| `pydantic` | When defining Pydantic models, validators, serializers, or settings |
| `fastapi-python` | When writing FastAPI-style async code with dependency injection |
| `fastapi-templates` | When setting up project structure, CRUD patterns, or service layers |

Load a skill before writing code by calling the `skill` tool with the skill name.

---

## Code Conventions

### Commits
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`
- Do NOT include "Co-Authored-By" or AI attribution
- One commit per logical change

### Tests
- Tests go in `tests/` mirroring the `src/` structure
- Use pytest with `anyio` for async tests
- All tests must pass before considering a change "complete"
- Do NOT comment out failing tests — fix them or mark as skip with a reason

### Database
- Default `DATABASE_URL`: `sqlite+aiosqlite:///factus.db`
- Startup creates tables automatically via `create_db_and_tables()` in `src/infrastructure/database.py`
- Repositories receive `AsyncSession` via dependency injection
- JSON columns are used for nested Factus API data (OrderReference, BillingPeriod, WithholdingTaxes)

---

## Project Context

### What is this?
A **Model Context Protocol (MCP) server** for integrating with **Factus**, Colombia's electronic invoicing (DIAN) platform. Enables AI agents to create, query, and manage electronic invoices through standard MCP tools.

### Tech Stack
| Technology | Role |
|---|---|
| **Python 3.14+** | Runtime |
| **uv** | Package manager |
| **SQLModel** | ORM + Pydantic models |
| **aiosqlite** | Async SQLite driver |
| **httpx** | Async HTTP client |
| **pydantic-settings** | Environment config |
| **pytest + pytest-asyncio** | Testing |
| **mcp** (Python SDK) | MCP protocol |

### Architecture (Layers)

```
src/
├── core/                  # Foundation layer
│   ├── config.py          # pydantic-settings (env vars, validation)
│   └── constants.py       # DIAN code mappings (document types, payment methods, etc.)
├── schemas/               # Data layer
│   └── models.py          # SQLModel entities (7 tables)
├── infrastructure/        # External integrations
│   ├── database.py        # Async engine, session factory, table creation
│   ├── factus_client.py   # FactusAuth (transparent OAuth2) + FactusClient (HTTP wrapper)
│   └── repositories/      # Repository pattern (CRUD per entity)
│       ├── base.py                    # BaseRepository[T] (generic)
│       ├── customer_repository.py     # + search, get_by_identification, get_by_email
│       ├── establishment_repository.py # + get_by_name
│       ├── numbering_range_repository.py # + get_active, get_by_prefix, get_default
│       └── invoice_repository.py      # + get_by_reference_code, get_by_status, get_pending_sync
│           (also: InvoiceItemRepository, WithholdingTaxRepository, AllowanceChargeRepository)
├── mcp_server/            # 🔜 MCP tools (EMPTY - not yet implemented)
├── services/              # 🔜 Business logic services (EMPTY - not yet implemented)
└── infrastructure/        # Done
```

### What's Already Built (✅)
- **Settings** (`src/core/config.py`): `ENV`, credentials, `DATABASE_URL` — validates email, required fields
- **DIAN Constants** (`src/core/constants.py`): `get_dian_code(category, name)` — 7 categories of DIAN codes
- **FactusAuth** (`src/infrastructure/factus_client.py`): httpx.Auth with transparent OAuth2:
  - Login on first request (`grant_type=password`)
  - Token caching with 30s safety margin
  - Auto-refresh on expiry (`grant_type=refresh_token`)
  - Double-checked lock (`asyncio.Lock`) for concurrent safety
  - **GOTCHA**: The `yield` inside `async_auth_flow()` is part of httpx's Auth protocol — CANNOT be extracted into separate methods because `yield` inside `async def` creates an async generator
- **FactusClient** (`src/infrastructure/factus_client.py`): Async HTTP client wrapper (`get`, `post`, `put`, `delete`), context manager, accepts mock `transport`
- **Database** (`src/infrastructure/database.py`): Lazy singleton engine, `create_db_and_tables()`, `get_session()` (FastAPI-style), `get_async_session()` (context manager)
- **6 Repositories**: All extend `BaseRepository[ModelT]` with specific query methods
- **7 SQLModel tables**:
  | Table | Purpose | Key Fields |
  |---|---|---|
  | `customers` | Client/purchaser | identification, dv, company, names, email, municipality_id |
  | `establishments` | Issuer branch | name, address, municipality_id |
  | `numbering_ranges` | DIAN authorization ranges | prefix, from_number, to_number, document_type_id, is_active |
  | `invoices` | Electronic invoice (main entity) | reference_code (unique), number, cufe, status, total, JSON: order_reference, billing_period, errors |
  | `invoice_items` | Invoice line items | code_reference, quantity, price, tax_rate, JSON: withholding_taxes, mandate |
  | `withholding_taxes` | Withholdings (flat table, alternative to JSON) | code, withholding_tax_rate |
  | `allowance_charges` | Global discounts/surcharges | is_surcharge, reason, base_amount, amount |
- **Tests** (`tests/`):
  - `test_config.py`: Settings validation (missing fields, invalid ENV, invalid email)
  - `test_constants.py`: DIAN code lookups (valid categories, invalid lookups)
  - `test_client.py`: Full auth flow coverage with `httpx.MockTransport`:
    - First request triggers login
    - Second request reuses cached token
    - Expired token triggers refresh
    - Concurrent requests → single login (lock)
    - Auth header injection, sandbox vs production URLs
    - FactusClient GET, POST with JSON body, context manager

### Gotchas & Key Decisions
1. **httpx.Auth yield pattern** — `FactusAuth.async_auth_flow()` uses `yield` to send intermediate auth requests. This is part of httpx's protocol and CANNOT be refactored into separate async methods. The `yield` only works inside the generator.
2. **Double-checked lock** — Used instead of a simple lock to avoid acquiring the lock on every request (fast path when token is valid).
3. **30s safety margin** — Token expiration subtracts 30s to prevent clock skew issues.
4. **JSON columns** — `order_reference`, `billing_period`, `errors`, `withholding_taxes`, `mandate`, `additional_properties` use SQLAlchemy `JSON` type for nested Factus API data.
5. **withholding_taxes** has TWO representations: JSON array in `InvoiceItem` AND flat table `WithholdingTax`. The JSON is for the Factus API shape, the table is for querying/reporting.
6. **SQLModel `sa_type=JSON`** — Must import `JSON` from `sqlmodel` (not `sqlalchemy`), and use `sa_type=JSON` in `Field()`.

### What's Missing / Next Steps 🔜
- `src/mcp_server/` — MCP tool definitions (create invoice, list customers, etc.)
- `src/services/` — Business logic layer (invoice creation workflow, validation, sync)
- `main.py` — Server entry point (FastAPI or MCP SDK server with startup hook)
- Integration tests against sandbox
- Factus API endpoints beyond the auth layer

### File System Map
```
factus_mcp_server/
├── AGENTS.md                # This file
├── pyproject.toml           # Project metadata + dependencies
├── .env                     # Local environment variables (gitignored)
├── factus.db                # SQLite database (auto-created, gitignored)
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings via pydantic-settings
│   │   └── constants.py     # DIAN code mappings
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py        # 7 SQLModel tables
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py      # Async engine + sessions
│   │   ├── factus_client.py # FactusAuth + FactusClient
│   │   └── repositories/
│   │       ├── base.py      # BaseRepository[T]
│   │       ├── customer_repository.py
│   │       ├── establishment_repository.py
│   │       ├── numbering_range_repository.py
│   │       └── invoice_repository.py
│   ├── mcp_server/          # 🔜 (empty)
│   └── services/            # 🔜 (empty)
├── tests/
│   ├── test_config.py
│   ├── test_constants.py
│   └── test_client.py
└── .agents/
    └── skills/              # Project-level skills
        ├── sqlmodel-async/
        ├── httpx-patterns/
        ├── mcp-server-python/
        └── python-testing-patterns/
```
