"""
Account repository implementations.

This module provides persistence access methods for financial account
entities used by the Tradequity doubly-entry ledger system.

Design principles:
    - Persistence-only responsibilities.
    - No business rule enforcement.
    - Explicit typed query methods.
    - Async SQLAlchemy access patterns.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy             import select
from app.db.enums           import AccountType
from app.db.models.account  import Account

class AccountRepository:
    """
    Repository for financial account persistence operations.

    This repository encapsulates account retrieval and persistence accss
    for user and platform financial accounts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initializes the repository.
        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """
        Retrieve an account by identifier.

        Args:
            account_id:
                Target account identifier.

        Returns:
            Account | None:
                Matching account if found, otherwise None.
        """
        stmt = select(Account).where(Account.id == account_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
    
    async def get_user_cash_account(self, user_id: UUID) -> Account | None:
        """
        Retrieve a user's liquid cash account.
        Args:
            user_id:
                User profile Identifier.
        Returns:
             Account | None:
                Matching user cash account if found.
        """
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.account_type == AccountType.USER_CASH,
            Account.is_active.is_(True)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_platform_treasury_account(self) -> Account | None:
        """
        Retrieves the platform treasury account.

        Returns:
            Account | None:
                Platform treasury account if configured.
        """

        stmt = select(Account).where(
            Account.account_type == AccountType.PLATFORM_TREASURY,
            Account.is_active.is_(True)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_platform_revenue_account(self) -> Account | None:
        """
        Retrieve the platform revenue account.

        Returns:
             Account | None:
                Platform revenue account if configured.
        """

        stmt = select(Account).where(
            Account.account_type == AccountType.PLATFORM_REVENUE,
            Account.is_active.is_(True)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create(self, account: Account) -> Account:
        """
        Persist a new financial account.

        Args:
            account:
                Account entity to persist.
        
        Returns:
            Account:
                Persisted account entity.
        """

        self.db.add(account)
        await self.db.flush()

        return account

    async def get_user_cash_account_for_update(self, user_id: UUID) -> Account | None:
        """
        Retrieve and lock a user's liquid cash account.

        This method acquires a row-level database lock to prevent concurrent
        workflows from overspending the same user funds.

        Args:
            user_id:
                User profile identifier.

        Returns:
            Account | None:
                Locker user cash account if found.
        """
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.account_type == AccountType.USER_CASH,
            Account.is_active.is_(True)
        ).with_for_update()

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_user_settlement_account(self, user_id: UUID) -> Account | None:
        """
        Retrieve a user's settlement account.

        Args:
            user_id:
                Target user identifier.

        Returns:
            Account | None:
                Matching settlement account if found.
        """
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.account_type == AccountType.USER_SETTLEMENT,
            Account.is_active.is_(True)
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()


    async def get_platform_fee_reserve_account(self) -> Account | None:
        """
        Retrieve the platform performance fee reserve account.

        Returns:
             Account | None:
                Matching active fee reserve account.
        """

        stmt = select(Account).where(
            Account.account_type == AccountType.PLATFORM_FEE,
            Account.is_active.is_(True)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()