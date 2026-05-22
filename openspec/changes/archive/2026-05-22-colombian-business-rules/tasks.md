# Tasks: Colombian Business Rules

## Phase 1: Tax Module (Foundation)

- [ ] 1.1 Create `src/services/tax/__init__.py` — package marker
- [ ] 1.2 Create `src/services/tax/config.py`:
  - UVT value (47,000), all threshold constants
  - ReteRenta rates per customer type
  - ReteIVA rate constant
  - ReteICA default rates (Bogotá)
  - ReteGMF rate constant
  - Payment method codes that trigger ReteGMF
- [ ] 1.3 Create `src/services/tax/withholding.py`:
  - `calculate()` — main function orchestrating all sub-calculations
  - `_rete_renta_rate()` — determine rate or None
  - `_rete_iva_per_item()` — calculate ReteIVA for each IVA-taxed item
  - `_rete_ica_per_item()` — calculate ReteICA for service items
  - `_rete_gmf_amount()` — calculate 4x1000 if applicable
  - `_is_autorretenedor()` — tribute_code == "08"
  - `_is_gran_contribuyente()` — tribute_code in ("08", "22")

## Phase 2: Mappers & Validators

- [ ] 2.1 Create `src/services/mappers.py`:
  - `customer_to_factus_dict(customer, establishment)` — maps all fields + converts IDs to DIAN codes
  - `product_to_factus_dict(product, quantity, discount_rate)` — maps all fields + converts IDs to DIAN codes
  - `_map_identification_document_id(id: int) -> str` — Factus ID → DIAN code
  - `_map_unit_measure_id(id: int) -> str` — Factus ID → DIAN code
- [ ] 2.2 Create `src/services/validators.py`:
  - `InvoiceValidator.validate_customer()` — checks identification, names/company, email, municipality
  - `InvoiceValidator.validate_items()` — checks code_reference, price >= 0, quantity > 0
  - `InvoiceValidator.validate_payment()` — checks at least one payment detail
  - `InvoiceValidator.validate()` — runs all and returns combined errors

## Phase 3: InvoiceService Enhancement

- [ ] 3.1 Modify `src/schemas/dto.py`:
  - Add `allowance_charges: Optional[list[dict]]` to `InvoiceCreate`
- [ ] 3.2 Modify `src/services/invoice_service.py`:
  - Add `create_with_numbering()` method:
    - Accepts `data`, `numbering_range_id`, `numbering_service`, `establishment`
    - Calls `NumberingRangeService.next_available()`
    - Calls `customer_to_factus_dict()` if customer is a Customer model
    - Calls `product_to_factus_dict()` for each item if items are Product models
    - Calls `WithholdingTaxCalculator.calculate()` and embeds result per-item
    - Calls `_enrich_with_totals()`
    - Calls `InvoiceValidator.validate()` before sending
    - Sends to Factus API
    - Returns response
  - Modify `_build_request()` — include `allowance_charges` in payload if present
  - Rewrite `_enrich_with_totals()`:
    - For each item, read `taxes[]` array
    - Calculate gross_value = price * quantity * (1 - discount_rate/100)
    - Calculate tax per item using item's specified rates: `gross * (rate / (100 + rate))`
    - Sum all taxes for total
    - Include allowance_charges in total (discounts reduce, surcharges increase)
    - Set payment_details[0].amount to final total
  - Add `_calculate_item_taxes(item: dict) -> tuple[Decimal, Decimal]` static method
- [ ] 3.3 Modify `src/services/__init__.py` — export new modules

## Phase 4: Tests

- [ ] 4.1 Create `tests/test_services/test_tax/__init__.py` — package marker
- [ ] 4.2 Create `tests/test_services/test_tax/test_config.py`:
  - UVT value is 47000
  - Threshold constants are positive
  - ReteRenta rates exist for natural, legal, services
- [ ] 4.3 Create `tests/test_services/test_tax/test_withholding.py`:
  - `test_natural_person_below_threshold` — no ReteRenta
  - `test_natural_person_above_threshold` — ReteRenta 2.5%
  - `test_legal_entity_above_threshold` — ReteRenta 3.5%
  - `test_autorretenedor_no_reterenta` — no ReteRenta
  - `test_gran_contribuyente_reteiva` — ReteIVA 15% on IVA portion
  - `test_excluded_items_no_withholding` — no taxes on excluded items
  - `test_services_reteica` — ReteICA 0.2% for services
  - `test_electronic_payment_rete_gmf` — ReteGMF 0.4% over 100 UVT
  - `test_multiple_withholdings` — ReteIVA + ReteGMF combined
  - `test_no_withholdings` — empty result when nothing applies
  - `test_is_autorretenedor_true` — tribute_code "08" returns True
  - `test_is_gran_contribuyente_true` — tribute_code "22" returns True
- [ ] 4.4 Create `tests/test_services/test_mappers.py`:
  - `test_customer_nit_full` — full NIT customer → Factus dict
  - `test_customer_cc` — cédula de ciudadanía → DIAN code "13"
  - `test_customer_with_names` — no company, names present
  - `test_product_full` — full product → Factus item dict
  - `test_product_with_discount` — product with 10% discount
  - `test_product_excluded` — is_excluded=True → rate 0.00
  - `test_product_unit_measure_mapping` — Factus ID → DIAN code
- [ ] 4.5 Create `tests/test_services/test_validators.py`:
  - `test_valid_customer` — no errors
  - `test_missing_identification` — error returned
  - `test_missing_names_and_company` — error returned
  - `test_missing_email` — error returned
  - `test_valid_items` — no errors
  - `test_missing_code_reference` — error with index
  - `test_negative_price` — error
  - `test_zero_quantity` — error
  - `test_empty_payment` — error
  - `test_multiple_errors` — combined error list
  - `test_valid_payload_all_ok` — empty list
- [ ] 4.6 Modify `tests/test_services/test_invoice_service.py`:
  - `test_create_with_numbering_success` — mock NumberingRangeService, verify payload structure
  - `test_create_with_numbering_range_exhausted` — error propagated
  - `test_create_with_numbering_validation_error` — ValueError raised before API call
  - `test_create_with_allowance_charges` — allowance_charges in payload
  - `test_per_item_tax_calculation` — items with different tax rates
  - `test_tax_with_multiple_rates` — item with IVA + INC
  - `test_zero_tax_item` — item with 0% rate
