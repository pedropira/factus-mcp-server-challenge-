# Spec: FactusPayloadMapper

## Purpose

Provide helper functions to convert local DB models (Customer, Product, Establishment) into the dict format expected by the Factus API v2.

---

### Requirement: MAPPER_CUSTOMER_TO_FACTUS

The system MUST provide `customer_to_factus_dict(customer: Customer, establishment: Establishment) -> dict` that maps a Customer DB model to a Factus API customer dict.

#### Scenario: Full customer mapping

- GIVEN a `Customer` with:
  - `identification` = "222222222222"
  - `dv` = "6"
  - `company` = "Empresa SAS"
  - `names` = None
  - `email` = "contacto@empresa.com"
  - `phone` = "3001234567"
  - `address` = "Calle 123 # 45-67"
  - `municipality_id` = "11001"
  - `identification_document_id` = 6 (NIT)
  - Plus a tribute_id that maps to "ZZ" and legal_organization_id that maps to "1"
- WHEN `customer_to_factus_dict(customer, establishment)` is called
- THEN the returned dict MUST contain:
  ```python
  {
    "identification_document_code": "31",   # DIAN code for NIT
    "identification": "222222222222",
    "dv": "6",
    "company": "Empresa SAS",
    "names": None,
    "address": "Calle 123 # 45-67",
    "email": "contacto@empresa.com",
    "phone": "3001234567",
    "legal_organization_code": "1",         # mapped from legal_organization_id
    "tribute_code": "ZZ",                   # mapped from tribute_id
    "municipality_code": "11001",           # mapped from municipality_id
  }
  ```

#### Scenario: Customer with names instead of company

- GIVEN a Customer with `company` = None and `names` = "Juan Pérez"
- WHEN `customer_to_factus_dict()` is called
- THEN the returned dict has `names` = "Juan Pérez" and `company` = None
- AND the dict is valid for Factus API (one of company/names is required)

#### Scenario: Customer identification document ID → DIAN code

- GIVEN `Customer.identification_document_id` = 3 (Factus ID for cédula de ciudadanía)
- WHEN `customer_to_factus_dict()` is called
- THEN the returned dict has `identification_document_code` = "13" (DIAN code)
- AND NOT `identification_document_id` = 3 (Factus uses DIAN codes, not Factus IDs)

---

### Requirement: MAPPER_PRODUCT_TO_FACTUS

The system MUST provide `product_to_factus_dict(product: Product, quantity: int | Decimal, discount_rate: str = "0.00") -> dict` that maps a Product DB model to a Factus API item dict.

#### Scenario: Full product mapping

- GIVEN a `Product` with:
  - `code_reference` = "PROD-001"
  - `name` = "Laptop Pro"
  - `price` = Decimal("2500000.00")
  - `tax_rate` = "19.00"
  - `unit_measure_id` = 70 (unidad)
  - `standard_code_id` = 1 (estándar contribuyente)
  - `tribute_id` = 1 (IVA)
  - `is_excluded` = False
- AND quantity = 2
- WHEN `product_to_factus_dict(product, quantity)` is called
- THEN the returned dict MUST contain:
  ```python
  {
    "code_reference": "PROD-001",
    "name": "Laptop Pro",
    "quantity": "2.00",
    "price": "2500000.00",
    "discount_rate": "0.00",
    "unit_measure_code": "94",          # mapped from unit_measure_id
    "standard_code": "1",               # mapped from standard_code_id
    "taxes": [{"code": "01", "rate": "19.00"}],  # mapped from tax_rate + tribute_id
    "total_discount": "0.00",
  }
  ```

#### Scenario: Product with discount

- GIVEN a `Product` with `price` = "50000.00" and quantity = 1
- AND `discount_rate` = "10.00"
- WHEN `product_to_factus_dict(product, 1, "10.00")` is called
- THEN the returned dict has `discount_rate` = "10.00"
- AND `total_discount` = "5000.00" (50,000 * 0.10)

#### Scenario: Product excluded from IVA

- GIVEN a `Product` with `is_excluded` = True and `tax_rate` = "0.00"
- WHEN `product_to_factus_dict()` is called
- THEN the returned dict has `taxes` = `[{"code": "01", "rate": "0.00"}]`

#### Scenario: Product unit_measure_id → DIAN code mapping

- GIVEN `Product.unit_measure_id` = 70 (Factus ID for "unidad")
- WHEN `product_to_factus_dict()` is called
- THEN the returned dict has `unit_measure_code` = "94" (DIAN code for "unidad")
- AND NOT `unit_measure_id` = 70
