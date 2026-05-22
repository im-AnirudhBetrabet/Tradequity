"""
Market pricing repository implementations.

This module provides persistence access methods for cached market pricing
records used in portfolio valuation workflows.

Design principles:
    - Persistence-only responsibilities
    - Async SQLAlchemy access patterns
    - Efficient cached pricing retrieval
"""

from sqlalchemy.ext.asyncio     import AsyncSession
from app.db.models.market_price import LatestMarketPrice
from datetime                   import datetime
from sqlalchemy                 import delete
from sqlalchemy                 import select


class MarketRepository:
    """
    Repository for cached market pricing persistence operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository.

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def get_by_symbol(self,symbol: str) -> LatestMarketPrice | None:
        """
        Retrieve the latest cached market price for a symbol.

        Args:
            symbol:
                Target exchange symbol.

        Returns:
            LatestMarketPrice | None:
                Cached price record if found.
        """
        stmt = select(LatestMarketPrice).where(
            LatestMarketPrice.symbol == symbol
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_symbols(self,symbols: list[str]) -> list[LatestMarketPrice]:
        """
        Retrieve cached market prices for multiple symbols.

        Args:
            symbols:
                Target exchange symbols.

        Returns:
            list[LatestMarketPrice]:
                Matching cached price records.
        """
        stmt = select(LatestMarketPrice).where(
            LatestMarketPrice.symbol.in_(symbols)
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create_or_update(self,market_price: LatestMarketPrice) -> LatestMarketPrice:
        """
        Persist or update a cached market price record.

        Args:
            market_price:
                Cached market price entity.

        Returns:
            LatestMarketPrice:
                Persisted pricing record.
        """
        await self.db.merge(market_price)
        await self.db.flush()

        return market_price

    async def delete_stale(self,older_than: datetime) -> int:
        """
        Delete stale cached pricing records.

        Args:
            older_than:
                Threshold timestamp.

        Returns:
            int:
                Number of deleted records.
        """
        stmt = delete(LatestMarketPrice).where(
            LatestMarketPrice.updated_at < older_than
        )

        result = await self.db.execute(stmt)

        return result.rowcount or 0
