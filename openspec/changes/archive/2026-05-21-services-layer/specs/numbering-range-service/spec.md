# Numbering Range Service Specification

## Purpose

Define the service layer behavior for DIAN numbering ranges: CRUD plus automatic assignment of the next available invoice number within a range.

## Requirements

### Requirement: RANGE_CREATE

The system MUST provide `NumberingRangeService.create(data)` to register a new DIAN authorized range.

### Requirement: RANGE_GET_ACTIVE

The system MUST provide `NumberingRangeService.get_active(document_type_id)` that returns all active ranges, optionally filtered by document type.

### Requirement: RANGE_NEXT_AVAILABLE

The system MUST provide `NumberingRangeService.next_available(range_id)` that computes the next invoice number for the given range.

#### Scenario: First invoice in range

- GIVEN a range with `from_number=1`, `to_number=5000`, and no invoices using it
- WHEN `NumberingRangeService.next_available(1)` is called
- THEN the result MUST be `1`

#### Scenario: Next after existing invoices

- GIVEN a range with `from_number=1`, `to_number=5000`, and invoices numbered 1, 2, 3 already exist
- WHEN `NumberingRangeService.next_available(1)` is called
- THEN the result MUST be `4`

#### Scenario: Range exhausted

- GIVEN a range with `from_number=1`, `to_number=3`, and 3 invoices already exist
- WHEN `NumberingRangeService.next_available(1)` is called
- THEN the system MUST raise a `ValueError("Numbering range exhausted")`

#### Scenario: Range not found

- GIVEN no range with `id=999` exists
- WHEN `NumberingRangeService.next_available(999)` is called
- THEN the system MUST raise a `ValueError("Numbering range not found")`

### Requirement: RANGE_UPDATE

The system MUST provide `NumberingRangeService.update(id, data)` for updating range properties.

### Requirement: RANGE_GET_DEFAULT

The system MUST provide `NumberingRangeService.get_default_for_document_type(document_type_id)` returning the first active range for that document type.
