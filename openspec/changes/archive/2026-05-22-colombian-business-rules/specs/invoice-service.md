# Spec: InvoiceService — Enhanced Creation

## Purpose

Enhance `InvoiceService.create()` and add `create_with_numbering()` with Colombian business rules: allowance_charges support, per-item tax calculation, and numbering range integration.

---

### Requirement: INVOICE_CREATE_WITH_ALLOWANCE

`InvoiceService.create()` MUST accept an `allowance_charges` field in `InvoiceCreate` and include it in the Factus API payload.

#### Scenario: Create invoice with allowance charges

- GIVEN an `InvoiceCreate` DTO with `allowance_charges` containing:
  ```python
  [
    {"is_surcharge": False, "reason": "Descuento por pronto pago", "base_amount": "50000.00", "amount": "5000.00"},
    {"is_surcharge": True, "reason": "Intereses por mora", "base_amount": "50000.00", "amount": "2500.00"},
  ]
  ```
- WHEN `InvoiceService.create()` is called
- THEN the payload sent to Factus MUST include an `allowance_charges` array with the same items
- AND `_enrich_with_totals()` MUST include allowance_charges in the total calculation
  - discount (is_surcharge=False) reduces the total
  - surcharge (is_surcharge=True) increases the total
- AND the response is returned normally

#### Scenario: Create invoice without allowance charges

- GIVEN an `InvoiceCreate` DTO with `allowance_charges` = `None` or empty
- WHEN `InvoiceService.create()` is called
- THEN the payload sent to Factus MUST NOT include `allowance_charges`
- AND behavior is identical to the current implementation

---

### Requirement: INVOICE_CREATE_TAX_PER_ITEM

`InvoiceService._enrich_with_totals()` MUST calculate taxes per item using each item's specified tax rates instead of a hardcoded rate.

#### Scenario: Items with different tax rates

- GIVEN items with different `taxes` arrays:
  ```python
  items = [
    {"quantity": "1.00", "price": "100000.00", "taxes": [{"code": "01", "rate": "19.00"}]},
    {"quantity": "1.00", "price": "50000.00", "taxes": [{"code": "01", "rate": "5.00"}]},
  ]
  ```
- WHEN `_enrich_with_totals()` is called
- THEN the first item's tax = 100,000 * 0.19 = 19,000
- AND the second item's tax = 50,000 * 0.05 = 2,500
- AND total = (100,000 + 50,000) + (19,000 + 2,500) = 171,500

#### Scenario: Item with IVA incluído (price includes tax)

- GIVEN an item where `is_excluded` is False
- AND the Factus API's price is the gross price (WITH taxes included)
- WHEN `_enrich_with_totals()` is called
- THEN the tax amount MUST be calculated as: `price * quantity * (tax_rate / (100 + tax_rate))`
- EXAMPLE: price=119,000, quantity=1, rate=19.00 → tax = 119,000 * (19/119) = 19,000
- AND gross_value = price * quantity = 119,000

#### Scenario: Item with multiple taxes

- GIVEN an item with multiple taxes: `[{"code": "01", "rate": "19.00"}, {"code": "04", "rate": "8.00"}]`
- WHEN `_enrich_with_totals()` is called
- THEN the item's total tax = sum of all individual taxes
- AND each tax is calculated separately: `price * quantity * (rate / (100 + rate))`

#### Scenario: Item with 0% tax

- GIVEN an item with `taxes = [{"code": "01", "rate": "0.00"}]`
- WHEN `_enrich_with_totals()` is called
- THEN tax_amount for that item = 0

---

### Requirement: INVOICE_CREATE_WITH_NUMBERING

`InvoiceService.create_with_numbering()` MUST coordinate with `NumberingRangeService` to auto-assign the next available invoice number.

#### Scenario: Create invoice with auto-numbering

- GIVEN a valid `InvoiceCreate` DTO and a `numbering_range_id` that has available numbers
- WHEN `InvoiceService.create_with_numbering(numbering_range_id)` is called
- THEN the following occurs:
  1. `NumberingRangeService.next_available(range_id)` is called to get the next number
  2. The prefix and number are included in the Factus payload
  3. `FactusClient.post("/v2/bills/validate", json=payload)` is called
  4. On success, the response is returned
- AND the prefix+number are visible in the payload sent (`prefix` + formatted number)

#### Scenario: Numbering range exhausted

- GIVEN a `numbering_range_id` where `next_available()` raises `ValueError("Numbering range exhausted")`
- WHEN `InvoiceService.create_with_numbering(range_id)` is called
- THEN the error is propagated to the caller
- AND no API call is made to Factus

#### Scenario: Numbering range not found

- GIVEN a non-existent `numbering_range_id`
- WHEN `InvoiceService.create_with_numbering(range_id)` is called
- THEN `ValueError("Numbering range not found")` is raised
- AND no API call is made to Factus

---

### Requirement: INVOICE_ERROR_HANDLING

The system MUST handle common Factus API errors gracefully.

#### Scenario: Duplicate reference code (409 Conflict)

- GIVEN a previously used `reference_code`
- WHEN `InvoiceService.create()` is called
- AND Factus API returns 409 with `{"message": "Ya existe un documento con el mismo reference_code", ...}`
- THEN `FactusApiError` is raised with `status_code` = 409
- AND the error message includes "duplicate" or "ya existe"

#### Scenario: Validation error (422 Unprocessable Entity)

- GIVEN an invalid payload
- WHEN `InvoiceService.create()` is called
- AND Factus API returns 422 with `{"message": "...", "errors": [...]}`
- THEN `FactusApiError` is raised with `status_code` = 422
- AND the `body` attribute includes the full error details for debugging
