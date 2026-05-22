"""
Withdrawal repository implementations.

This module provides persistence access methods for withdrawal workflow
records.

Design principles:
    - Persistence-only responsibilities
    - Transaction-safe workflow mutation support
    - Async SQLAlchemy access patterns
"""

from sqlalchemy.ext.asyncio   import AsyncSession
from app.db.enums             import WithdrawalStatus
from app.db.models.withdrawal import WithdrawalRequest
from sqlalchemy               import select
from uuid                     import UUID



class WithdrawalRepository:
    """
    Repository for withdrawal workflow persistence operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository.

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self,withdrawal: WithdrawalRequest) -> WithdrawalRequest:
        """
        Persist a withdrawal request.

        Args:
            withdrawal:
                Withdrawal entity to persist.

        Returns:
            WithdrawalRequest:
                Persisted withdrawal entity.
        """
        self.db.add(withdrawal)
        await self.db.flush()

        return withdrawal

    async def get_by_id(self,withdrawal_id: UUID) -> WithdrawalRequest | None:
        """
        Retrieve a withdrawal request by identifier.

        Args:
            withdrawal_id:
                Target withdrawal identifier.

        Returns:
            WithdrawalRequest | None:
                Matching withdrawal if found.
        """
        stmt = select(WithdrawalRequest).where(
            WithdrawalRequest.id == withdrawal_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id_for_update( self, withdrawal_id: UUID) -> WithdrawalRequest | None:
        """
        Retrieve and lock a withdrawal request for workflow mutation.

        Args:
            withdrawal_id:
                Target withdrawal identifier.

        Returns:
            WithdrawalRequest | None:
                Locked withdrawal entity if found.
        """
        stmt = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .with_for_update()
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> list[WithdrawalRequest]:
        """
        Retrieve withdrawal history for a user.

        Args:
            user_id:
                Target user identifier.

        Returns:
            list[WithdrawalRequest]:
                Matching withdrawal requests ordered newest first.
        """
        stmt = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.user_id == user_id)
            .order_by(WithdrawalRequest.requested_at.desc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_pending_requests(self) -> list[WithdrawalRequest]:
        """
        Retrieve all pending withdrawal requests.

        Returns:
            list[WithdrawalRequest]:
                Pending withdrawal requests.
        """
        stmt = select(WithdrawalRequest).where(
            WithdrawalRequest.status == WithdrawalStatus.PENDING
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def update(self,withdrawal: WithdrawalRequest) -> WithdrawalRequest:
        """
        Flush updates for a mutated withdrawal workflow entity.

        Args:
            withdrawal:
                Mutated withdrawal entity.

        Returns:
            WithdrawalRequest:
                Updated withdrawal entity.
        """
        await self.db.flush()

        return withdrawal