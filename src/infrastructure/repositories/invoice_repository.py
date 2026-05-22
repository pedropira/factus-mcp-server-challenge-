"""
Repository for Invoice and related entities (InvoiceItem, AllowanceCharge).
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.repositories.base import BaseRepository
from src.schemas.models import (
    AllowanceCharge,
    Invoice,
    InvoiceItem,
    WithholdingTax,
)


class InvoiceRepository(BaseRepository[Invoice]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Invoice)

    async def get_by_reference_code(
        self, reference_code: str
    ) -> Optional[Invoice]:
        """Busca una factura por su código de referencia único."""
        stmt = select(Invoice).where(
            Invoice.reference_code == reference_code
        )
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_by_number(self, number: str) -> Optional[Invoice]:
        """Busca una factura por su número asignado (prefijo + consecutivo)."""
        stmt = select(Invoice).where(Invoice.number == number)
        result = await self._session.exec(stmt)
        return result.one_or_none()

    async def get_by_status(
        self, status: int, limit: int = 50
    ) -> Sequence[Invoice]:
        """Obtiene facturas por estado."""
        stmt = (
            select(Invoice)
            .where(Invoice.status == status)
            .limit(limit)
        )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_pending_sync(self, limit: int = 50) -> Sequence[Invoice]:
        """Obtiene facturas pendientes de sincronizar (sin CUFE)."""
        stmt = (
            select(Invoice)
            .where(Invoice.cufe.is_(None))
            .limit(limit)
        )
        result = await self._session.exec(stmt)
        return result.all()


class InvoiceItemRepository(BaseRepository[InvoiceItem]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InvoiceItem)

    async def get_by_invoice_id(self, invoice_id: int) -> Sequence[InvoiceItem]:
        """Obtiene todos los ítems de una factura."""
        stmt = (
            select(InvoiceItem)
            .where(InvoiceItem.invoice_id == invoice_id)
        )
        result = await self._session.exec(stmt)
        return result.all()


class WithholdingTaxRepository(BaseRepository[WithholdingTax]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WithholdingTax)

    async def get_by_invoice_item_id(
        self, invoice_item_id: int
    ) -> Sequence[WithholdingTax]:
        """Obtiene todas las retenciones de un ítem."""
        stmt = (
            select(WithholdingTax)
            .where(WithholdingTax.invoice_item_id == invoice_item_id)
        )
        result = await self._session.exec(stmt)
        return result.all()


class AllowanceChargeRepository(BaseRepository[AllowanceCharge]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AllowanceCharge)

    async def get_by_invoice_id(
        self, invoice_id: int
    ) -> Sequence[AllowanceCharge]:
        """Obtiene todos los descuentos/recargos de una factura."""
        stmt = (
            select(AllowanceCharge)
            .where(AllowanceCharge.invoice_id == invoice_id)
        )
        result = await self._session.exec(stmt)
        return result.all()
