# Invoice Service Specification

## Purpose

Define the service layer behavior for electronic invoice creation, querying, and synchronization with the Factus API.

## Requirements

### Requirement: INVOICE_CREATE

The system MUST provide `InvoiceService.create(data)` that orchestrates customer validation, numbering range lookup, next number computation, Factus API submission, and invoice persistence.

#### Scenario: Create invoice successfully

- GIVEN a valid `InvoiceCreate` DTO with:
  - A `customer_id` that exists
  - A `numbering_range_id` that is active and has available numbers
  - Valid invoice items
- WHEN `InvoiceService.create()` is called with an opened `FactusClient`
- THEN the following occurs in order:
  1. Customer existence is verified via `CustomerRepository`
  2. Numbering range availability is checked via `NumberingRangeService.next_available()`
  3. A Factus-compliant JSON payload is built with customer, items, and number data
  4. `FactusClient.post("/v1/bills/ebills", json=payload)` is called
  5. On success, the `Invoice` + `InvoiceItem`s + `AllowanceCharge`s are persisted
  6. The response fields (number, cufe, status, total, qr) are stored on the invoice
- AND the created `Invoice` with all response data is returned

#### Scenario: Factus API returns error

- GIVEN a valid invoice request
- WHEN `FactusClient.post()` returns a non-200 status
- THEN the invoice is NOT persisted to the database
- AND the error details are returned to the caller without crashing

#### Scenario: Customer does not exist

- GIVEN an `InvoiceCreate` with a non-existent `customer_id`
- WHEN `InvoiceService.create()` is called
- THEN a `ValueError("Customer not found")` is raised
- AND no API call is made

### Requirement: INVOICE_GET_BY_REFERENCE

The system MUST provide `InvoiceService.get_by_reference_code(code)` returning the invoice or `None`.

### Requirement: INVOICE_LIST_BY_STATUS

The system MUST provide `InvoiceService.list_by_status(status, limit)` returning invoices filtered by their Factus status code.

### Requirement: INVOICE_GET_PENDING_SYNC

The system MUST provide `InvoiceService.get_pending_sync(limit)` returning invoices without a `cufe` (not yet synchronized with Factus).

#### Scenario: No pending invoices

- GIVEN all invoices have a `cufe` value
- WHEN `InvoiceService.get_pending_sync()` is called
- THEN an empty list is returned
