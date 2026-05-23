# Proposal: MCP Server Layer

## Intent

Wrap all existing Factus services (invoices, credit notes, support documents, customers, products, etc.) as MCP tools, resources, and prompts. Enable AI agents to create, query, and manage Colombian electronic invoices through standard MCP protocol — with zero hallucination risk on DIAN codes and tax calculations.

## Scope

### In Scope
- Tool definitions for all 8 service domains (~50 tools)
- Resources: DIAN code lookups, tax config (UVT, rates, rules), dynamic entity reads
- Prompts: creation guides (one per document type) + analytical prompts for user decisions
- `main.py` entry point with stdio transport and lifespan (DB init + FactusClient)
- Pydantic schemas in `schemas/tool_params.py` for all tool parameters
- Tests for all tools, resources, and prompts

### Out of Scope
- SSE transport (future: deploy as remote server)
- Auth/API key for external clients (MCP stdio is local by design)
- Web dashboard or UI

## Capabilities

### New Capabilities
- `mcp-server`: Complete MCP server exposing tools, resources, and prompts for all Factus operations
- `mcp-tools-invoice`: Invoice/credit note/support doc/adjustment note tools
- `mcp-tools-catalog`: Customer/product/establishment/numbering range/company tools
- `mcp-resources`: DIAN codes, tax config, dynamic entity URIs
- `mcp-prompts`: Creation guides and analytical prompts for end users

### Modified Capabilities
- None (this is a new layer, existing specs unchanged)

## Approach

Separated module pattern: each domain in `tools/`, `resources/`, `prompts/` exports a `register(server)` function. `main.py` creates the server, initializes dependencies (DB session, FactusClient) via lifespan, calls all register functions, and runs stdio transport. All parameters use Pydantic models in `schemas/tool_params.py` for validation and JSON Schema generation.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/mcp_server/` | New | Complete MCP server structure |
| `pyproject.toml` | Modified | Add `mcp` dependency |
| `src/services/` | Unchanged | Tools call existing services |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tool params too complex for AI to fill | Medium | `tool_params.py` with clear descriptions and optional defaults |
| MCP SDK API changes | Low | Pin version in `pyproject.toml` |

## Rollback Plan

Revert `openspec/changes/mcp-server-layer/` — tools are stateless wrappers over existing services. No DB migration needed.

## Dependencies

- `mcp` Python SDK (latest stable)

## Success Criteria

- [ ] All ~50 tools registered and callable via MCP inspector
- [ ] All resources return correct data (DIAN codes, tax config, entity reads)
- [ ] Prompts loadable by MCP clients
- [ ] Tests pass for all tool modules
- [ ] `mcp run main.py` starts without errors
- [ ] End-to-end: create invoice with numbering flow works via MCP
