---
name: sqlmodel-async
description: >
  Async SQLModel patterns for SQLAlchemy with async engines, JSON columns, repository pattern, and session management.
  Trigger: When working with SQLModel models, async database sessions, repositories with AsyncSession, or defining SQLModel tables with JSON columns.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Defining SQLModel table models with `table=True`
- Using JSON columns to store nested data (`sa_type=JSON`)
- Creating async engines and session factories with `sqlite+aiosqlite://`
- Implementing the repository pattern with `AsyncSession`
- Writing async database queries with `session.exec()`
- Managing relationships between SQLModel tables

## Critical Patterns

### 1. Model Definition with JSON Columns

Use `sa_type=JSON` on `Field()` for nested data that matches external API responses. This avoids creating separate tables for deeply nested structures.

```python
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime

class Invoice(SQLModel, table=True):
    __tablename__ = "invoices"

    id: Optional[int] = Field(default=None, primary_key=True)
    reference_code: str = Field(max_length=100)
    order_reference: Optional[dict] = Field(default=None, sa_type=JSON)
    billing_period: Optional[dict] = Field(default=None, sa_type=JSON)
    errors: Optional[list] = Field(default=None, sa_type=JSON)
```

### 2. Foreign Keys and Relationships

Always use `Optional[int]` for nullable FKs. The column name is `{related_table}_id`.

```python
class Invoice(SQLModel, table=True):
    ...
    customer_id: int = Field(foreign_key="customers.id")
    establishment_id: Optional[int] = Field(default=None, foreign_key="establishments.id")
    numbering_range_id: int = Field(foreign_key="numbering_ranges.id")

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: Optional[int] = Field(default=None, primary_key=True)
    identification: str = Field(max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
```

### 3. Async Engine and Session

Create engine as a singleton. Use `create_async_engine` from `sqlalchemy.ext.asyncio`, NOT from SQLModel directly.

```python
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

_engine: Optional[AsyncEngine] = None

def get_engine(database_url: str) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(database_url, echo=False)
    return _engine
```

### 4. Table Creation on Startup

Use `SQLModel.metadata.create_all` with `conn.run_sync()`. Import models BEFORE calling create_all so they register in metadata.

```python
from sqlmodel import SQLModel

async def create_db_and_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        from src.schemas import models  # noqa: F401 — registers models in metadata
        await conn.run_sync(SQLModel.metadata.create_all)
```

### 5. AsyncSession for Repositories

Inject `AsyncSession` into repositories via constructor. Never pass engine to repositories.

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

class BaseRepository:
    def __init__(self, session: AsyncSession, model_class: type) -> None:
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: int):
        return await self.session.get(self.model_class, id)

    async def list_all(self):
        result = await self.session.exec(select(self.model_class))
        return result.all()

    async def add(self, instance):
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
```

### 6. get_or_create Pattern

Check existence first, return existing or create new. Useful for syncing external API data to local DB.

```python
async def get_or_create_customer(self, identification: str, defaults: dict) -> Customer:
    stmt = select(Customer).where(Customer.identification == identification)
    result = await self.session.exec(stmt)
    customer = result.first()
    if customer:
        return customer, False
    customer = Customer(identification=identification, **defaults)
    self.session.add(customer)
    await self.session.commit()
    await self.session.refresh(customer)
    return customer, True
```

### 7. Search with Text Matching

Use `ilike` for case-insensitive search. Avoid raw SQL for simple filters.

```python
from sqlmodel import select, or_

async def search_customers(self, text: str) -> list[Customer]:
    pattern = f"%{text}%"
    stmt = select(Customer).where(
        or_(
            Customer.identification.ilike(pattern),
            Customer.company.ilike(pattern),
            Customer.names.ilike(pattern),
            Customer.email.ilike(pattern),
        )
    )
    result = await self.session.exec(stmt)
    return result.all()
```

### 8. Session Context Manager

Provide a reusable async context manager for direct session usage outside DI.

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

@asynccontextmanager
async def get_async_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
```

## Commands

```bash
# Install with aiosqlite support
pip install "sqlmodel[aiosqlite]"

# Install with asyncpg for PostgreSQL
pip install "sqlmodel[asyncpg]"
```

## Critical Warnings

- `SQLModel.metadata.create_all` works with async engines via `conn.run_sync()`, NOT directly
- Always import model modules before calling `create_all` — otherwise tables won't be created
- `sa_type=JSON` requires `from sqlalchemy import Column, JSON` (not from SQLModel)
- `session.exec()` is SQLModel's async wrapper around `session.execute()`
- `session.get()` works directly with primary key for async sessions
- Do NOT use `sessionmaker` with SQLModel — use `AsyncSession(engine)` directly
