# Archived: fix-adjustment-note-endpoints

**Archived:** 2026-05-25  
**Status:** ✅ Implemented and verified

## Summary

All 6 adjustment note endpoints corrected to match actual Factus API documentation. DTO payload rewritten to match API contract.

## Files Changed (SDD scope)

| File | Change |
|------|--------|
| `src/schemas/dto.py` | Rewrote `AdjustmentNoteCreate`: removed `document`, `send_email`; renamed `support_document_reference` → `support_document_number`; added `correction_concept_code`, `payment_details`, `created_time`, `numbering_range_id`, `cash_rounding_amount` |
| `src/services/adjustment_note_service.py` | All 6 paths corrected; `get_by_id` → `get_by_number`; `delete` uses `reference_code` via v1; payload builder updated |
| `src/mcp_server/schemas/tool_params.py` | Updated all 6 param models — renamed fields, removed `send_email`, added new required fields |
| `src/mcp_server/tools/adjustment_note_tools.py` | Updated DTO construction, service method calls, and error messages |
| `src/mcp_server/prompts/creation_guides.py` | Updated user-facing guide text |
| `tests/test_services/test_adjustment_note_service.py` | Full test rewrite — 15 tests (4 new), all passing |
| `tests/test_mcp_server/test_prompts.py` | Updated assertion to match renamed field |

## Verification

**211/211 tests passing** (no regressions)

## Learnings

- Factus uses different endpoints for adjustment notes vs all other doc types
- GET/download use document `number`, not internal `factus_id`
- DELETE is v1 and uses `reference_code`, not v2
- Create DTO requires `correction_concept_code` and `payment_details` — missing before
- `send_email` is NOT supported for adjustment notes (it is for invoices)
