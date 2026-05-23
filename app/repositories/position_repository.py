"""
Position repository implementations.

This module provides persistence access methods for pooled master
investment positions.

Design principles:
    - Persistence - only responsibilities.
    - Transaction - safe row locking for mutable financial state.
    - Async SQLAlchemy access patterns.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from uuid                   import UUID
from sqlalchemy             import select
from app.db.models          import MasterPosition

class PositionRepository:
    """
    Repository for pooled master position persistence operations.

    This repository encapsulates persistence access for mutable pooled
    investment positions used in buy and sell workflows.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initializes the repository.

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db


    async def create(self, position: MasterPosition) -> MasterPosition:
        """
        Persist a new master position.

        Args:
            position:
                Master position entity to persist.
        Returns:
            MasterPosition:
                Persisted master position entity
        """
        self.db.add(position)
        await self.db.flush()
        return position
    
    async def get_by_id(self, position_id: UUID) -> MasterPosition | None:
        """
        Retrieve a master position by identifier.

        Args:
            position_id:
                Target master position identifier.

        Returns:
            MasterPosition | None:
                Matching position if found.
        """

        stmt = select(MasterPosition).where(MasterPosition.id == position_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async  def get_by_id_for_update(self, position_id: UUID) -> MasterPosition | None:
        """
        Retrieve and lock a master position for transactional mutation.

        This method acquires a row-level database lock to prevent
        concurrent modifications during sensitive financial workflows.

        Args:
             position_id:
                Target master position identifier.

        Returns:
            MasterPosition | None:
                Locked position if found.
        """

        stmt = select(MasterPosition).where(MasterPosition.id == position_id).with_for_update()

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def update(self, position: MasterPosition) -> MasterPosition:
        """
        Flush updates for an existing master position

        Args:
            position:
                Mutated position entity.

        Return:
            MasterPosition:
            Updated position entity.
        """

        await self.db.flush()

        return position