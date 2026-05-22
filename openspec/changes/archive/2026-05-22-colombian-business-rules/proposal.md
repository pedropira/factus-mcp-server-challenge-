# Proposal: Colombian Business Rules for Invoice Service

## Intent

Add Colombian tax business rules to the existing Factus API services layer. The current `InvoiceService` is a thin HTTP wrapper — it passes raw dicts to Factus API with no understanding of Colombian tax law. This change adds:

1. **Withholding tax auto-calculation** — ReteRenta, ReteIVA, ReteICA, ReteFUENTE, ReteGMF based on customer type, product type, and amounts
2. **AllowanceCharge support** — Global discounts/surcharges in the invoice payload
3. **DIAN validation rules** — Pre-submit validation of mandatory fields, combinations, and ranges
4. **Tax calculation per item** — Respect each item's tax_rate instead of assuming 19% IVA
5. **Mapper helpers** — Convert local DB models (Customer, Product) into Factus API dict format
6. **Numbering range integration** — `next_available()` called before invoice creation

## Background

The services were implemented after the original SDD (`openspec/changes/archive/2026-05-21-services-layer/`) but took a different approach:

| Aspect | Archived Design | Actual Implementation |
|--------|----------------|----------------------|
| Invoice persistence | Local DB | **Factus API is source of truth** (no local DB) |
| InvoiceService input | Structured DTOs | **Raw dicts** pass-through to Factus API |
| Factus endpoint | `/v1/bills/ebills` | **`/v2/bills/validate`** (v2) |
| Tax calculation | Not specified | Hardcoded 19% IVA on everything |
| Withholding tax | Not specified | **Not implemented** |

The actual implementation is leaner and more pragmatic (Factus as source of truth eliminates sync issues). This proposal builds ON TOP of what exists — not a rewrite.

## Scope

### In Scope

| Feature | Description |
|---------|-------------|
| **WithholdingTax calculator** | Module that determines applicable witholdings for an invoice based on customer (`tribute_code`), items (`tax_rate`, `is_excluded`, amounts), and Colombian thresholds |
| **AllowanceCharge support** | Allow passing `allowance_charges` in `InvoiceCreate` and include them in the Factus payload |
| **Tax calculation per item** | `_enrich_with_totals()` rewritten to use each item's actual tax rates instead of hardcoded 19% |
| **Mapper helpers** | `customer_to_factus_dict(customer: Customer) -> dict` and `product_to_factus_dict(product: Product) -> dict` |
| **Numbering range + send** | New method `create_with_numbering()` that gets next available number, builds payload, sends to Factus |
| **DIAN pre-validation** | Validate mandatory fields before sending to Factus API (customer fields, item fields, ranges) |
| **Factus API error handling** | Improved error parsing for common Factus errors (409 duplicate, 422 validation) |
| **Tests** | Unit tests for withholding calculator, mapper helpers, validation, and integration tests for InvoiceService |

### Out of Scope
- MCP tool implementation (separate change)
- Local DB persistence for invoices (Factus remains source of truth)
- Credit notes, debit notes, support documents business rules (separate changes)
- Reports, exports, dashboards
- Real sandbox credentials / CI integration with Factus sandbox

## Capabilities

### New Capabilities
- `WithholdingTaxCalculator` — Determines applicable taxes per Colombian law
- `FactusPayloadMapper` — Converts DB models to Factus API dict format
- `InvoiceValidator` — Pre-submit DIAN validation rules

### Modified Capabilities
- `InvoiceService.create()` — Now supports `allowance_charges`, proper tax calculation per item
- `InvoiceService.create_with_numbering()` — New method: range → number → build → send
- `InvoiceService._enrich_with_totals()` — Rewritten to respect per-item tax rates
- `InvoiceCreate` DTO — Add `allowance_charges` field

## Approach

1. **WithholdingTaxCalculator** (`src/services/tax/`):
   - Pure functions (no IO) — easy to unit test
   - Receive customer info (`tribute_code`, `identification_document_code`), items (list of dicts with `price`, `quantity`, `tax_rate`, `is_excluded`), gross total
   - Return list of withholding tax dicts matching Factus API format: `[{"code": "06", "withholding_tax_rate": "2.5", "tax_amount": "..."}]`
   - Apply Colombian thresholds:
     - **ReteRenta (06)**: 2.5% on purchases > 27 UVT (~$1,045,000 COP in 2026) from persons, 3.5% from companies, 4% for services
     - **ReteIVA (05)**: 15% on purchases from Grandes Contribuyentes, 11% from Regimen Simple
     - **ReteICA (07)**: 0.2% to 1% depending on municipality and activity
     - **ReteFUENTE (08)**: on withholdings at source (wider range 0.5%-11%)
     - **ReteGMF/4x1000 (20)**: 0.4% on payments > 100 UVT via financial system
   - **Autorretenciones**: If customer `tribute_code` is "08" (Gran Contribuyente con Autorretención), certain rates change

2. **AllowanceCharge support**:
   - Add `allowance_charges: list[dict]` to `InvoiceCreate` DTO
   - Pass through to Factus payload inside `_build_request()`
   - Include in total calculation within `_enrich_with_totals()`

3. **Tax calculation rewrite**:
   - Read each item's `taxes` array (e.g. `[{"code": "01", "rate": "19.00"}]`)
   - Calculate tax per item using the item-specific rate(s)
   - Sum taxes for gross/tax/total calculation
   - Support items with `is_excluded: true` (0% tax, customer still pays VAT to supplier but doesn't charge it)

4. **Mapper helpers**:
   - `customer_to_factus_dict(customer: Customer, establishment: Establishment) -> dict`
   - `product_to_factus_dict(product: Product, quantity: int | str) -> dict`
   - Handle field name mapping (e.g., `identification_document_id` → `identification_document_code`, `municipality_id` → `municipality_code`)

5. **Numbering range integration**:
   - `create_with_numbering(data: InvoiceCreate, numbering_range_id: int)`:
     1. Load range from `NumberingRangeRepository`
     2. Call `NumberingRangeService.next_available(range_id)`
     3. Build payload with prefix + number
     4. Send to Factus API
     5. Return result

6. **DIAN pre-validation**:
   - Validate customer has required fields (identification, name/company, email, municipality)
   - Validate items have required fields (code_reference, price, quantity, taxes)
   - Validate total ranges
   - Validate numbering range is active and has available numbers

## Withholding Tax Rules (Colombian Law)

### General Rules
- **ReteRenta (06)**: Applied to purchases of goods/services from:
  - Natural persons: 2.5% on amounts > 27 UVT
  - Legal entities (not Grandes Contribuyentes): 3.5%
  - Services: 4% on payments > 4 UVT
  - Purchases from Grandes Contribuyentes (tribute_code "08"): NO ReteRenta (they self-withhold)

- **ReteIVA (05)**: Applied when purchaser is a Grand Contribuyente (tribute_code "08"):
  - 15% on purchases of goods subject to IVA
  - 11% on purchases from Regimen Simple de Tributación
  - Applied on the IVA portion only

- **ReteICA (07)**: Municipal industry and commerce tax
  - Rate varies by municipality (Bogotá 0.2% for services, 0.4% for commercial activities)
  - Applied on gross value
  - Optional if customer is outside the municipality

- **ReteFUENTE (08)**: Covers other withholdings at source
  - 2.5% on rental payments
  - 1% on purchases from stock exchange members
  - 0.5% on purchases of coffee from producers
  - 11% on lottery/lottery prizes

- **ReteGMF/4x1000 (20)**: Gravamen a los Movimientos Financieros
  - 0.4% on payments exceeding 100 UVT made through financial system
  - Only relevant when payment method is electronic/check

### Thresholds (2026, estimated)
- 1 UVT ≈ $47,000 COP (2026 estimated)
- 27 UVT ≈ $1,269,000 COP (ReteRenta threshold)
- 4 UVT ≈ $188,000 COP (Services threshold)
- 100 UVT ≈ $4,700,000 COP (ReteGMF threshold)

### Autorretención
When customer `tribute_code` = "08" (Gran Contribuyente con Autorretención):
- The customer handles their own ReteRenta — NO ReteRenta applied by seller
- ReteIVA and ReteICA STILL apply (they are collected by seller)
- Other rules remain the same

## DIAN Code Mappings

The service must map between local DB field values and Factus API codes:

| Local DB Field | Factus API Field | Mapping |
|---------------|-------------------|---------|
| `Customer.identification_document_id` | `identification_document_code` | DIAN code: "13"=NIT, "11"=CC, "22"=CE, etc. |
| `Customer.municipality_id` | `municipality_code` | DIAN municipality code: "11001"=Bogotá |
| `Customer.tribute_id` (via `constants.py`) | `tribute_code` | "ZZ"=No aplica, "08"=Autorretención, "01"=IVA, etc. |
| `Customer.legal_organization_id` (via `constants.py`) | `legal_organization_code` | "1"=Persona Natural, "2"=Persona Jurídica |
| `Product.unit_measure_id` (via `constants.py`) | `unit_measure_code` | "94"=Unidad, "97"=Kilogramo, etc. |
| `Product.standard_code_id` (via `constants.py`) | `standard_code` | DIAN standard code for product classification |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/services/invoice_service.py` | **Modified** | Add `create_with_numbering()`, `allowance_charges`, rewrite `_enrich_with_totals()`, improved error handling |
| `src/services/tax/withholding.py` | **New** | WithholdingTaxCalculator — all Colombian tax rules |
| `src/services/tax/__init__.py` | **New** | Package marker |
| `src/services/mappers.py` | **New** | Mapper helpers: `customer_to_factus_dict()`, `product_to_factus_dict()` |
| `src/services/validators.py` | **New** | InvoiceValidator — pre-submit DIAN validation |
| `src/schemas/dto.py` | **Modified** | Add `allowance_charges` field to `InvoiceCreate` |
| `src/infrastructure/constants.py` | **Modified** | Add tribute codes, identification document codes mappings if missing |
| `src/services/__init__.py` | **Modified** | Export new modules |
| `tests/test_services/test_tax/` | **New** | Tests for WithholdingTaxCalculator |
| `tests/test_services/test_mappers.py` | **New** | Tests for mapper helpers |
| `tests/test_services/test_validators.py` | **New** | Tests for InvoiceValidator |
| `tests/test_services/test_invoice_service.py` | **Modified** | Add tests for `create_with_numbering()`, `allowance_charges`, new tax calculation |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| UVT values change yearly | Medium | UVT as constant in one place, easy to update |
| Factus API v2 shape changes | Low | Mappers centralize all API shape logic |
| Tax rules complexity → bugs | Medium | Pure functions, comprehensive unit tests for every rule |
| Autorretención edge cases | Medium | Documented test cases for each scenario |
| InvoiceService.input is raw dicts — no type safety | Medium | We keep this pattern but add validators with clear error messages |

## Rollback Plan

Revert changes to `src/services/invoice_service.py` and `src/schemas/dto.py`. Delete `src/services/tax/`, `src/services/mappers.py`, `src/services/validators.py`. Delete new test files.

## Dependencies

- Existing `InvoiceService` in `src/services/invoice_service.py`
- `FactusClient` in `src/infrastructure/factus_client.py`
- Existing repositories in `src/infrastructure/repositories/`
- `src/core/constants.py` for DIAN code lookups
- Existing tests in `tests/test_services/test_invoice_service.py`

## Success Criteria

- [ ] `WithholdingTaxCalculator` correctly determines applicable taxes for: natural person < 27 UVT, natural person > 27 UVT, legal entity, Gran Contribuyente, Gran Contribuyente con Autorretención
- [ ] `InvoiceService.create()` supports `allowance_charges` and passes them to Factus payload
- [ ] `_enrich_with_totals()` calculates tax per item using the item's specified tax rate(s), not hardcoded 19%
- [ ] `InvoiceService.create_with_numbering()` fetches next number, builds payload, sends to Factus
- [ ] `customer_to_factus_dict()` correctly maps all fields from Customer model to Factus API format
- [ ] `InvoiceValidator` catches missing required fields before API call
- [ ] All existing tests still pass
- [ ] New tests cover: 5+ withholding tax scenarios, mapper field mapping, validator rules, allowance_charges in payload
