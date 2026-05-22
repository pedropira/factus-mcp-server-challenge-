# Establishment Service Specification

## Purpose

Define the service layer behavior for establishment (issuer branch) management.

## Requirements

### Requirement: ESTABLISHMENT_CREATE

The system MUST provide `EstablishmentService.create(data)` that validates and creates an establishment, returning it with generated `id`.

#### Scenario: Create establishment successfully

- GIVEN valid `EstablishmentCreate` data
- WHEN `EstablishmentService.create()` is called
- THEN a new `Establishment` is persisted and returned

### Requirement: ESTABLISHMENT_GET_BY_ID

The system MUST provide `EstablishmentService.get_by_id(id)` returning the establishment or `None`.

#### Scenario: Get existing establishment

- GIVEN an establishment with `id=1` exists
- WHEN `EstablishmentService.get_by_id(1)` is called
- THEN the establishment is returned

### Requirement: ESTABLISHMENT_GET_BY_NAME

The system MUST provide `EstablishmentService.get_by_name(name)` that delegates to `EstablishmentRepository.get_by_name()`.

#### Scenario: Find by name

- GIVEN an establishment named "Sucursal Norte" exists
- WHEN `EstablishmentService.get_by_name("Sucursal Norte")` is called
- THEN the establishment is returned

### Requirement: ESTABLISHMENT_UPDATE

The system MUST provide `EstablishmentService.update(id, data)` that updates and returns the establishment, raising `ValueError` if not found.

### Requirement: ESTABLISHMENT_DELETE

The system MUST provide `EstablishmentService.delete(id)` that removes the establishment, raising `ValueError` if not found.

### Requirement: ESTABLISHMENT_LIST

The system MUST provide `EstablishmentService.list(offset, limit)` returning paginated establishments sorted by name.
