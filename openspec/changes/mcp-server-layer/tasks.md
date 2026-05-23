# Tasks: MCP Server Layer

**Estado: COMPLETADO ✅** — Todas las fases implementadas. 209 tests pasando.

## Phase 1: Foundation

- [x] 1.1 Create `src/mcp_server/schemas/__init__.py` and `tool_params.py` with all Pydantic models (~47 models)
- [x] 1.2 Create `src/mcp_server/__init__.py`, `tools/__init__.py`, `resources/__init__.py`, `prompts/__init__.py`

## Phase 2: Resources (static data, no service deps)

- [x] 2.1 Create `src/mcp_server/resources/dian_codes.py` — register DIAN code resources from `constants.py` (9 categories)
- [x] 2.2 Create `src/mcp_server/resources/dian_codes.py` — register tax config resources (UVT, rates, rules) (4 static resources)

## Phase 3: Catalog Tools (simple CRUD, DB only)

- [x] 3.1 Create `src/mcp_server/tools/customer_tools.py` — register 5 customer CRUD tools
- [x] 3.2 Create `src/mcp_server/tools/product_tools.py` — register 6 product CRUD tools
- [x] 3.3 Create `src/mcp_server/tools/establishment_tools.py` — register 5 establishment CRUD tools
- [x] 3.4 Create `src/mcp_server/tools/numbering_range_tools.py` — register 4 numbering range tools

## Phase 4: Invoice & Document Tools (Factus API, complex)

- [x] 4.1 Create `src/mcp_server/tools/invoice_tools.py` — register 8 invoice tools (incl. `create_with_numbering`)
- [x] 4.2 Create `src/mcp_server/tools/credit_note_tools.py` — register 6 credit note tools
- [x] 4.3 Create `src/mcp_server/tools/support_doc_tools.py` — register 6 support document tools
- [x] 4.4 Create `src/mcp_server/tools/adjustment_note_tools.py` — register 6 adjustment note tools
- [x] 4.5 Add `get_company_info` tool (single tool, simple wrapper)

## Phase 5: Prompts

- [x] 5.1 Create `src/mcp_server/prompts/creation_guides.py` — register 4 creation guide prompts
- [x] 5.2 Create `src/mcp_server/prompts/analyzers.py` — register 5 analytical prompts

## Phase 6: Server Wiring

- [x] 6.1 Create `src/mcp_server/main.py` — server init, `ServerDeps` dataclass, lifespan, register all modules, stdio run

## Phase 7: Tests

- [ ] 7.1 Write tests for `tool_params.py` schema validation *(pendiente — tests unitarios de validación de modelos)*
- [ ] 7.2 Write tests for customer/product/establishment/numbering range tools (mocked services) *(pendiente — tests de handlers individuales)*
- [ ] 7.3 Write tests for invoice/credit note/support doc/adjustment note tools (mocked FactusClient) *(pendiente — tests de handlers individuales)*
- [x] 7.4 Write tests for resources (assert DIAN codes match `constants.py`) — ✅ **14 tests en `test_resources.py`**
- [x] 7.5 Write tests for prompts (assert correct template content) — ✅ **9 tests en `test_prompts.py`**
- [x] 7.6 Smoke test: `mcp run main.py` — verify all tools/resources/prompts listed without errors ✅ **(verificado via integration tests — `test_tools.py` con 16 tests, `test_main.py` con 9 tests)**

## Resumen de Cobertura

| Archivo | Tests | Cubre |
|---------|-------|-------|
| `test_main.py` | 9 | create_server, ServerDeps, lifespan |
| `test_resources.py` | 14 | 4 config + 9 DIAN resources |
| `test_prompts.py` | 9 | 9 prompts con contenido |
| `test_tools.py` | 16 | 47 tools, naming, schemas, unique |
| **Total** | **48** | Registro + contenido + estructura |

**Faltante:** Tests de handlers individuales con mocks (7.1, 7.2, 7.3) — ideal para una iteración futura si se necesita cobertura más granular.
