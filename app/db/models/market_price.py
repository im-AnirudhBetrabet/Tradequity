"""
Market pricing ORM model definitions.

This module defines cached market pricing records used for portfolio
valuation and mark-to-market reporting.

These records represent transient pricing snapshots rather than immutable
financial events.
"""

from datetime       import datetime
from decimal        import Decimal
from sqlalchemy     import DateTime
from sqlalchemy     import Numeric
from sqlalchemy     import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from app.db.base    import Base


class LatestMarketPrice(Base):
    """
    Cached latest market price record.

    Represents the most recently known price for a tradable instrument.

    Attributes:
        symbol:
            Exchange trading symbol.

        price:
            Latest known market price.

        source:
            Market data provider identifier.

        as_of:
            Timestamp representing market quote freshness.

        updated_at:
            Timestamp of cache update.
    """

    __tablename__   = "latest_market_prices"
    __mapper_args__ = {"eager_defaults": True}

    symbol    : Mapped[str]      = mapped_column(Text,primary_key=True)
    price     : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    source    : Mapped[str]      = mapped_column(Text,nullable=False)
    as_of     : Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())