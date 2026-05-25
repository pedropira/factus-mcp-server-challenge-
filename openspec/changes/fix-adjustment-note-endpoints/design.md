# Design: Fix Adjustment Note Endpoints and Payload

## Technical Approach

Map all 6 adjustment note endpoints to their correct Factus API paths and rewrite the `AdjustmentNoteCreate` DTO + service payload builder to match the actual API contract verified from Factus docs.

## Architecture Decisions

### Decision: Use `number` not `factus_id` for GET/download

**Choice**: Rename `factus_id` parameter to `number` and use `/v2/adjustment-notes/{number}` (and `/v2/adjustment-notes/{number}/download-pdf` / `download-xml`)
**Alternatives**: Keep `factus_id` and translate to `number` via an internal lookup
**Rationale**: Factus API uses `number` (the document number returned in create response) not the internal ID. Extra lookup would add unnecessary latency. The MCP tool already receives `number` from the create/list response.

### Decision: DELETE uses `/v1/` and `reference_code`

**Choice**: `DELETE /v1/adjustment-notes/reference/{reference_code}`, parameter renamed to `reference_code`
**Alternatives**: Keep using factus_id with v2 path
**Rationale**: Factus docs explicitly show DELETE as v1 endpoint using reference_code. Using v2 path causes 404.

### Decision: `send_email` removed from create DTO

**Choice**: Remove `send_email` field from `AdjustmentNoteCreate` DTO
**Alternatives**: Keep it (default false, ignored by API)
**Rationale**: Factus API does NOT accept `send_email` for adjustment notes — it's not in the docs. Sending unused fields adds noise.

### Decision: Create payload uses Factus-compatible shape

**Choice**: Match the Factus docs exactly: `support_document_number` (not `support_document_reference`), `correction_concept_code` (required), `payment_details` (required, array), `observation` as string, no `document` field, no `send_email`
**Alternatives**: Map fields internally
**Rationale**: Direct one-to-one mapping is simpler and makes debugging against Factus API trivial.

## Data Flow

```
MCP Tool params → AdjustmentNoteCreate DTO → AdjustmentNoteService
                                                  │
               ┌──────────────────────────────────┤
               ▼                                  ▼
     POST /v2/adjustment-notes/validate   GET /v2/adjustment-notes
     DELETE /v1/adjustment-notes/         GET /v2/adjustment-notes/{n}
       reference/{code}                   GET /v2/adjustment-notes/{n}/download-pdf
                                          GET /v2/adjustment-notes/{n}/download-xml
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/schemas/dto.py` | Modify | Rewrite `AdjustmentNoteCreate`: remove `document`, rename `support_document_reference`→`support_document_number`, add `correction_concept_code`, `payment_details`, optional fields |
| `src/services/adjustment_note_service.py` | Modify | All 6 paths corrected; `get_by_id`→`get_by_number`; `delete` uses reference_code; `factus_id`→`number`; payload builder updated |
| `src/mcp_server/schemas/tool_params.py` | Modify | Adjustment note params: add `correction_concept_code`, `payment_details`; remove `send_email` |
| `tests/test_services/test_adjustment_note_service.py` | Modify | All endpoint paths, DTO construction, expected payloads, method signatures |

## Interfaces / Contracts

### AdjustedNoteCreate DTO (new)

```python
class AdjustmentNoteCreate(SQLModel):
    reference_code: str                           # Código único
    support_document_number: str                  # Número de documento soporte
    correction_concept_code: str                  # Código del motivo (obligatorio)
    created_time: Optional[str] = None             # HH:mm:ss
    numbering_range_id: Optional[int] = None
    payment_details: list[dict]                   # Array de medios de pago (obligatorio)
    cash_rounding_amount: Optional[str] = None
    provider: dict                                 # Datos del proveedor
    items: list[dict]                              # Items
    observation: Optional[str] = None
```

### Service signature changes

```python
# Before → After
get_by_id(factus_id: str) → get_by_number(number: str)
delete(factus_id: str) → delete(reference_code: str)
download_pdf(factus_id: str) → download_pdf(number: str)
download_xml(factus_id: str) → download_xml(number: str)
```

### Corrected endpoints

| Method | Current (wrong) | Correct |
|--------|----------------|---------|
| POST create | `/v2/support-document-adjustment-notes/validate` | `/v2/adjustment-notes/validate` |
| GET list | `/v2/support-document-adjustment-notes` | `/v2/adjustment-notes` |
| GET by number | `/v2/support-document-adjustment-notes/{id}` | `/v2/adjustment-notes/{number}` |
| DELETE | `/v2/support-document-adjustment-notes/{id}` | `/v1/adjustment-notes/reference/{reference_code}` |
| GET PDF | `/v2/support-document-adjustment-notes/{id}/pdf` | `/v2/adjustment-notes/{number}/download-pdf` |
| GET XML | `/v2/support-document-adjustment-notes/{id}/xml` | `/v2/adjustment-notes/{number}/download-xml` |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | All 6 ops with correct paths | Mock FactusClient, assert correct URL called |
| Unit | Create payload shape | Mock FactusClient, assert JSON body matches expected |
| Unit | Error handling | Mock 4xx/5xx, verify FactusApiError |
| Unit | get_by_reference_code still works | Uses list internally |

## Migration / Rollout

No migration required. Only internal service layer changes — no persisted data affected.

## Open Questions

- [ ] Adjust PDF/XML download: Factus returns base64 in JSON, not binary. Should we decode base64 and return bytes, or return raw JSON?
