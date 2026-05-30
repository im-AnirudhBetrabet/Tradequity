"""
Ledger repository implementations.

This module provides persistence across methods for immutable financial
ledger transactions and derived account balance calculations.

Design principles:
    - Immutable financial transaction persistence.
    - Deterministic balance derivation.
    - Persistence-only responsibilities.
    - Async SQLAlchemy access patters.
"""

from decimal                import Decimal
from uuid                   import UUID
from sqlalchemy             import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import TransactionReferenceType
from app.db.models.ledger   import LedgerTransaction

class LedgerRepository:
    """
    Repository for ledger transaction persistence operations.

    This repository encapsulates immutable financial transaction writes
    and derived balance calculations for financial accounts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialises the repository.

        Args:
             db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self, transaction: LedgerTransaction) -> LedgerTransaction:
        """
        Persist a single ledger transaction.

        Args:
            transaction:
                Ledger transaction entity to persist.

        Returns:
            LedgerTransaction:
            Persisted ledger transaction entity.
        """

        self.db.add(transaction)
        await self.db.flush()

        return transaction

    async def create_many(self, transactions: list[LedgerTransaction]) -> list[LedgerTransaction]:
        """
        Persist multiple ledger transactions.

        Args:
            transactions:
                Ledger transaction entities to persist.

        Returns:
            list[LedgerTransaction]:
                Persisted ledger transactions.
        """

        self.db.add_all(transactions)
        await self.db.flush()

        return transactions

    async def get_account_balance(self, account_id: UUID) -> Decimal:
        """
        Calculate the derived balance for an account.

        Balance is computed as:
            inbound credits - outbound debits

        Args:
            account_id
                Target account identifier.

        Returns:
            Decimal:
                Derived account balance.
        """

        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                            (
                                LedgerTransaction.to_account_id == account_id,
                                LedgerTransaction.amount
                            ),
                            (
                                LedgerTransaction.from_account_id == account_id,
                                -LedgerTransaction.amount,
                            ),
                            else_=Decimal("0"),
                        )
                ),
                    Decimal("0"),
            )
        )

        result = await self.db.execute(stmt)

        balance = result.scalar_one()

        return Decimal(balance)

    async def get_account_transactions(self, account_id: UUID) -> list[LedgerTransaction]:
        """
        Retrieve all transactions involving a specific amount.
        Args;
            account_id:
                Target account identifier.

            Returns:
                list[LedgerTransaction]:
                    Matching ledger transactions ordered newest first
        """
        stmt = select(LedgerTransaction).where(
            (LedgerTransaction.from_account_id == account_id) | (LedgerTransaction.to_account_id == account_id)
        ).order_by(LedgerTransaction.created_at)

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_total_deposits(self, account_id: UUID) -> Decimal:
        """
        Retrieve total deposits credited into an account.
        Args:
            account_id:
                Target account identifier.

        Returns:
            Decimal:
                Total deposited amount.
        """

        stmt = select(
            func.coalesce(
                func.sum(
                    LedgerTransaction.amount
                ),
                Decimal("0")
            )
        ).where(
            LedgerTransaction.to_account_id == account_id,
            LedgerTransaction.reference_type == TransactionReferenceType.DEPOSIT
        )

        result = await self.db.execute(stmt)

        return Decimal(result.scalar_one())

    async def get_recent_transactions(self, account_id: UUID, limit: int = 10) -> list[LedgerTransaction]:
        """
        Retrieve recent account transactions.

        Args:
            account_id:
                Target account identifier.

            limit:
                Maximum records to return.

        Returns:
            list[LedgerTransaction]:
                Recent transactions ordered newest first.
        """

        stmt = (
            select(LedgerTransaction)
            .where(
                (LedgerTransaction.from_account_id == account_id)
                |
                (LedgerTransaction.to_account_id == account_id)
            )
            .order_by(
                LedgerTransaction.created_at.desc()
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return list(
            result.scalars().all()
        )