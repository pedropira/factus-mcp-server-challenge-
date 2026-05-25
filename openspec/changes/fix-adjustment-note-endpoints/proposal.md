# Proposal: Fix Adjustment Note Endpoints and Payload

## Intent

Adjustment note service (`adjustment_note_service.py`) uses incorrect API paths, wrong HTTP methods, and mismatched payload fields vs. the official Factus API v2 documentation. All 6 endpoints (create, list, get, delete, download PDF, download XML) are broken against real sandbox/production.

## Scope

### In Scope
- Fix all 6 endpoint paths to match Factus docs (`/v2/adjustment-notes/...`)
- Fix DELETE endpoint (uses `/v1/` and `reference_code` instead of `/v2/` and `id`)
- Rewrite `AdjustmentNoteCreate` DTO to match actual Factus request schema
- Add missing required fields: `correction_concept_code`, `payment_details`
- Update tool params to expose new required fields
- Fix provider payload shape (add `country_code`, rename municipality)
- Update all tests to use correct paths and payloads

### Out of Scope
- Support document service (not affected)
- Credit note service (different endpoint set)
- Invoice service (different endpoint set)
- MCP tools for adjustment notes (covered in existing `mcp-tools-catalog` spec)

## Capabilities

### New Capabilities
- None (this is a fix to existing capability)

### Modified Capabilities
- `adjustment-note-service`: All endpoint paths, create payload shape, auth flow consistency

## Approach

1. Map each current endpoint to the correct Factus equivalent using official docs
2. Update `AdjustmentNoteCreate` DTO: add `correction_concept_code`, `payment_details`, rename `support_document_reference` → `support_document_number`, remove `document`, fix provider shape
3. Update `adjustment_note_service.py`: fix all paths, fix delete to use `/v1/.../reference/{code}`, fix get/download to use `number` not `factus_id`
4. Update tool params: expose `correction_concept_code`, `payment_details`
5. Update all tests to match

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/schemas/dto.py` | Modified | `AdjustmentNoteCreate` fields renamed/added/removed |
| `src/services/adjustment_note_service.py` | Modified | All 6 endpoint paths + delete uses v1 + reference_code |
| `src/mcp_server/schemas/tool_params.py` | Modified | Adjustment note tool params |
| `tests/test_services/test_adjustment_note_service.py` | Modified | All endpoint paths + payload shapes |
| `openspec/specs/` | None | No spec-level behavioral change |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Delete endpoint moved to v1 — broke if Factus reverts | Low | Already documented as v1 in official docs |
| `number` vs `factus_id` — get/download now use document number | Med | Store `number` from create response; add fallback to `get_by_id` via `get_by_reference_code`→list |
| DTO rename breaks existing callers | Low | Only called from service → service → tool param chain; no external consumers |

## Rollback Plan

Revert commit. All changes are isolated to adjustment note service + DTO + tests.

## Dependencies

None.

## Success Criteria

- [ ] All 209 tests pass
- [ ] `GET /v2/adjustment-notes` used for list instead of wrong path
- [ ] `DELETE /v1/adjustment-notes/reference/{code}` used for delete
- [ ] Create payload includes `correction_concept_code` and `payment_details`
