# Design: MCP Server Layer

## Technical Approach

Claseless `FactusServer` encapsulating server creation, dependency injection, and module registration. Each `tools/`, `resources/`, `prompts/` submodule exports a `register(server, deps)` function. `main.py` builds deps in lifespan, creates the server, calls all register functions, and runs stdio transport. Tool params use Pydantic models for validation + JSON Schema generation.

## Architecture Decisions

### Decision: Registration Pattern

| Option | Tradeoff | Decision |
|--------|----------|----------|
| All decorators in main.py | Simple but unmaintainable >200 lines | ❌ |
| Each module exports `register(server)` | Clean separation, easy to test | ✅ |
| Class-based with self-registration | Couples tools to class lifecycle | ❌ |

### Decision: Dependency Injection

**Choice**: Lifespan creates a `ServerDeps` dataclass (FactusClient, db factory, service instances). Passed to each `register(server, deps)`.

**Rationale**: Services are stateless wrappers — create once per server lifetime. `get_async_session` factory for DB tools avoids session leaks.

### Decision: Tool Params Schema

**Choice**: One `tool_params.py` with all Pydantic models. Tool functions accept the model as single param: `async def create_invoice(params: CreateInvoiceParams) -> dict`.

**Rationale**: Pydantic auto-generates JSON Schema for MCP discovery. Single-param tools are simpler for LLMs to call than multi-param.

### Decision: Resources vs Tools

**Choice**: Static DIAN codes → Resources (no computation). Entity lookups → Tools (require DB/API calls). Tax config → Resources (static per compile).

**Rationale**: Resources are read-only URIs the LLM fetches like files. Tools execute code. Mixing them causes confusion.

## Data Flow

```
┌──────────────┐     ┌─────────────────────────────────────┐
│  MCP Client  │◄───►│  factus-mcp-server (stdio)          │
│  (AI Agent)  │     │                                     │
└──────────────┘     │  main.py                            │
                     │    ├── lifespan: init DB + Factus    │
                     │    ├── register_tools()              │
                     │    │   ├── invoice_tools.register()  │
                     │    │   ├── customer_tools.register() │
                     │    │   └── ...                       │
                     │    ├── register_resources()          │
                     │    └── register_prompts()            │
                     │                                     │
                     │  Tools ──→ Services ──→ Factus API  │
                     │  Resources ──→ static/cached data   │
                     │  Prompts ──→ static templates       │
                     └─────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_server/main.py` | Create | Server setup, lifespan, DI wiring, stdio run |
| `src/mcp_server/schemas/tool_params.py` | Create | All Pydantic models for tool parameters (20+ models) |
| `src/mcp_server/tools/__init__.py` | Create | Re-exports all register functions |
| `src/mcp_server/tools/invoice_tools.py` | Create | 8 tools: create, create_with_numbering, list, get_by_number, get_by_reference, delete, download_pdf/xml |
| `src/mcp_server/tools/credit_note_tools.py` | Create | 6 tools: create, list, get, delete, download_pdf/xml |
| `src/mcp_server/tools/support_doc_tools.py` | Create | 6 tools |
| `src/mcp_server/tools/adjustment_note_tools.py` | Create | 6 tools |
| `src/mcp_server/tools/customer_tools.py` | Create | 5 tools: create, get, search, update, delete |
| `src/mcp_server/tools/product_tools.py` | Create | 6 tools: create, get, get_by_code, search, update, delete |
| `src/mcp_server/tools/establishment_tools.py` | Create | 5 tools |
| `src/mcp_server/tools/numbering_range_tools.py` | Create | 4 tools |
| `src/mcp_server/resources/__init__.py` | Create | Re-exports register |
| `src/mcp_server/resources/dian_codes.py` | Create | Resources for DIAN codes, tax config, UVT, municipality rates |
| `src/mcp_server/prompts/__init__.py` | Create | Re-exports register |
| `src/mcp_server/prompts/creation_guides.py` | Create | 4 creation guide prompts |
| `src/mcp_server/prompts/analyzers.py` | Create | 5 analytical prompts |

## Interfaces / Contracts

```python
# schemas/tool_params.py — example
class CreateInvoiceParams(BaseModel):
    reference_code: str = Field(description="Unique document reference")
    customer: dict = Field(description="Customer data (Factus API dict)")
    items: list[dict] = Field(description="Invoice items")
    payment_details: list[dict] = Field(description="Payment info")
    send_email: bool = Field(default=False)
    allowance_charges: list[dict] | None = Field(default=None)

# tools/invoice_tools.py — pattern
def register(server: Server, deps: ServerDeps) -> None:
    @server.tool()
    async def create_invoice(params: CreateInvoiceParams) -> dict:
        """Create an electronic invoice in Factus."""
        svc = InvoiceService(deps.factus)
        return await svc.create(InvoiceCreate(**params.model_dump()))
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Tool params validation | Test Pydantic models directly |
| Unit | Tool logic (with mocked services) | Mock FactusClient + services, verify correct calls |
| Integration | Resource data accuracy | Assert DIAN codes match constants.py |
| Smoke | Server starts and registers all tools | `mcp run main.py` + list-tools |

## Migration / Rollout

No migration required. New files only, existing services unchanged.

## Open Questions

- [ ] None — all decisions resolved in discussion with stakeholder.
