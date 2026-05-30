"""
Allocation repository implementations.

This module provides persistence access methods for user beneficial
ownership allocations within pooled investment positions.

Design principles:
    - Persistence - only responsibilities.
    - Transaction - safe row locking for mutable ownership state.
    - Async SQLAlchemy access patters.
"""
from decimal import Decimal

from app.db.models.allocation import PositionAllocation
from app.db.enums             import AllocationStatus
from sqlalchemy.ext.asyncio   import AsyncSession
from sqlalchemy               import select, func
from uuid                     import UUID

class AllocationRepository:
    """
    Repository for user allocation persistence operations.

    This repository encapsulates persistence access for mutable user
    ownership allocations used in buy, sell, and liquidation workflows
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initializes the repository.

        Args:
             db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self, allocation: PositionAllocation) -> PositionAllocation:
        """
        Persist a single allocation.

        Args:
            allocation:
                Allocation entity to persist.

        Returns:
            PositionAllocation:
                Persisted allocation entity.
        """

        self.db.add(allocation)
        await self.db.flush()

        return allocation

    async def create_many(self, allocations: list[PositionAllocation]) -> list[PositionAllocation]:
        """
        Persist multiple allocations.

        Args:
            allocations:
                Allocation entities to persist.

        Returns:
            list[PositionAllocation]:
                Persisted allocation entities.
        """

        self.db.add_all(allocations)
        await self.db.flush()

        return allocations

    async def get_by_id(self, allocation_id: UUID) -> PositionAllocation:
        """
        Retrieve an allocation by identifier.

        Args:
            allocation_id:
                Target allocation identifier.

        Returns:
            PositionAllocation | None:
                Matching allocation if found.
        """
        stmt = select(PositionAllocation).where(PositionAllocation.id == allocation_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_position_id(self, position_id: UUID) -> list[PositionAllocation]:
        """
        Retrieve all allocations for a master position.

        Args:
            position_id:
                Target master position idenitifier.

        Returns:
            list[PositionAllocations]:
                Matching allocations.
        """

        stmt = select(PositionAllocation).where(PositionAllocation.position_id == position_id)

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_open_by_position_id(self, position_id: UUID) -> list[PositionAllocation]:
        """
        Retrieve all open allocations for a master position.

        Args:
            position_id:
                Target master position identifier.

        Returns:
            list[PositionAllocation]:
                Open allocations.
        """
        stmt = select(PositionAllocation).where(
            PositionAllocation.position_id == position_id,
            PositionAllocation.status == AllocationStatus.OPEN,
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_open_by_position_id_for_update(self,position_id: UUID) -> list[PositionAllocation]:
        """
        Retrieve and lock all open allocations for a master position.

        This method acquires row-level locks to prevent concurrent
        ownership mutation during sell or liquidation workflows.

        Args:
            position_id:
                Target master position identifier.

        Returns:
            list[PositionAllocation]:
                Locked open allocations.
        """
        stmt = select(PositionAllocation).where(PositionAllocation.position_id == position_id, PositionAllocation.status == AllocationStatus.OPEN).with_for_update()

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def update(self, allocation: PositionAllocation) -> PositionAllocation:
        """
        Flush updates for a mutated allocation.

        Args:
            allocation:
                Mutated allocation entity.

        Returns:
            PositionAllocation:
                Updated allocation entity.
        """
        await self.db.flush()

        return allocation

    async def get_open_by_position_and_user_for_update(self, position_id: UUID, user_id: UUID) -> list[PositionAllocation]:
        """
        Retrieve and lock open allocations for a specific user within
        a master position.

        This method is used for targeted liquidation workflows.

        Args:
            position_id:
                Target master position identifier.

            user_id:
                Target investor identifier.

        Returns:
            list[PositionAllocation]:
                Locked matching allocations.
        """
        stmt = select(PositionAllocation).where(
            PositionAllocation.position_id == position_id,
            PositionAllocation.user_id     == user_id,
            PositionAllocation.status      == AllocationStatus.OPEN
        ).with_for_update()

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_active_position_counts(self, user_ids: list[UUID]) -> dict[UUID, int]:
        """
        Get the counts of active position(s) (holdings) for the users
        Args:
            user_ids:
                list of user ids

        Returns:
             dict[UUID, int]:
                User ids mapped to the corresponding number of active positions.
        """

        if not user_ids:
            return {}

        stmt = select(
            PositionAllocation.user_id,
            func.count(PositionAllocation.id).label(
                "holding_count"
            )
        ).where(
            PositionAllocation.user_id.in_(user_ids),
            PositionAllocation.status == AllocationStatus.OPEN
        ).group_by(
            PositionAllocation.user_id
        )

        result = await self.db.execute(stmt)

        return {
            row.user_id: int(row.holding_count)
            for row in result.all()
        }

    async def get_active_position_count(self, user_id: UUID) -> int:
        """
        Get the counts of active position(s) (holdings) for a user
        Args:
            user_id:
                list of user ids

        Returns:
             int:
                Number of active holdings for the user
        """

        if not user_id:
            return 0

        stmt = select(
                func.count(
                    PositionAllocation.id
                )
            ).where(
                PositionAllocation.user_id == user_id,
                PositionAllocation.status == AllocationStatus.OPEN,
            )

        result = await self.db.execute(stmt)

        return int(result.scalar_one())

    async def get_open_by_user_id(self, user_id: UUID) -> list[PositionAllocation]:
        """
        Retrieve all open allocations for an investor.

        Args:
            user_id:
                Target investor identifier.

        Returns:
            list[PositionAllocation]:
                Open allocations.
        """

        stmt = select(PositionAllocation).where(
            PositionAllocation.user_id == user_id,
            PositionAllocation.status == AllocationStatus.OPEN,
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_total_invested_amount(
            self,
            user_id: UUID,
    ) -> Decimal:
        """
        Retrieve total invested capital for an investor.

        Invested capital is calculated as the sum of the
        remaining cost basis of all open allocations.

        Args:
            user_id:
                Target investor identifier.

        Returns:
            Decimal:
                Total invested capital.
        """

        stmt = select(
            func.coalesce(
                func.sum(
                    PositionAllocation.remaining_cost
                ),
                0,
            )
        ).where(
            PositionAllocation.user_id == user_id,
            PositionAllocation.status == AllocationStatus.OPEN,
        )

        result = await self.db.execute(stmt)

        return result.scalar_one()