"""
NumberingRangeService — DIAN numbering ranges.

Dos fuentes de datos:
  - Local DB (CRUD): gestión interna de rangos registrados.
  - Factus API (GET /v2/numbering-ranges): rangos reales desde Factus.

La columna factus_id enlaza los rangos locales con los IDs de la API de Factus.
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

    # ── Local → Factus ID resolution ─────────────────────────────────────

    async def get_factus_id(self, local_id: int) -> int:
        """Resuelve un ID local de rango de numeración al ID de Factus API.

        Args:
            local_id: ID del rango en la base de datos local.

        Returns:
            ID del rango en la API de Factus.

        Raises:
            ValueError: Si no se encuentra el rango o no tiene factus_id.
        """
        range_ = await self._repo.get_by_id(local_id)
        if range_ is None:
            raise ValueError(
                f"Numbering range with local id {local_id} not found"
            )
        if range_.factus_id is None:
            raise ValueError(
                f"Numbering range {local_id} ('{range_.prefix}') has no "
                f"factus_id. Sync ranges first via fetch_numbering_ranges_from_factus."
            )
        return range_.factus_id

    # ── Factus API — GET /v2/numbering-ranges ────────────────────────────

    async def fetch_from_factus(
        self, is_active: bool = True
    ) -> list[dict]:
        """Obtiene rangos de numeración desde Factus API y los sincroniza con la DB local.

        Para cada rango devuelto por Factus:
          1. Busca si ya existe un rango local con el mismo `factus_id`.
             Si no existe, busca por `prefix` + `document_type_id`.
          2. Si existe: actualiza sus campos (from_number, to_number, etc.)
             y asegura que `factus_id` esté correcto.
          3. Si no existe: crea un nuevo registro con `factus_id`.

        Args:
            is_active: Si es True, filtra solo rangos activos.

        Returns:
            Lista de rangos en el formato de la API de Factus (respuesta cruda).
        """
        if self._factus is None:
            raise RuntimeError("FactusClient required for API calls")
        if self._repo is None:
            raise RuntimeError("Repository (session) required for DB sync")

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
        ranges: list[dict] = data.get("data", {}).get("data", [])

        for r in ranges:
            factus_id = r.get("id")
            prefix = r.get("prefix") or ""
            doc_type_id = str(r.get("type_document_id") or "")

            # Buscar por factus_id primero
            existing = await self._repo.get_by_factus_id(factus_id)

            # Si no, buscar por prefix + doc_type
            if existing is None:
                existing = await self._repo.get_by_prefix_and_doc_type(
                    prefix, doc_type_id
                )

            if existing is not None:
                # Actualizar registro existente
                existing.factus_id = factus_id
                existing.prefix = prefix
                existing.from_number = int(r.get("from") or 0)
                existing.to_number = int(r.get("to") or 0)
                existing.resolution_number = r.get("resolution_number") or ""
                existing.start_date = r.get("start_date") or ""
                existing.end_date = r.get("end_date") or ""
                existing.months = int(r.get("months") or 0)
                existing.document_type_id = doc_type_id
                existing.is_active = bool(r.get("is_active") or False)
                await self._repo.update(existing)
            else:
                # Crear nuevo registro
                new_range = NumberingRange(
                    factus_id=factus_id,
                    prefix=prefix,
                    from_number=int(r.get("from") or 0),
                    to_number=int(r.get("to") or 0),
                    resolution_number=r.get("resolution_number") or "",
                    start_date=r.get("start_date") or "",
                    end_date=r.get("end_date") or "",
                    months=int(r.get("months") or 0),
                    document_type_id=doc_type_id,
                    is_active=bool(r.get("is_active") or False),
                )
                await self._repo.create(new_range)

        return ranges


__all__ = ["NumberingRangeService"]
