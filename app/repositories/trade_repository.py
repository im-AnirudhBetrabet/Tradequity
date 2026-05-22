"""
Trade repository implementations.

This module provides persistence access methods for immutable trade
execution records.

Design principles:
    - Persistence only responsibilities.
    - Immutable trade event access.
    - Async SQLAlchemy access patterns.
    - Transaction-sage query support
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy             import select
from app.db.models.trade    import TradeExecution
from uuid                   import UUID

class TradeRepository:
    """
    Repository for trade execution persistence operations.

    This repository encapsulates immutable trade execution writes and
    retrieval operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self, trade: TradeExecution) -> TradeExecution:
        """
        Persist a trade execution record.

        Args:
            trade:
                Trade execution entity to persist

            Returns:
                TradeExecution:
                    Persisted trade execution entity.
        """

        self.db.add(trade)
        await self.db.flush()

        return trade

    async def get_by_id(self, trade_id: UUID) -> TradeExecution | None:
        """
        Retrieves a trade execution by identifier.

        Args:
            trade_id:
                Target trade execution identifier.

        Returns:
            TradeExecution | None:
                Matching trade execution if found.
        """

        stmt = select(TradeExecution).where(TradeExecution.id == trade_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_position_id(self, position_id: UUID) -> list[TradeExecution]:
        """
        Retrieve trade executions associated with a master position.

        Args:
            position_id:
                Target master position identifier.

        Returns:
            list[TradeExecution]:
                Matching trade executions ordered oldest first.
        """
        stmt = (
            select(TradeExecution)
            .where(TradeExecution.position_id == position_id)
            .order_by(TradeExecution.executed_at.asc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())