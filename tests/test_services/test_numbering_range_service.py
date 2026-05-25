"""
Tests for NumberingRangeService.

Focus on the next_available() logic which is the most complex behavior:
computing the next invoice number from the max used in the invoices table.
"""

from __future__ import annotations

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.schemas.dto import NumberingRangeCreate
from src.schemas.models import NumberingRange
from src.services.numbering_range_service import NumberingRangeService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)

    # By default, make exec() return a MagicMock whose .one() returns None
    mock_result = MagicMock()
    mock_result.one.return_value = None
    session.exec.return_value = mock_result

    return session


@pytest.fixture
def service(mock_session: AsyncMock) -> NumberingRangeService:
    return NumberingRangeService(mock_session)


@pytest.fixture
def active_range() -> NumberingRange:
    return NumberingRange(
        id=1,
        document_type_id="21",
        prefix="FAC",
        from_number=1,
        to_number=5000,
        resolution_number="1876000000001",
        start_date="01-01-2025",
        end_date="31-12-2025",
        months=12,
        is_active=True,
    )


# ─── NEXT AVAILABLE ──────────────────────────────────────────────────────────


class TestNumberingRangeServiceNextAvailable:
    async def test_first_invoice_returns_from_number(
        self,
        service: NumberingRangeService,
        mock_session: AsyncMock,
        active_range: NumberingRange,
    ) -> None:
        """No invoices exist → returns range.from_number."""
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=active_range)
            # sim.exec() returns Mock where .one() = None (set in fixture)

            result = await service.next_available(1)  # range_id=1 (int, not doc type)

            assert result == 1

    async def test_next_after_existing_invoices(
        self,
        service: NumberingRangeService,
        mock_session: AsyncMock,
        active_range: NumberingRange,
    ) -> None:
        """Invoices at 1, 2, 3 → returns 4."""
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=active_range)
            mock_session.exec.return_value.one.return_value = 3

            result = await service.next_available(1)

            assert result == 4

    async def test_range_exhausted_raises_error(
        self,
        service: NumberingRangeService,
        mock_session: AsyncMock,
    ) -> None:
        """from=1, to=3, max used=3 → ValueError."""
        exhausted = NumberingRange(
            id=1, document_type_id="21", prefix="FAC",
            from_number=1, to_number=3,
            resolution_number="1876000000001",
            start_date="01-01-2025",
            end_date="31-12-2025",
            months=12,
            is_active=True,
        )
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=exhausted)
            mock_session.exec.return_value.one.return_value = 3

            with pytest.raises(ValueError, match="Numbering range exhausted"):
                await service.next_available(1)

    async def test_range_not_found_raises_error(
        self, service: NumberingRangeService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Numbering range with id 999 not found"):
                await service.next_available(999)


# ─── GET ACTIVE ──────────────────────────────────────────────────────────────


class TestNumberingRangeServiceGetActive:
    async def test_returns_active_ranges(
        self,
        service: NumberingRangeService,
        active_range: NumberingRange,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_active = AsyncMock(return_value=[active_range])
            results = await service.get_active()

            assert len(results) == 1
            assert results[0].prefix == "FAC"
            mock_repo.get_active.assert_awaited_once_with(None)

    async def test_filters_by_document_type(
        self,
        service: NumberingRangeService,
        active_range: NumberingRange,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_active = AsyncMock(return_value=[active_range])
            results = await service.get_active(document_type_id="21")

            assert len(results) == 1
            mock_repo.get_active.assert_awaited_once_with("21")


# ─── GET DEFAULT ─────────────────────────────────────────────────────────────


class TestNumberingRangeServiceGetDefault:
    async def test_returns_default_range(
        self,
        service: NumberingRangeService,
        active_range: NumberingRange,
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_default_for_document_type = AsyncMock(return_value=active_range)
            result = await service.get_default_for_document_type("21")

            assert result is not None
            assert result.id == 1
            mock_repo.get_default_for_document_type.assert_awaited_once_with("21")

    async def test_returns_none_when_no_default(
        self, service: NumberingRangeService
    ) -> None:
        with patch.object(service, "_repo", spec=True) as mock_repo:
            mock_repo.get_default_for_document_type = AsyncMock(return_value=None)
            result = await service.get_default_for_document_type("99")

            assert result is None
