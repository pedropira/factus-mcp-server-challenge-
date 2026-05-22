# Design: Service Layer

## Technical Approach

Single-responsibility services consuming existing repositories and `FactusClient`. Each service is a plain class with `AsyncSession` injected via constructor. `InvoiceService` additionally receives `FactusClient` (already opened). DTOs live in `src/schemas/dto.py` as Pydantic models for input validation.

Entity services (Customer, Establishment, NumberingRange, Product) follow a uniform CRUD pattern. InvoiceService is the orchestrator — it coordinates multiple repositories, builds Factus-compliant payloads, and handles the send-and-persist flow.

---

## Architecture Decisions

### Decision: Service Pattern

| Option | Tradeoff | Decision |
|--------|----------|----------|
| One service per entity | More files, clearer boundaries | ✅ **Chosen** — matches repo pattern, each has distinct methods |
| Single big service class | Fewer files, harder to test | ❌ Rejected |
| BaseService with generics | Could work but entity-specific methods don't fit | ❌ Rejected — too abstract for this layer |

### Decision: DTO Location

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `src/schemas/dto.py` | Single file, all DTOs together, clean imports | ✅ **Chosen** — keeps schemas/ as the data contract layer |
| DTOs inside services/ | Closer to usage, but scattered | ❌ Rejected — harder to find and import |
| Reuse SQLModel models as DTOs | Less code, but models have DB-only fields | ❌ Rejected — input DTOs differ from DB models |

### Decision: InvoiceService + FactusClient

`FactusClient` is a context manager. `InvoiceService` will receive it pre-opened. The caller (future MCP tool) is responsible for the `async with FactusClient(...) as client:` lifecycle.

```
Caller (MCP tool) ──→ opens FactusClient ──→ passes to InvoiceService ──→ service calls client.post()
```

### Decision: Numbering — Next Available Number

`NumberingRangeService.next_available(range_id)` reads the current range and the last used number from the invoices table, returning the next consecutive. If none used yet, returns `from_number`. If `to_number` reached, raises an error.

---

## Data Flow

### Invoice Creation Flow

```
MCP Tool
  │
  ├─ InvoiceService.create_invoice(data)
  │   │
  │   ├─ CustomerRepository.get_by_id(customer_id)
  │   ├─ NumberingRangeRepository.get_default_for_document_type(...)
  │   ├─ NumberingRangeService.next_available(range_id)
  │   │
  │   ├─ Build Factus payload (map DTO → Factus JSON format)
  │   │
  │   ├─ FactusClient.post("/api/invoices", json=payload)
  │   │   └─ Returns { number, cufe, status, total, ... }
  │   │
  │   └─ InvoiceRepository.create(invoice)
  │       └─ Persist Invoice + InvoiceItems + AllowanceCharges
  │
  └─ Returns Invoice (with cufe, number, status)
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/schemas/dto.py` | Create | Pydantic input DTOs: `CustomerCreate`, `CustomerUpdate`, `InvoiceCreate`, `InvoiceItemCreate`, `ProductCreate`, `ProductUpdate` |
| `src/schemas/models.py` | Modify | Add `Product` table |
| `src/services/__init__.py` | Create | Re-export all services |
| `src/services/customer_service.py` | Create | Customer CRUD + search |
| `src/services/establishment_service.py` | Create | Establishment CRUD |
| `src/services/numbering_range_service.py` | Create | Numbering range CRUD + `next_available()` |
| `src/services/invoice_service.py` | Create | Invoice orchestration: create, get, list, sync |
| `src/services/product_service.py` | Create | Product CRUD (new table) |
| `src/infrastructure/repositories/product_repository.py` | Create | Repository for Product |
| `tests/test_services/__init__.py` | Create | Package marker |
| `tests/test_services/test_customer_service.py` | Create | Tests for CustomerService |
| `tests/test_services/test_invoice_service.py` | Create | Tests for InvoiceService (with mocked FactusClient) |
| `tests/test_services/test_product_service.py` | Create | Tests for ProductService |

---

## Interfaces / Contracts

### DTO Pattern (`src/schemas/dto.py`)

```python
class CustomerCreate(SQLModel):
    identification_document_id: int
    identification: str
    dv: str | None = None
    company: str | None = None
    names: str | None = None
    email: str | None = None
    phone: str | None = None
    municipality_id: str | None = None

class InvoiceItemCreate(SQLModel):
    code_reference: str
    name: str
    quantity: int
    price: Decimal
    tax_rate: str          # "19.00", "0.00"
    unit_measure_id: int
    standard_code_id: int
    tribute_id: int

class InvoiceCreate(SQLModel):
    numbering_range_id: int
    customer_id: int
    reference_code: str
    items: list[InvoiceItemCreate]
    payment_form: str = "1"
    payment_method_code: str = "10"
    notes: str | None = None
```

### Service Pattern

```python
class CustomerService:
    def __init__(self, session: AsyncSession):
        self.repo = CustomerRepository(session)

    async def create(self, data: CustomerCreate) -> Customer: ...
    async def get_by_id(self, id: int) -> Customer | None: ...
    async def update(self, id: int, data: CustomerUpdate) -> Customer: ...
    async def delete(self, id: int) -> None: ...
    async def search(self, query: str, limit: int = 20) -> list[Customer]: ...

class InvoiceService:
    def __init__(self, session: AsyncSession, factus: FactusClient):
        self.session = session
        self.factus = factus
        self.invoice_repo = InvoiceRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.range_repo = NumberingRangeRepository(session)
        self.item_repo = InvoiceItemRepository(session)

    async def create(self, data: InvoiceCreate) -> Invoice: ...
    async def get_by_reference_code(self, code: str) -> Invoice | None: ...
    async def list_by_status(self, status: int) -> list[Invoice]: ...
    async def get_pending_sync(self) -> list[Invoice]: ...
```

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | CustomerService CRUD | Mock `CustomerRepository`, verify correct calls |
| Unit | InvoiceService.create | Mock all repos + `FactusClient.post()`, verify payload structure |
| Unit | NumberingRangeService.next_available | Mock range repo + invoice count query |
| Unit | ProductService CRUD | Mock `ProductRepository` |

All tests use `pytest-asyncio` with `AsyncMock` for repositories and `MockTransport` for FactusClient.

---

## Migration / Rollout

No migration required. New `products` table is auto-created by `create_db_and_tables()`. Existing data unaffected.

---

## Open Questions

None.
