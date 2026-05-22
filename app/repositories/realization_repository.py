"""
Realization repository implementations.

This module provides persistence access methods for immutable allocation
realization financial records.

Design principles:
    - Immutable financial event persistence
    - Persistence-only responsibilities
    - Async SQLAlchemy access patterns
"""
from sqlalchemy.ext.asyncio    import AsyncSession
from app.db.models.allocation  import PositionAllocation
from app.db.models.realization import AllocationRealization
from uuid                      import UUID
from sqlalchemy                import select

class RealizationRepository:
    """
    Repository for allocation realization persistence operations.

    This repository encapsulates immutable realization financial event
    writes and retrieval operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository.

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self, realization: AllocationRealization) -> AllocationRealization:
        """
        Persist a realization record.

        Args:
            realization:
                Realization entity to persist.

        Returns:
            AllocationRealization:
                Persisted realization entity.
        """
        self.db.add(realization)
        await self.db.flush()

        return realization

    async def create_many(self, realizations: list[AllocationRealization]) -> list[AllocationRealization]:
        """
        Persist multiple realization records.

        Args:
            realizations:
                Realization entities to persist.

        Returns:
            list[AllocationRealization]:
                Persisted realization entities.
        """
        self.db.add_all(realizations)
        await self.db.flush()

        return realizations

    async def get_by_trade_id(self,trade_execution_id: UUID) -> list[AllocationRealization]:
        """
        Retrieve realizations for a specific sell trade.

        Args:
            trade_execution_id:
                Target sell trade identifier.

        Returns:
            list[AllocationRealization]:
                Matching realization records.
        """
        stmt = select(AllocationRealization).where(
            AllocationRealization.trade_execution_id == trade_execution_id
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_by_allocation_id(self, allocation_id: UUID) -> list[AllocationRealization]:
        """
        Retrieve realization history for an allocation.

        Args:
            allocation_id:
                Target allocation identifier.

        Returns:
            list[AllocationRealization]:
                Matching realization records ordered oldest first.
        """
        stmt = (
            select(AllocationRealization)
            .where(
                AllocationRealization.allocation_id == allocation_id
            )
            .order_by(AllocationRealization.realized_at.asc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_user_realizations(self, user_id: UUID) -> list[AllocationRealization]:
        """
        Retrieve realization history for a user.

        Args:
            user_id:
                Target user profile identifier.

        Returns:
            list[AllocationRealization]:
                User realization history ordered newest first.
        """
        stmt = (
            select(AllocationRealization)
            .join(
                PositionAllocation,
                PositionAllocation.id == AllocationRealization.allocation_id,
            )
            .where(PositionAllocation.user_id == user_id)
            .order_by(AllocationRealization.realized_at.desc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())
