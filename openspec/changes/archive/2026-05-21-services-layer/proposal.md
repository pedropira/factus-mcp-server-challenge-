# Proposal: Service Layer

## Intent

Create the service layer (`src/services/`) containing the business logic layer between repositories and future MCP tools. Each service orchestrates CRUD operations on entities and Factus API calls for electronic documents.

## Scope

### In Scope
- `CustomerService` — CRUD + customer search
- `EstablishmentService` — CRUD for establishments
- `NumberingRangeService` — CRUD for numbering ranges + auto-assignment of next available number
- `InvoiceService` — Invoice creation (payload assembly + Factus API submission + persistence), lookup by reference code, listing by status, pending sync
- `ProductService` — CRUD for product catalog — new `products` table
- Unit tests for each service
- Input/Output DTOs (Create, Update, Query) using Pydantic/SQLModel

### Out of Scope
- MCP tool implementation (separate change)
- Real sandbox connection to Factus (services consume `FactusClient` which can be mocked)
- Credit notes, debit notes, support documents (future changes)
- Reports or exports

## Capabilities

### New Capabilities
- `customer-service`: Customer CRUD with search by identification, email, name
- `establishment-service`: Establishment CRUD
- `numbering-range-service`: Numbering range CRUD + automatic next available number assignment
- `invoice-service`: Electronic invoice creation, query and sync with the Factus API
- `product-service`: Product catalog CRUD (reference codes, prices, taxes)

### Modified Capabilities
None

## Approach

1. **Input DTOs**: define `CustomerCreate`, `CustomerUpdate`, `InvoiceCreate`, etc. as Pydantic models in `src/schemas/dto.py`.
2. **Service Base**: abstract class or protocol with `AsyncSession` injection.
3. **Entity services** (Customer, Establishment, NumberingRange, Product): direct CRUD + specific query methods. Each receives `AsyncSession`.
4. **InvoiceService**: receives `AsyncSession` + `FactusClient`. Orchestrates: validate customer, find active range, compute next number, build Factus-compliant payload, POST to Factus, persist response.
5. **Each service defines its own async methods** — repositories already exist, services consume them.
6. **Tests**: each service with fixtures that mock repositories and FactusClient using `unittest.mock` or `MockTransport`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/services/` | New | Full service directory |
| `src/schemas/dto.py` | New | Input/output DTOs for services |
| `src/schemas/models.py` | Modified | New `Product` table |
| `src/infrastructure/repositories/product_repository.py` | New | Repository for Product |
| `tests/test_services/` | New | Unit tests per service |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Service-FactusClient coupling | Medium | FactusClient injected via constructor, easy to mock |
| Factus payload format changes | Low | Mapping centralized in one service method |
| DB/API transaction inconsistency | Medium | If Factus accepts but DB fails, invoice is inconsistent. Use "save pending first, send later" pattern |

## Rollback Plan

Delete `src/services/`, `src/schemas/dto.py`, revert `src/schemas/models.py`, delete `tests/test_services/`.

## Dependencies

- Existing repositories in `src/infrastructure/repositories/`
- `FactusClient` in `src/infrastructure/factus_client.py`
- `SQLModel` for the new `Product` table

## Success Criteria

- [ ] All services implemented with their DTOs
- [ ] Unit tests passing (at least one test per public method on each service)
- [ ] `InvoiceService.create_invoice()` builds correct Factus payload and calls `FactusClient.post()`
- [ ] `products` table created with `ProductRepository`
- [ ] `create_db_and_tables()` includes the new table
