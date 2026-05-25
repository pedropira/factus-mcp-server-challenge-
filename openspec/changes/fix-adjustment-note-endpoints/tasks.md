# Tasks: fix-adjustment-note-endpoints

## Task 1 — Update DTO (`src/schemas/dto.py`)

**Changes:**
- `support_document_reference` → `support_document_number`
- Remove `document` field (was default "04")
- Remove `send_email` field
- Add `correction_concept_code: str` (required)
- Add `payment_details: list[dict]` (required)
- Add `created_time: Optional[str]` (optional, "HH:mm:ss")
- Add `numbering_range_id: Optional[int]` (optional)
- Add `cash_rounding_amount: Optional[str]` (optional)

**Verification:**
- No import errors
- All 6 call sites in test file compile

---

## Task 2 — Update Service (`src/services/adjustment_note_service.py`)

**Path changes (all 6):**
| Method | Old Path | New Path |
|--------|----------|----------|
| create | `/v2/support-document-adjustment-notes/validate` | `/v2/adjustment-notes/validate` |
| list | `/v2/support-document-adjustment-notes` | `/v2/adjustment-notes` |
| get_by_id→get_by_number | `/v2/support-document-adjustment-notes/{id}` | `/v2/adjustment-notes/{number}` |
| delete | `/v2/support-document-adjustment-notes/{id}` | `/v1/adjustment-notes/reference/{reference_code}` |
| download_pdf | `/v2/support-document-adjustment-notes/{id}/pdf` | `/v2/adjustment-notes/{number}/download-pdf` |
| download_xml | `/v2/support-document-adjustment-notes/{id}/xml` | `/v2/adjustment-notes/{number}/download-xml` |

**Signature changes:**
- `get_by_id(factus_id: str)` → `get_by_number(number: str)`
- `delete(factus_id: str)` → `delete(reference_code: str)`
- `download_pdf(factus_id: str)` → `download_pdf(number: str)`
- `download_xml(factus_id: str)` → `download_xml(number: str)`

**Payload change (create):**
- Remove: `document`, `send_email`
- Rename: `support_document_reference` → `support_document_number`
- Add: `correction_concept_code`, `payment_details`, `created_time`, `numbering_range_id`, `cash_rounding_amount`

**Verification:**
- `pytest tests/test_services/test_adjustment_note_service.py` passes

---

## Task 3 — Update Tests (`tests/test_services/test_adjustment_note_service.py`)

**Changes:**
- Fixture `sample_create_data` → use new DTO shape
- All mock assertions for paths → use new paths
- All mock assertions for payloads → use new payload shape
- All method calls → use new method names/signatures
- Delete test: parameter is `reference_code` not `factus_id`
- PDF/XML tests: parameter is `number` not `factus_id`

**Verification:**
- `pytest tests/test_services/test_adjustment_note_service.py -v` → all pass

---

## Task 4 — Update Tool Params (if exists)

*Only if `src/mcp_server/schemas/tool_params.py` has adjustment note params*

**Changes:**
- Remove `send_email` from adjustment note params
- Add `correction_concept_code`, `payment_details` params
- Rename `support_document_reference` param if present
- Rename `factus_id` params to `number`/`reference_code` where applicable

**Verification:**
- No import errors
- `uv run python -c "from src.mcp_server.schemas.tool_params import *; print('OK')"` passes
