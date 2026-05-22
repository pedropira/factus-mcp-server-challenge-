# Customer Service Specification

## Purpose

Define the service layer behavior for customer (purchaser) management: CRUD and search operations consumed by MCP tools.

## Requirements

### Requirement: CUSTOMER_CREATE

The system MUST provide a `CustomerService.create()` method that accepts a `CustomerCreate` DTO, creates a `Customer` entity via `CustomerRepository.create()`, and returns the created customer.

#### Scenario: Create customer successfully

- GIVEN valid `CustomerCreate` data with all required fields
- WHEN `CustomerService.create()` is called
- THEN a new `Customer` is persisted via `CustomerRepository.create()`
- AND the created `Customer` with its generated `id` is returned

#### Scenario: Create customer with duplicate identification

- GIVEN a customer with `identification` "12345" already exists
- WHEN `CustomerService.create()` is called with `identification` "12345"
- THEN the system MUST raise a `ValueError` or integrity error

### Requirement: CUSTOMER_GET_BY_ID

The system MUST provide `CustomerService.get_by_id(id)` returning the customer or `None`.

#### Scenario: Get existing customer

- GIVEN a customer with `id=1` exists
- WHEN `CustomerService.get_by_id(1)` is called
- THEN the customer is returned

#### Scenario: Get non-existent customer

- GIVEN no customer with `id=999` exists
- WHEN `CustomerService.get_by_id(999)` is called
- THEN `None` is returned

### Requirement: CUSTOMER_SEARCH

The system MUST provide `CustomerService.search(query, limit)` that searches by identification, name, company, or email using `CustomerRepository.search()`.

#### Scenario: Search finds matches

- GIVEN customers "Juan Pérez" and "María Pérez" exist
- WHEN `CustomerService.search("Pérez")` is called
- THEN both customers are returned

#### Scenario: Search returns empty

- GIVEN no customers match "NoExiste"
- WHEN `CustomerService.search("NoExiste")` is called
- THEN an empty list is returned

### Requirement: CUSTOMER_UPDATE

The system MUST provide `CustomerService.update(id, data)` that updates and returns the customer, raising `ValueError` if not found.

### Requirement: CUSTOMER_DELETE

The system MUST provide `CustomerService.delete(id)` that removes the customer, raising `ValueError` if not found.
