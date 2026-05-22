# Spec: WithholdingTaxCalculator

## Purpose

Auto-calculate Colombian withholding taxes (ReteRenta, ReteIVA, ReteICA, ReteFUENTE, ReteGMF) based on customer type, product type, and amounts, following DIAN regulations.

## Requirements

### Requirement: WITHHOLDING_CALCULATE

The system MUST provide `WithholdingTaxCalculator.calculate(customer: dict, items: list[dict], gross_total: Decimal) -> list[dict]` that returns a list of withholding tax dicts in Factus API format.

**Output format**: Each dict MUST have `{"code": str, "withholding_tax_rate": str, "tax_amount": str}` matching what Factus API expects inside `items[].withholding_taxes[]`.

---

### Scenario: Natural person under 27 UVT — no ReteRenta

- GIVEN a customer with `tribute_code` = "ZZ" (no special regime) and `legal_organization_code` = "2" (persona natural)
- AND item total gross value is 500,000 COP (below 27 UVT ≈ 1,269,000 COP)
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST NOT include any ReteRenta (code "06")

---

### Scenario: Natural person over 27 UVT — ReteRenta 2.5%

- GIVEN a customer with `tribute_code` = "ZZ" and `legal_organization_code` = "2" (persona natural)
- AND item total gross value is 1,500,000 COP (above 27 UVT)
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST include ReteRenta (code "06") with `withholding_tax_rate` = "2.50"
- AND `tax_amount` MUST equal 1,500,000 * 0.025 = 37,500 COP

---

### Scenario: Legal entity over 27 UVT — ReteRenta 3.5%

- GIVEN a customer with `tribute_code` = "ZZ" and `legal_organization_code` = "1" (persona jurídica)
- AND item total gross value is 2,000,000 COP (above 27 UVT)
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST include ReteRenta (code "06") with `withholding_tax_rate` = "3.50"
- AND `tax_amount` MUST equal 2,000,000 * 0.035 = 70,000 COP

---

### Scenario: Gran Contribuyente con Autorretención — NO ReteRenta

- GIVEN a customer with `tribute_code` = "08" (Gran Contribuyente con Autorretención)
- AND item total gross value is 10,000,000 COP (well above 27 UVT)
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST NOT include ReteRenta (the customer self-withholds)

---

### Scenario: Gran Contribuyente — ReteIVA on items with IVA

- GIVEN a customer with `tribute_code` = "22" (Gran Contribuyente) or "08" (Autorretenedor)
- AND items include products with `tax_rate` = "19.00" (subject to IVA)
- AND each taxed item has a non-0 `price`
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST include ReteIVA (code "05") for each item subject to IVA
- AND the `tax_amount` for ReteIVA MUST be: item_IVA_amount * 0.15
- WHERE `item_IVA_amount = price * quantity * (19/119)` (IVA is included in price)

---

### Scenario: Items marked as excluded — no withholding taxes

- GIVEN items where `is_excluded` = True
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result for those items MUST NOT include ReteRenta or ReteIVA
- AND the item still contributes to gross total for threshold calculations

---

### Scenario: Services — ReteICA at municipal rate

- GIVEN a customer and the invoice includes service-type items
- AND the establishment municipality is Bogotá (code "11001")
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result SHOULD include ReteICA (code "07") for service items
- AND the rate SHOULD be "0.20" (0.2% for services in Bogotá)
- AND `tax_amount` = item_gross_value * 0.002

---

### Scenario: Payment via financial system over 100 UVT — ReteGMF

- GIVEN payment details with `payment_method_code` = "47" (transferencia) or "42" (consignación)
- AND total amount > 100 UVT (≈ 4,700,000 COP)
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST include ReteGMF (code "20") with `withholding_tax_rate` = "0.40"
- AND `tax_amount` = total_amount * 0.004

---

### Scenario: No applicable withholdings — empty list

- GIVEN a customer with `tribute_code` = "ZZ" (no special regime)
- AND item total gross value is 100,000 COP (below all thresholds)
- AND no electronic payment method
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST be an empty list

---

### Scenario: Multiple applicable withholdings — all returned

- GIVEN a customer with `tribute_code` = "22" (Gran Contribuyente)
- AND items with IVA 19%, total gross 10,000,000 COP
- AND payment via transferencia (code "47")
- WHEN `WithholdingTaxCalculator.calculate()` is called
- THEN the result MUST include ReteIVA (05) AND ReteGMF (20)
- AND ReteRenta MUST NOT be present (Gran Contribuyente self-withholds)

---

### Requirement: WITHHOLDING_UVT_CONFIG

The system MUST define UVT value and thresholds as a constant configuration that can be updated yearly.

- `UVT` = Decimal("47000") (estimated 2026 value)
- `RETE_RENTA_UVT_THRESHOLD` = 27
- `RETE_GMF_UVT_THRESHOLD` = 100
- `SERVICES_UVT_THRESHOLD` = 4
