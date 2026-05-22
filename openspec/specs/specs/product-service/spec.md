# Product Service Specification

## Purpose

Define the service layer behavior for the product catalog: a new `products` table with CRUD operations for managing reference codes, prices, and tax configuration.

## Requirements

### Requirement: PRODUCT_TABLE_EXISTS

The system MUST include a `Product` SQLModel table with `__tablename__ = "products"` registered in `SQLModel.metadata` so `create_db_and_tables()` creates it.

#### Scenario: Table created at startup

- GIVEN the application starts and calls `create_db_and_tables()`
- THEN a `products` table MUST exist in the database

### Requirement: PRODUCT_CREATE

The system MUST provide `ProductService.create(data)` that creates a product with unique `code_reference`.

#### Scenario: Create product successfully

- GIVEN valid `ProductCreate` data
- WHEN `ProductService.create()` is called
- THEN a new `Product` is persisted via `ProductRepository.create()`
- AND the created product with generated `id` is returned

#### Scenario: Duplicate code_reference

- GIVEN a product with `code_reference="PROD-001"` already exists
- WHEN `ProductService.create()` is called with the same code
- THEN the system MUST raise an integrity error

### Requirement: PRODUCT_GET_BY_ID

The system MUST provide `ProductService.get_by_id(id)` returning the product or `None`.

### Requirement: PRODUCT_GET_BY_CODE

The system MUST provide `ProductService.get_by_code(code_reference)` returning the product or `None`.

#### Scenario: Find by code

- GIVEN a product with `code_reference="PROD-001"` exists
- WHEN `ProductService.get_by_code("PROD-001")` is called
- THEN the product is returned

### Requirement: PRODUCT_SEARCH

The system MUST provide `ProductService.search(query, limit)` that searches products by name or code reference.

### Requirement: PRODUCT_UPDATE

The system MUST provide `ProductService.update(id, data)` that updates and returns the product, raising `ValueError` if not found.

### Requirement: PRODUCT_DELETE

The system MUST provide `ProductService.delete(id)` that removes the product, raising `ValueError` if not found.
