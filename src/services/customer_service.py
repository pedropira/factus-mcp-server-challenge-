"""
CustomerService — CRUD + search for customers (purchasers).
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories import CustomerRepository
from src.schemas.dto import CustomerCreate, CustomerUpdate
from src.schemas.models import Customer


class CustomerService:
    """Business logic for customer/purchaser management."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = CustomerRepository(session)

    async def create(self, data: CustomerCreate) -> Customer:
        """Create a new customer from validated input data."""
        customer = Customer.model_validate(data)
        return await self._repo.create(customer)

    async def get_by_id(self, id: int) -> Optional[Customer]:
        """Return a customer by primary key, or None."""
        return await self._repo.get_by_id(id)

    async def search(
        self, query: str, limit: int = 20
    ) -> Sequence[Customer]:
        """Search customers by identification, name, company, or email."""
        return await self._repo.search(query, limit)

    async def update(self, id: int, data: CustomerUpdate) -> Customer:
        """Update a customer. Raises ValueError if not found."""
        customer = await self._repo.get_by_id(id)
        if customer is None:
            raise ValueError(f"Customer with id {id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        return await self._repo.update(customer)

    async def delete(self, id: int) -> None:
        """Delete a customer. Raises ValueError if not found."""
        customer = await self._repo.get_by_id(id)
        if customer is None:
            raise ValueError(f"Customer with id {id} not found")
        await self._repo.delete(customer)
