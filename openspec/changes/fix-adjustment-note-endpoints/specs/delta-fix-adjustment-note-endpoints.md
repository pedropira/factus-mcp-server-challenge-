# Delta Spec: Fix Adjustment Note Endpoints

> **Change**: fix-adjustment-note-endpoints
> **Author**: AI Architect
> **Date**: 2026-05-25

## 1. Scope

This delta spec ONLY documents the corrected endpoint contracts for the `AdjustmentNoteService`. No capability structure changes — same capability, same MCP tool contract modified.

## 2. API Contract: AdjustmentNoteService

### 2.1 Create Adjustment Note

```
POST /v2/adjustment-notes/validate
Body: AdjustmentNoteCreate
```

**Payload fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `reference_code` | string | ✅ | Unique per tenant |
| `support_document_number` | string | ✅ | Renamed from `support_document_reference` |
| `correction_concept_code` | string | ✅ | NEW — Factus correction reason code |
| `created_time` | string | ❌ | Format: `HH:mm:ss` |
| `numbering_range_id` | integer | ❌ | DIAN numbering range ID |
| `payment_details` | array[object] | ✅ | NEW — at least one payment method |
| `cash_rounding_amount` | string | ❌ | "0.00" default |
| `provider` | object | ✅ | Provider data (same as invoice) |
| `items` | array[object] | ✅ | Item list |
| `observation` | string | ❌ | Max 250 chars |

**Removed fields (compared to current code):** `document`, `send_email`

### 2.2 List Adjustment Notes

```
GET /v2/adjustment-notes
Query: limit, offset, filter[status], filter[reference_code], etc.
```

Same query parameters, only path changed from `/v2/support-document-adjustment-notes`.

### 2.3 Get by Number

```
GET /v2/adjustment-notes/{number}
```

**Changed from:** `/v2/support-document-adjustment-notes/{id}`
**Parameter renamed:** `factus_id` → `number`

### 2.4 Delete

```
DELETE /v1/adjustment-notes/reference/{reference_code}
```

**Changed from:** `DELETE /v2/support-document-adjustment-notes/{id}`
**Parameter renamed:** `factus_id` → `reference_code` (the API's reference_code, not internal ID)

### 2.5 Download PDF

```
GET /v2/adjustment-notes/{number}/download-pdf
```

**Changed from:** `/v2/support-document-adjustment-notes/{id}/pdf`
**Parameter renamed:** `factus_id` → `number`

### 2.6 Download XML

```
GET /v2/adjustment-notes/{number}/download-xml
```

**Changed from:** `/v2/support-document-adjustment-notes/{id}/xml`
**Parameter renamed:** `factus_id` → `number`

## 3. Error Handling

Same as current: `FactusApiError` with `status_code`, `message`, `body`.

## 4. Return Values

All endpoints return `dict` from `response.json()` (same as before except PDF/XML which also return `dict` with base64 content instead of binary).

**PDF/XML note:** Factus returns `{"data": {"content_base64": "..."}}` not raw binary. Service should decode base64 to bytes if returning binary, or pass through as dict. This is an open question to resolve during implementation.
