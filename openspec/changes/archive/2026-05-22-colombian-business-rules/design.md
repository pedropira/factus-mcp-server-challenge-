# Design: Colombian Business Rules for Invoice Service

## Technical Approach

Add three new modules (`tax/`, `mappers.py`, `validators.py`) and enhance the existing `InvoiceService` to include Colombian tax business logic while keeping the Factus API-as-source-of-truth pattern.

The key insight: **withholding taxes are legal obligations determined by customer type + product type + amounts**, not agent decisions. The service layer MUST calculate them automatically. AllowanceCharges (discounts/surcharges) ARE agent decisions and should be passed explicitly.

---

## Architecture Decisions

### Decision 1: WithholdingTaxCalculator — Pure Functions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Pure functions** in `src/services/tax/` | Easy to unit test, no mocking needed, composable | ✅ **Chosen** |
| Class with state | More OOP, harder to test, state unnecessary | ❌ Rejected |
| Inside InvoiceService | Violates SRP, hard to test independently | ❌ Rejected |

### Decision 2: Return format — Per-item dict

`calculate()` returns `dict[int, list[dict]]` mapping item index → list of withholding tax dicts, because Factus API requires `withholding_taxes[]` inside each item.

```python
# Returns:
{
    0: [{"code": "06", "withholding_tax_rate": "2.50", "tax_amount": "37500.00"}],
    1: [{"code": "05", "withholding_tax_rate": "15.00", "tax_amount": "2375.00"}],
}
```

### Decision 3: Mappers — Standalone Functions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Standalone functions** in `src/services/mappers.py` | Easy to import, testable, no class overhead | ✅ **Chosen** |
| Static methods on service classes | Tight coupling to services, harder to reuse | ❌ Rejected |
| Part of DTO layer | DTOs are for input, not transformation | ❌ Rejected |

### Decision 4: Validators — Static class with grouped methods

- `InvoiceValidator` with static methods groups validation by concern (customer, items, payment)
- Returns `list[str]` of error messages — empty list means valid
- `validate()` runs all and returns combined list
- Easy to add new rules without modifying existing ones

### Decision 5: Tax config — Simple constants in `tax/` module

- UVT values, rates, and thresholds defined in `src/services/tax/config.py`
- Single source of truth for all tax-related constants
- Easy annual update

### Decision 6: `create_with_numbering()` — new method, not replacing `create()`

- `create()` remains as-is (raw Factus passthrough) for simplicity
- `create_with_numbering(data, range_id, establishment)` adds:
  1. Validation
  2. Numbering range resolution
  3. Customer/Product mapping
  4. Withholding tax calculation
  5. Pre-submit validation
- This allows callers to choose which level of automation they want

---

## Data Flow

### Invoice Creation with Full Automation

```
Caller (future MCP tool)
  │
  ├─ InvoiceService.create_with_numbering(data, range_id, establishment)
  │   │
  │   ├─ 1. Pre-validate: InvoiceValidator.validate(payload)
  │   │     └─ If errors → raise ValueError with all error messages
  │   │
  │   ├─ 2. Get next number:
  │   │     └─ NumberingRangeService.next_available(range_id)
  │   │     └─ Returns next_number (int)
  │   │
  │   ├─ 3. Map customer & products to Factus format:
  │   │     ├─ customer_dict = customer_to_factus_dict(customer, establishment)
  │   │     └─ items_dict = [product_to_factus_dict(p, ...) for p in products]
  │   │
  │   ├─ 4. Replace raw dicts with mapped dicts
  │   │
  │   ├─ 5. Build preliminary payload:
  │   │     ├─ reference_code, document, operation_type
  │   │     ├─ prefix + formatted number
  │   │     ├─ customer (mapped)
  │   │     ├─ items (mapped)
  │   │     ├─ allowance_charges (if provided)
  │   │     └─ payment_details
  │   │
  │   ├─ 6. Calculate withholdings:
  │   │     ├─ gross_total = sum(items price * quantity)
  │   │     └─ withholding_map = WithholdingTaxCalculator.calculate(
  │   │            customer=customer_dict,
  │   │            items=items_dict,
  │   │            gross_total=gross_total,
  │   │            payment_details=payment_details,
  │   │         )
  │   │     └─ Embed withholding_taxes into each item
  │   │
  │   ├─ 7. Calculate totals:
  │   │     └─ payload = _enrich_with_totals(payload)
  │   │     └─ (per-item tax calculation using item's tax rates)
  │   │
  │   ├─ 8. Send to Factus:
  │   │     └─ FactusClient.post("/v2/bills/validate", json=payload)
  │   │
  │   └─ 9. Return response dict
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/services/tax/__init__.py` | **Create** | Package marker |
| `src/services/tax/config.py` | **Create** | UVT value, thresholds, tax rates constants |
| `src/services/tax/withholding.py` | **Create** | `calculate()` — main function, `_rete_renta()`, `_rete_iva()`, `_rete_ica()`, `_rete_gmf()` |
| `src/services/mappers.py` | **Create** | `customer_to_factus_dict()`, `product_to_factus_dict()`, `_map_id_to_code()` |
| `src/services/validators.py` | **Create** | `InvoiceValidator` class with static validation methods |
| `src/services/invoice_service.py` | **Modify** | Add `create_with_numbering()`, `allowance_charges` in `_build_request()`, rewrite `_enrich_with_totals()`, add `_calculate_item_taxes()` |
| `src/schemas/dto.py` | **Modify** | Add `allowance_charges: Optional[list[dict]]` to `InvoiceCreate` |
| `src/services/__init__.py` | **Modify** | Export new modules |
| `tests/test_services/test_tax/__init__.py` | **Create** | Package marker |
| `tests/test_services/test_tax/test_withholding.py` | **Create** | Tests for all withholding scenarios |
| `tests/test_services/test_tax/test_config.py` | **Create** | Tests for UVT constants |
| `tests/test_services/test_mappers.py` | **Create** | Tests for mapper functions |
| `tests/test_services/test_validators.py` | **Create** | Tests for InvoiceValidator |
| `tests/test_services/test_invoice_service.py` | **Modify** | Add tests for `create_with_numbering()`, allowance_charges, per-item tax |

---

## Interfaces / Contracts

### `src/services/tax/config.py`

```python
UVT = Decimal("47000")
RETE_RENTA_UVT_THRESHOLD = 27
SERVICES_UVT_THRESHOLD = 4
RETE_GMF_UVT_THRESHOLD = 100

# ReteRenta rates by customer type
RETE_RENTA_RATES: dict[str, Decimal] = {
    "natural": Decimal("2.50"),     # Persona natural
    "legal": Decimal("3.50"),       # Persona jurídica
    "services": Decimal("4.00"),    # Servicios
}

# ReteIVA rates
RETE_IVA_RATE = Decimal("15.00")   # 15% on IVA portion

# ReteICA rates by municipality (for Bogotá as default)
RETE_ICA_RATES: dict[str, Decimal] = {
    "11001": Decimal("0.20"),       # Bogotá — commercial activities 0.4%, services 0.2%
}

# ReteGMF
RETE_GMF_RATE = Decimal("0.40")    # 4x1000 = 0.4%
```

### `src/services/tax/withholding.py`

```python
def calculate(
    customer: dict,
    items: list[dict],
    gross_total: Decimal,
    payment_details: list[dict] | None = None,
) -> dict[int, list[dict]]:
    """Calculate applicable withholdings per item.
    
    Returns:
        Dict mapping item_index → list of withholding dicts:
        {0: [{"code": "06", "withholding_tax_rate": "2.50", "tax_amount": "37500.00"}]}
    """
    ...

def _rete_renta_rate(customer: dict) -> Decimal | None:
    """Determine ReteRenta rate based on customer type. Returns None if not applicable."""

def _rete_iva_items(items: list[dict], customer: dict) -> dict[int, Decimal]:
    """Determine ReteIVA per item. Returns dict of item_index → amount."""

def _rete_ica_items(items: list[dict], municipality_code: str) -> dict[int, Decimal]:
    """Determine ReteICA per item. Returns dict of item_index → amount."""

def _rete_gmf_amount(payment_details: list[dict], gross_total: Decimal) -> Decimal | None:
    """Determine ReteGMF/4x1000. Returns amount or None."""

def _is_autorretenedor(customer: dict) -> bool:
    """Check if customer is Gran Contribuyente con Autorretención (tribute_code "08")."""

def _is_gran_contribuyente(customer: dict) -> bool:
    """Check if customer is Gran Contribuyente (tribute_code "22" or "08")."""
```

### `src/services/mappers.py`

```python
def customer_to_factus_dict(
    customer: Customer,
    establishment: Establishment | None = None,
) -> dict:
    """Convert Customer DB model to Factus API customer dict."""
    ...

def product_to_factus_dict(
    product: Product,
    quantity: int | Decimal | str,
    discount_rate: str = "0.00",
) -> dict:
    """Convert Product DB model to Factus API item dict."""
    ...
```

### `src/services/validators.py`

```python
class InvoiceValidator:
    @staticmethod
    def validate_customer(customer: dict) -> list[str]: ...
    
    @staticmethod
    def validate_items(items: list[dict]) -> list[str]: ...
    
    @staticmethod
    def validate_payment(payment_details: list[dict] | None) -> list[str]: ...
    
    @staticmethod
    def validate(payload: dict) -> list[str]:
        """Run all validators and return combined errors."""
        errors = []
        errors.extend(InvoiceValidator.validate_customer(payload.get("customer", {})))
        errors.extend(InvoiceValidator.validate_items(payload.get("items", [])))
        errors.extend(InvoiceValidator.validate_payment(payload.get("payment_details")))
        return errors
```

### Enhanced `InvoiceCreate` DTO

```python
class InvoiceCreate(SQLModel):
    # Existing fields...
    allowance_charges: Optional[list[dict]] = Field(default=None)
    # Each dict: {"is_surcharge": bool, "reason": str, "base_amount": str, "amount": str}
```

### Enhanced `InvoiceService`

```python
class InvoiceService:
    # Existing methods unchanged...
    
    async def create_with_numbering(
        self,
        data: InvoiceCreate,
        numbering_range_id: int,
        numbering_service: NumberingRangeService,
        establishment: Establishment | None = None,
    ) -> dict:
        """Create invoice with auto-numbering, mapping, and tax calculation."""
        ...
    
    # Modified internal methods:
    def _build_request(self, data: InvoiceCreate) -> dict:
        """Add allowance_charges to payload if present."""
        ...
    
    def _enrich_with_totals(self, payload: dict) -> dict:
        """Rewritten: per-item tax calculation using item's actual tax rates."""
        ...
    
    @staticmethod
    def _calculate_item_taxes(item: dict) -> tuple[Decimal, Decimal]:
        """Calculate gross and tax amounts for a single item.
        
        Returns:
            (gross_value, tax_amount) for the item
        """
        ...
```

---

## Testing Strategy

| Module | What to Test | Approach |
|--------|-------------|----------|
| `tax/config.py` | UVT value, thresholds | Direct assertions on constants |
| `tax/withholding.py` | 10+ scenarios: natural ≤27 UVT, natural >27 UVT, legal entity, autorretenedor, Gran Contribuyente, mixed items, excluded items, services, electronic payment, no withholdings | Pure function calls, no mocking needed |
| `mappers.py` | Customer mapping (NIT, CC), product mapping (with/without discount, excluded, unit measure codes) | Direct assertions on returned dicts |
| `validators.py` | Valid customer, missing fields, multiple errors | Direct assertions on returned error lists |
| `invoice_service.py` | `create_with_numbering()` success, range exhausted, validation errors, allowance_charges in payload, per-item tax calculation | Mock `FactusClient`, `NumberingRangeService` |

### Key Test Design

- **Withholding tests**: Use `pytest.mark.parametrize` with 10+ cases (customer data + expected withholdings)
- **Mapper tests**: Use real DB model instances with known data
- **Validator tests**: Dicts with known missing fields
- **Invoice service tests**: Inherit existing test patterns (mock FactusClient with `AsyncMock`)

---

## Migration / Rollout

No migration needed. All new modules are additive — they don't change existing behavior. Existing `create()` method remains unchanged. `create_with_numbering()` is a new method.

---

## Open Questions

1. **UVT 2026 exact value**: Estimated at 47,000 COP. Needs verification against official DIAN resolution for 2026.
2. **ReteICA rates per municipality**: Currently only Bogotá. Should be configurable per establishment.
3. **Should services auto-detect item type (goods vs services)?**: Currently the mapper doesn't distinguish. May need a `Product.type` field.
