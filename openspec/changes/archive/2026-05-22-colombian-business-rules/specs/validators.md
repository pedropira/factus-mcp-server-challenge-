# Spec: InvoiceValidator

## Purpose

Pre-submit validation of DIAN requirements before sending payloads to the Factus API. Catches missing or invalid fields early, providing clear error messages.

---

### Requirement: VALIDATE_CUSTOMER

The system MUST provide `InvoiceValidator.validate_customer(customer: dict) -> list[str]` that checks required customer fields for Factus API compliance.

#### Scenario: Customer with all required fields

- GIVEN a customer dict with: `identification_document_code`, `identification`, `names` or `company`, `email`, `address`, `municipality_code`, `legal_organization_code`, `tribute_code`
- WHEN `validate_customer()` is called
- THEN the result MUST be an empty list (no errors)

#### Scenario: Customer missing identification

- GIVEN a customer dict without `identification`
- WHEN `validate_customer()` is called
- THEN the result MUST include `"Customer missing required field: identification"`

#### Scenario: Customer missing both names and company

- GIVEN a customer dict with neither `names` nor `company`
- WHEN `validate_customer()` is called
- THEN the result MUST include an error indicating at least one of names/company is required

#### Scenario: Customer missing email

- GIVEN a customer dict without `email`
- WHEN `validate_customer()` is called
- THEN the result MUST include `"Customer missing required field: email"`
- NOTE: Even though Factus might accept it, DIAN requires email for electronic invoice delivery

---

### Requirement: VALIDATE_ITEMS

The system MUST provide `InvoiceValidator.validate_items(items: list[dict]) -> list[str]` that checks required item fields.

#### Scenario: All items valid

- GIVEN a list of items, each with: `code_reference`, `name`, `quantity`, `price`, `unit_measure_code`, `standard_code`, `taxes`
- WHEN `validate_items()` is called
- THEN the result MUST be an empty list

#### Scenario: Item missing code_reference

- GIVEN an item without `code_reference`
- WHEN `validate_items()` is called
- THEN the result MUST include `"Item [index] missing required field: code_reference"`

#### Scenario: Item with negative price

- GIVEN an item with `price` = "-1000"
- WHEN `validate_items()` is called
- THEN the result MUST include `"Item [index] has negative price"`

#### Scenario: Item with zero quantity

- GIVEN an item with `quantity` = "0" or "0.00"
- WHEN `validate_items()` is called
- THEN the result MUST include `"Item [index] must have quantity greater than 0"`

---

### Requirement: VALIDATE_PAYMENT

The system MUST provide `InvoiceValidator.validate_payment(payment_details: list[dict]) -> list[str]` that checks payment details.

#### Scenario: Valid payment details

- GIVEN payment_details with at least one entry containing `payment_form`, `payment_method_code`, `amount`
- WHEN `validate_payment()` is called
- THEN the result MUST be an empty list

#### Scenario: Empty payment details

- GIVEN payment_details is `None` or empty list
- WHEN `validate_payment()` is called
- THEN the result MUST include `"At least one payment detail is required"`

---

### Requirement: VALIDATE_INVOICE

The system MUST provide `InvoiceValidator.validate(payload: dict) -> list[str]` that runs ALL validators and returns a combined list of errors.

#### Scenario: Valid invoice — no errors

- GIVEN a fully constructed payload dict with valid customer, items, and payment_details
- WHEN `validate()` is called
- THEN the result MUST be an empty list

#### Scenario: Multiple validation errors

- GIVEN a payload missing customer identification AND one item missing code_reference
- WHEN `validate()` is called
- THEN the result MUST include BOTH errors
- AND the list has length 2

#### Scenario: No errors — returns empty list

- GIVEN a valid payload
- WHEN `validate()` is called
- THEN the result MUST be an empty list
