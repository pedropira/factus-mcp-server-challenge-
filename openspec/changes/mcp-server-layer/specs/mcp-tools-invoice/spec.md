# MCP Tools — Invoice Domain Specification

## Purpose

MCP tools for electronic invoices, credit notes, support documents, and adjustment notes — creation, query, download, and deletion.

## Requirements

### Requirement: Invoice Tools

The system MUST provide tools for full invoice lifecycle.

| Tool | Description |
|------|-------------|
| `create_invoice` | Simple invoice via POST /v2/bills/validate |
| `create_invoice_with_numbering` | Full Colombian flow: numbering, mappers, validation, withholding calc |
| `list_invoices` | Paginated list with filters (status, reference_code) |
| `get_invoice_by_number` | Get by Factus-assigned number |
| `get_invoice_by_reference` | Get by reference code |
| `delete_invoice` | Delete by reference code |
| `download_invoice_pdf` | Download PDF binary |
| `download_invoice_xml` | Download XML |

#### Scenario: Create invoice with numbering

- GIVEN a `CreateInvoiceWithNumberingParams` with customer/products IDs
- WHEN the tool executes
- THEN it maps models via `customer_to_factus_dict`/`product_to_factus_dict`
- THEN it validates via `InvoiceValidator`
- THEN it gets next number from `NumberingRangeService`
- THEN it calculates withholdings via `calculate_withholdings`
- THEN it calls `InvoiceService.create_with_numbering`
- THEN it returns the Factus API response

#### Scenario: Tool returns error on validation failure

- GIVEN a payload with missing customer fields
- WHEN the tool executes
- THEN it returns `{"success": false, "error": "Invoice validation failed: ..."}`

### Requirement: Credit Note Tools

The system MUST provide tools for credit note lifecycle (create, list, get, delete, download PDF/XML).

### Requirement: Support Document Tools

The system MUST provide tools for support document lifecycle (create, list, get, delete, download PDF/XML).

### Requirement: Adjustment Note Tools

The system MUST provide tools for adjustment note lifecycle (create, list, get, delete, download PDF/XML).

### Requirement: Consistent Error Shape

All tools MUST return the same response shape: `{"success": bool} | {"success": bool, "data": dict} | {"success": bool, "error": str}`.

#### Scenario: Successful response shape

- GIVEN an invoice is created successfully
- WHEN the tool returns
- THEN the response contains `{"success": true, "data": {...}}`

#### Scenario: Error response shape

- GIVEN a Factus API error
- WHEN the tool returns
- THEN the response contains `{"success": false, "error": "..."}`
