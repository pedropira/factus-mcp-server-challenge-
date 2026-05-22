# Tasks: Service Layer

## Phase 1: Foundation (Product table + DTOs + Service base)

- [ ] 1.1 Add `Product` model to `src/schemas/models.py` (code_reference, name, price, tax_rate, unit_measure_id, standard_code_id, tribute_id)
- [ ] 1.2 Create `ProductRepository` in `src/infrastructure/repositories/product_repository.py` (extend BaseRepository[Product], add `get_by_code()`, `search()`)
- [ ] 1.3 Update `src/schemas/__init__.py` to export `Product`
- [ ] 1.4 Update `src/infrastructure/repositories/__init__.py` to export `ProductRepository`
- [ ] 1.5 Create `src/schemas/dto.py` with input DTOs: `CustomerCreate`, `CustomerUpdate`, `EstablishmentCreate`, `EstablishmentUpdate`, `NumberingRangeCreate`, `NumberingRangeUpdate`, `ProductCreate`, `ProductUpdate`, `InvoiceItemCreate`, `InvoiceCreate`

## Phase 2: Entity Services (Customer, Establishment, NumberingRange, Product)

- [ ] 2.1 Create `src/services/__init__.py` re-exporting all services
- [ ] 2.2 Create `src/services/customer_service.py` — `CustomerService` with: create, get_by_id, search, update, delete
- [ ] 2.3 Create `src/services/establishment_service.py` — `EstablishmentService` with: create, get_by_id, get_by_name, list, update, delete
- [ ] 2.4 Create `src/services/numbering_range_service.py` — `NumberingRangeService` with: create, get_active, get_default_for_document_type, next_available (computes next number from invoices table), update, delete
- [ ] 2.5 Create `src/services/product_service.py` — `ProductService` with: create, get_by_id, get_by_code, search, update, delete

## Phase 3: Invoice Service (Factus orchestration)

- [ ] 3.1 Create `src/services/invoice_service.py` — `InvoiceService.__init__` receives `AsyncSession` + `FactusClient`, wires up InvoiceRepository + CustomerRepository + NumberingRangeRepository + InvoiceItemRepository
- [ ] 3.2 Implement `InvoiceService.create()`: validate customer → get default range → next available number → build Factus payload → `FactusClient.post("/v1/bills/ebills")` → persist Invoice + Items → return
- [ ] 3.3 Implement `InvoiceService.get_by_reference_code()`, `list_by_status()`, `get_pending_sync()`

## Phase 4: Tests

- [ ] 4.1 Create `tests/test_services/__init__.py`
- [ ] 4.2 Write `tests/test_services/test_customer_service.py` — test create, get_by_id, search, update, delete (mock `CustomerRepository`)
- [ ] 4.3 Write `tests/test_services/test_product_service.py` — test create, get_by_code, search, delete (mock `ProductRepository`)
- [ ] 4.4 Write `tests/test_services/test_numbering_range_service.py` — test next_available (first, next, exhausted, not found), get_active, get_default
- [ ] 4.5 Write `tests/test_services/test_invoice_service.py` — test create (success with mocked FactusClient.post, customer not found, range exhausted, API error)
