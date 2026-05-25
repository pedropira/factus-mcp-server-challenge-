"""
NumberingRangeService — DIAN numbering ranges.

Dos fuentes de datos:
  - Local DB (CRUD): gestión interna de rangos registrados.
  - Factus API (GET /v2/numbering-ranges): rangos reales desde Factus.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.factus_client import FactusClient
from src.infrastructure.repositories import NumberingRangeRepository
from src.schemas.dto import NumberingRangeCreate, NumberingRangeUpdate
from src.schemas.models import Invoice, NumberingRange


class NumberingRangeService:
    """Business logic for DIAN numbering ranges and number assignment."""

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        factus: Optional[FactusClient] = None,
    ) -> None:
        self._session = session
        self._factus = factus
        self._repo = NumberingRangeRepository(session) if session else None

    # ── Local DB CRUD ────────────────────────────────────────────────────

    async def create(self, data: NumberingRangeCreate) -> NumberingRange:
        """Register a new DIAN authorized numbering range in local DB."""
        numbering_range = NumberingRange.model_validate(data)
        return await self._repo.create(numbering_range)

    async def get_active(
        self, document_type_id: Optional[str] = None
    ) -> Sequence[NumberingRange]:
        """Return active ranges from local DB."""
        return await self._repo.get_active(document_type_id)

    async def update(
        self, id: int, data: NumberingRangeUpdate
    ) -> NumberingRange:
        """Update a numbering range in local DB."""
        number_range = await self._repo.get_by_id(id)
        if number_range is None:
            raise ValueError(f"Numbering range with id {id} not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(number_range, field, value)
        return await self._repo.update(number_range)

    async def delete(self, id: int) -> None:
        """Delete a numbering range from local DB."""
        number_range = await self._repo.get_by_id(id)
        if number_range is None:
            raise ValueError(f"Numbering range with id {id} not found")
        await self._repo.delete(number_range)

    # ── Local DB — queries ───────────────────────────────────────────────

    async def get_default_for_document_type(
        self, document_type_id: str
    ) -> Optional[NumberingRange]:
        """Return the first active range for a document type from local DB."""
        return await self._repo.get_default_for_document_type(document_type_id)

    # ── Local DB — number assignment ─────────────────────────────────────

    async def next_available(self, range_id: int) -> int:
        """Compute the next available invoice number for a range.

        Lee el from_number/to_number del rango y consulta la tabla invoices
        para el número más alto usado dentro de este rango.
        """
        range_ = await self._repo.get_by_id(range_id)
        if range_ is None:
            raise ValueError(f"Numbering range with id {range_id} not found")

        stmt = select(func.max(Invoice.number)).where(
            Invoice.numbering_range_id == range_id
        )
        result = await self._session.exec(stmt)
        max_used = result.one()

        if max_used is None:
            return range_.from_number

        next_num = max_used + 1
        if next_num > range_.to_number:
            raise ValueError(
                f"Numbering range exhausted (max {range_.to_number})"
            )
        return next_num

    # ── Factus API — GET /v2/numbering-ranges ────────────────────────────

    async def fetch_from_factus(
        self, is_active: bool = True
    ) -> list[dict]:
        """Obtiene rangos de numeración directamente desde la API de Factus.

        Args:
            is_active: Si es True, filtra solo rangos activos.

        Returns:
            Lista de rangos en el formato de la API de Factus.
        """
        if self._factus is None:
            raise RuntimeError("FactusClient required for API calls")

        params: dict[str, Any] = {}
        if is_active:
            params["filter[is_active]"] = 1

        response = await self._factus.get(
            "/v2/numbering-ranges", params=params
        )
        await response.aread()

        if not response.is_success:
            raise RuntimeError(
                f"Factus API error ({response.status_code}): {response.text}"
            )

        data = response.json()
        return data.get("data", {}).get("data", [])
